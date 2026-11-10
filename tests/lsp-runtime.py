#!/usr/bin/env python3
"""Reproducible Helix runtime validation of the Quazi language configuration.

Helix runs in a pseudo-terminal with this repository's `languages.toml`
(its server command pointed at a logging proxy around `qz lsp`) and an
isolated configuration directory. The test types the keys a user would:
hover (`space k`), go to definition (`g d`) and insert-mode completion, and
checks in the proxy's message log that Helix sent each request for the open
`.qz` document and the server answered it with a result.
"""

import argparse
import fcntl
import json
import os
import pty
import shutil
import struct
import select
import sys
import tempfile
import termios
import time
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent

SOURCE = """fn helper(count: i32) i32 { ret count; }

fn main() i32 {
    const total: i32 = helper(2);
    ret total;
}
"""

PROXY = r'''
import json, subprocess, sys, threading
log = open(sys.argv[1], "a", buffering=1)
server = subprocess.Popen(sys.argv[2:], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def pump(source, sink, direction):
    while True:
        headers = {}
        while True:
            line = source.readline()
            if not line:
                sink.close()
                return
            if line in (b"\r\n", b"\n"):
                break
            name, _, value = line.decode().partition(":")
            headers[name.strip().lower()] = value.strip()
        body = source.read(int(headers["content-length"]))
        log.write(json.dumps({"direction": direction, "message": json.loads(body)}) + "\n")
        sink.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        sink.flush()

threading.Thread(target=pump, args=(server.stdout, sys.stdout.buffer, "server"), daemon=True).start()
pump(sys.stdin.buffer, server.stdin, "client")
server.wait()
'''


def messages(log):
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def answered(log, method):
    """Result of the last answered `method` request, or None."""
    entries = messages(log)
    ids = {entry["message"]["id"] for entry in entries
           if entry["direction"] == "client" and entry["message"].get("method") == method}
    results = [entry["message"].get("result") for entry in entries
               if entry["direction"] == "server" and entry["message"].get("id") in ids
               and "method" not in entry["message"]]
    return results[-1] if results else None


def wait_until(predicate, what, timeout=30.0, log=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    seen = ""
    if log is not None:
        seen = "; messages: " + ", ".join(
            json.dumps(entry["message"])[:300] for entry in messages(log)[-4:])
    raise AssertionError(f"timed out waiting for {what}{seen}")


class Terminal:
    """Helix in a pseudo-terminal; output is drained so it never blocks."""

    def __init__(self, command, env, cwd):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(cwd)
            os.execvpe(command[0], command, env)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))

    def drain(self, seconds=0.2):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                ready, _, _ = select.select([self.fd], [], [], 0.05)
                if ready:
                    os.read(self.fd, 65536)
            except OSError:
                return

    def keys(self, text, pause=0.4):
        os.write(self.fd, text.encode())
        self.drain(pause)

    def close(self):
        try:
            self.keys("\x1b:q!\r", 0.5)
        finally:
            for _ in range(50):
                pid, _ = os.waitpid(self.pid, os.WNOHANG)
                if pid:
                    return
                time.sleep(0.1)
            os.kill(self.pid, 9)
            os.waitpid(self.pid, 0)


def check(hx, qz, root):
    project = root / "project"
    (project / "src").mkdir(parents=True)
    (project / "quazi.toml").write_text('[package]\nname = "helix-runtime"\n\n[build]\nentry = "src/main.qz"\n')
    main = project / "src/main.qz"
    main.write_text(SOURCE)

    log = root / "lsp.jsonl"
    proxy = root / "proxy.py"
    proxy.write_text(PROXY)
    config = root / "config/helix"
    config.mkdir(parents=True)
    languages = (REPOSITORY / "languages.toml").read_text()
    languages = languages.replace('command = "qz"\nargs = ["lsp"]',
                                  f'command = "{sys.executable}"\n'
                                  f'args = ["{proxy}", "{log}", "{qz}", "lsp"]')
    assert str(proxy) in languages, "languages.toml no longer declares the expected server"
    (config / "languages.toml").write_text(languages)
    (config / "config.toml").write_text("[editor]\ncompletion-trigger-len = 1\nidle-timeout = 50\n")

    env = dict(os.environ, HOME=str(root), XDG_CONFIG_HOME=str(root / "config"),
               XDG_CACHE_HOME=str(root / "cache"), XDG_DATA_HOME=str(root / "data"),
               TERM="xterm-256color")
    terminal = Terminal([str(hx), "src/main.qz"], env, project)
    try:
        wait_until(lambda: any(entry["message"].get("method") == "textDocument/publishDiagnostics"
                               for entry in messages(log)), "initial diagnostics")
        opened = [entry["message"]["params"]["textDocument"] for entry in messages(log)
                  if entry["message"].get("method") == "textDocument/didOpen"]
        assert opened and opened[0]["languageId"] == "quazi", opened

        # Hover on `helper` in the call (line 4): search, collapse onto the
        # identifier's last character, then `space k`.
        terminal.keys("/helper\\(2\r")
        terminal.keys(";")
        terminal.keys("bh")
        terminal.keys(" ")
        terminal.keys("k", 1.0)
        hover = wait_until(lambda: answered(log, "textDocument/hover"), "hover result", log=log)
        assert "i32" in json.dumps(hover), hover
        terminal.keys("\x1b")

        # Go to definition of the same call target.
        terminal.keys("gd", 1.0)
        definition = wait_until(lambda: answered(log, "textDocument/definition"),
                                "definition result", log=log)
        assert json.dumps(definition).count('"line": 0') >= 1, definition

        # Completion while typing in a new line of `main`.
        terminal.keys("/ret total\r")
        # A separate write keeps `ESC O` from reading as an SS3 key sequence.
        terminal.keys(";", 0.3)
        terminal.keys("O", 0.3)
        terminal.keys("hel", 1.5)
        completion = wait_until(lambda: answered(log, "textDocument/completion"),
                                "completion result", log=log)
        labels = [item["label"] for item in
                  (completion["items"] if isinstance(completion, dict) else completion)]
        assert "helper" in labels, labels
        terminal.keys("\x1b")
    finally:
        terminal.close()
    print("PASS helix runtime: didOpen(quazi), diagnostics, hover, definition and completion "
          "requests answered through Helix")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hx", default=shutil.which("hx"), help="Helix executable")
    parser.add_argument("--qz", default=shutil.which("qz"), help="Quazi compiler executable")
    args = parser.parse_args()
    if not args.hx or not args.qz:
        parser.error("pass --hx and --qz (or put them on PATH)")
    with tempfile.TemporaryDirectory(prefix="helix-quazi-") as directory:
        check(Path(args.hx).resolve(), Path(args.qz).resolve(), Path(directory))


if __name__ == "__main__":
    main()
