# Quazi for Helix

This is a Helix language-configuration fragment, not a standalone plugin.
Merge `languages.toml` into either `~/.config/helix/languages.toml` or a
project's `.helix/languages.toml`. Copy `runtime/queries/quazi/` into the
matching Helix runtime query directory.

It registers `.qz` as `source.quazi`, launches `qz lsp`, and pins the Quazi
Tree-sitter grammar to commit `685ebbf2760a443262a7c8deb51b04f25d2e78c9`.
After installing the fragment, run:

```bash
hx --grammar fetch
hx --grammar build
```

The grammar deliberately preserves opaque field attributes such as
`name: String @ini("username")`; Helix only highlights their syntax and leaves
their meaning to the library or tool that owns the attribute.
