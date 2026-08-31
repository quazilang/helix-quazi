; Keep this in sync with tree-sitter/queries/highlights.scm.
["fn" "struct" "union" "trait" "enum" "impl" "type" "import" "pub" "unsafe"] @keyword
["ret" "if" "else" "for" "while" "match" "break" "continue"] @keyword.control
["true" "false"] @constant.builtin

(attribute name: (identifier) @attribute)
(struct_decl name: (identifier) @type)
(union_decl name: (identifier) @type)
(trait_decl name: (identifier) @type)
(enum_decl name: (identifier) @type)
(fn_decl name: (identifier) @function)
(struct_field name: (identifier) @property)
(param name: (identifier) @variable.parameter)

(string_literal) @string
(byte_string_literal) @string
(raw_string_literal) @string
(integer_literal) @constant.numeric.integer
(float_literal) @constant.numeric.float
(comment) @comment
