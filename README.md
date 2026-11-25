# Quazi for Helix

This is a Helix language-configuration fragment, not a standalone plugin.
Merge `languages.toml` into either `~/.config/helix/languages.toml` or a
project's `.helix/languages.toml`. Copy `runtime/queries/quazi/` into the
matching Helix runtime query directory.

It registers `.qz` as `source.quazi`, launches `qz lsp`, and pins the Quazi
Tree-sitter grammar to the commit named by `rev` in `languages.toml`
(currently `cb8eee528b00decba801f5e7a6e74a509c57700f`).
After installing the fragment, run:

```bash
hx --grammar fetch
hx --grammar build
```

The grammar deliberately preserves opaque field attributes such as
`name: String @ini("username")`; Helix only highlights their syntax and leaves
their meaning to the library or tool that owns the attribute.

From this workspace, verify the pinned grammar revision and highlight query:

```bash
bash tests/check-canonical-assets.sh
```

Validate the language configuration against a running Helix and `qz lsp`
(Helix 25.07; for example `nix build nixpkgs#helix` provides one). The test
starts Helix in a pseudo-terminal with an isolated configuration built from
this `languages.toml`, routes the server through a logging proxy, types the
keys for hover (`space k`), go to definition (`g d`) and insert-mode
completion, and requires each request to be answered for the open `quazi`
document:

```bash
python3 tests/lsp-runtime.py --hx /path/to/hx --qz /path/to/qz
```

Check the installation steps above end to end (Helix 25.07, a C compiler and
`git` on `PATH`). The script merges `languages.toml` into an isolated user
configuration, copies the queries, runs `hx --grammar fetch` and
`hx --grammar build`, and requires `hx --health quazi` to report the server,
the parser and the highlight queries. Until the pinned grammar revision is
published, it fetches that revision from the local `../tree-sitter` checkout
(override with `QUAZI_TREE_SITTER_DIR`):

```bash
HX=/path/to/hx QZ=/path/to/qz bash tests/install-smoke.sh
```
