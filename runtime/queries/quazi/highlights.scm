; Keywords
[
  "fn" "struct" "union" "trait" "enum" "impl" "type" "import"
  "for" "if" "else" "match" "ret"
  "const" "var" "pub" "unsafe" "as" "dyn" "for"
] @keyword

; Control flow keywords get a more specific scope
["ret" "if" "else" "for" "match" "break" "continue"] @keyword.control

; Primitive types
[
  "i8" "i16" "i32" "i64"
  "u8" "u16" "u32" "u64"
  "isize" "usize"
  "f16" "f32" "f64"
  "bool" "str" "bytes" "void" "any"
] @type.builtin

; Function declarations
(fn_decl name: (identifier) @function)

; Type declarations
(struct_decl name: (identifier) @type)
(trait_decl  name: (identifier) @type)
(enum_decl   name: (identifier) @type)
(impl_decl   first_type: (named_type (qualified_identifier (identifier) @type)))
(impl_decl   for_type: (named_type (qualified_identifier (identifier) @type)))

; Enum variants
(enum_variant name: (identifier) @constant)

; Attributes
(attribute name: (identifier) @attribute)
"@" @punctuation.special

; Parameters
(param name: (identifier) @variable.parameter)

; Struct fields
(struct_field name: (identifier) @property)

; Function calls
(call_expr callee: (identifier) @function.call)
(call_expr
  callee: (field_expr field: (identifier) @function.method))

; Field access
(field_expr field: (identifier) @property)

; Literals
(integer_literal) @number
(float_literal)   @number.float
(string_literal)  @string
(byte_string_literal) @string
(raw_string_literal) @string
(bool_literal)    @boolean

; Comments
(comment) @comment

; Operators
[
  "+" "-" "*" "/" "%" "**" "&" "|" "^" "~" "<<" ">>"
  "=" "==" "!=" "<" "<=" ">" ">="
  "+=" "-=" "*=" "/=" "%="
  "++" "--"
  "&&" "||" "!"
  "=>" ".."
] @operator

; Punctuation
["," ";" ":"] @punctuation.delimiter
["{" "}" "[" "]" "(" ")"] @punctuation.bracket
