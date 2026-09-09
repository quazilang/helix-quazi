#!/usr/bin/env bash
set -euo pipefail

repository_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
grammar_dir=${QUAZI_TREE_SITTER_DIR:-"$repository_dir/../tree-sitter"}

if [[ ! -d $grammar_dir/.git ]]; then
  printf 'canonical tree-sitter checkout is unavailable: %s\n' "$grammar_dir" >&2
  exit 1
fi

configured_revision=$(sed -n 's/.*rev = "\([0-9a-f]*\)".*/\1/p' "$repository_dir/languages.toml")
canonical_revision=$(git -C "$grammar_dir" rev-parse HEAD)

if [[ $configured_revision != "$canonical_revision" ]]; then
  printf 'languages.toml pins %s; canonical checkout is %s\n' "$configured_revision" "$canonical_revision" >&2
  exit 1
fi

cmp "$grammar_dir/queries/highlights.scm" "$repository_dir/runtime/queries/quazi/highlights.scm"
