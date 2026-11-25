#!/usr/bin/env bash
# Follow the README installation steps in an isolated home directory: merge
# languages.toml into the user configuration, copy the runtime queries,
# fetch and build the pinned grammar, and require `hx --health quazi` to find
# the server, the parser and the highlight queries.
#
# The pinned revision may not be published yet, so the grammar is fetched
# from a local tree-sitter checkout (QUAZI_TREE_SITTER_DIR, default
# ../tree-sitter) at the same revision.
set -euo pipefail

: "${HX:=hx}"
: "${QZ:=qz}"
repository_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
grammar_dir=$(CDPATH= cd -- "${QUAZI_TREE_SITTER_DIR:-$repository_dir/../tree-sitter}" && pwd)
qz_path=$(type -P -- "$QZ")
work_dir=$(mktemp -d)
trap 'rm -rf -- "$work_dir"' EXIT

config_dir=$work_dir/config/helix
mkdir -p "$config_dir/runtime/queries" "$work_dir/bin"
ln -s "$qz_path" "$work_dir/bin/qz"
{
  printf 'use-grammars = { only = ["quazi"] }\n\n'
  sed "s|git = \"https://github.com/quazilang/tree-sitter\"|git = \"$grammar_dir\"|" \
    "$repository_dir/languages.toml"
} > "$config_dir/languages.toml"
cp -r "$repository_dir/runtime/queries/quazi" "$config_dir/runtime/queries/"

export HOME=$work_dir XDG_CONFIG_HOME=$work_dir/config XDG_CACHE_HOME=$work_dir/cache
export PATH=$work_dir/bin:$PATH
"$HX" --grammar fetch
"$HX" --grammar build
test -f "$config_dir/runtime/grammars/quazi.so" || { printf 'quazi.so was not built\n' >&2; exit 1; }

health=$("$HX" --health quazi 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
printf '%s\n' "$health"
for expected in "✓ quazi: $work_dir/bin/qz" "Tree-sitter parser: ✓" "Highlight queries: ✓"; do
  grep -qF -- "$expected" <<<"$health" || { printf 'missing: %s\n' "$expected" >&2; exit 1; }
done
printf 'PASS Helix install smoke\n'
