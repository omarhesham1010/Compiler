from dataclasses import dataclass, asdict

from .tokens import Token, TokenType


@dataclass
class SemanticError:
    message: str
    line: int
    col: int
    severity: str = "error"

    def to_dict(self) -> dict:
        return asdict(self)


REL_OPS = {"==", "!=", "<", ">", "<=", ">="}
LOGIC_OPS = {"&&", "||"}
ARITH_OPS = {"+", "-", "*", "/", "%"}


class _Stream:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self, offset: int = 0) -> Token | None:
        idx = self.i + offset
        return self.tokens[idx] if 0 <= idx < len(self.tokens) else None

    def advance(self) -> Token | None:
        tok = self.peek()
        if tok is not None:
            self.i += 1
        return tok

    def eof(self) -> bool:
        return self.i >= len(self.tokens)


# Phase 2: validate the token stream and report semantic errors.
def analyze(tokens: list[Token]) -> list[SemanticError]:
    errors: list[SemanticError] = []
    declared: dict[str, str] = {}  # var_name -> data_type
    s = _Stream(tokens)
    brace_depth = 0  # tracks { } outside of if-bodies (e.g. while/for blocks)

    while not s.eof():
        tok = s.peek()
        if tok is None:
            break

        if tok.type == TokenType.IDENTIFIER.value and tok.value in {
            "int", "float", "string", "double", "bool", "char"
        }:
            _check_declaration(s, declared, errors)
            continue

        if tok.type == TokenType.RESERVED.value and tok.value == "if":
            _check_if_statement(s, declared, errors)
            continue

        if tok.type in (TokenType.IDENTIFIER_NAME.value, TokenType.VARIABLE.value):
            _check_assignment_or_use(s, declared, errors)
            continue

        if tok.type == TokenType.SYMBOL.value and tok.value == "{":
            brace_depth += 1
            s.advance()
            continue

        if tok.type == TokenType.SYMBOL.value and tok.value == "}":
            if brace_depth > 0:
                brace_depth -= 1
            else:
                errors.append(SemanticError(
                    "Unexpected '}' — no matching opening '{'",
                    tok.line, tok.col
                ))
            s.advance()
            continue

        if tok.type == TokenType.UNKNOWN.value:
            errors.append(SemanticError(
                f"Unknown character '{tok.value}'", tok.line, tok.col
            ))

        s.advance()

    return errors


def _check_declaration(s: _Stream, declared: dict, errors: list) -> None:
    dtype_tok = s.advance()
    name_tok = s.peek()

    if name_tok is None or name_tok.type not in (
        TokenType.VARIABLE.value, TokenType.IDENTIFIER_NAME.value
    ):
        errors.append(SemanticError(
            f"Expected variable name after '{dtype_tok.value}'",
            dtype_tok.line, dtype_tok.col
        ))
        return

    s.advance()
    if name_tok.value in declared:
        errors.append(SemanticError(
            f"Variable '{name_tok.value}' already declared",
            name_tok.line, name_tok.col
        ))
    else:
        declared[name_tok.value] = dtype_tok.value

    nxt = s.peek()
    if nxt and nxt.value == "=":
        s.advance()
        value_tok = s.peek()
        if value_tok is not None:
            _check_type_match(dtype_tok.value, value_tok, declared, errors)
        # consume up to ;
        while not s.eof():
            t = s.advance()
            if t and t.value == ";":
                break
    elif nxt and nxt.value == ";":
        s.advance()


def _check_type_match(dtype: str, value_tok: Token, declared: dict, errors: list) -> None:
    if value_tok.type == TokenType.STRING.value and dtype != "string":
        errors.append(SemanticError(
            f"Type mismatch: cannot assign string literal to '{dtype}'",
            value_tok.line, value_tok.col
        ))
    elif value_tok.type == TokenType.NUMBER.value and dtype == "string":
        errors.append(SemanticError(
            f"Type mismatch: cannot assign number to 'string'",
            value_tok.line, value_tok.col
        ))


def _check_assignment_or_use(s: _Stream, declared: dict, errors: list) -> None:
    name_tok = s.advance()
    if name_tok.value not in declared:
        errors.append(SemanticError(
            f"Use of undeclared variable '{name_tok.value}'",
            name_tok.line, name_tok.col
        ))
    nxt = s.peek()
    if nxt and nxt.value == "=":
        # consume the rest of the assignment until ;
        s.advance()
        while not s.eof():
            t = s.advance()
            if t and t.value == ";":
                break


# Validates the if-statement grammar from the project diagram:
# if ( Operand RelOp Operand ( LogicOp Operand RelOp Operand )* ) { ... }
def _check_if_statement(s: _Stream, declared: dict, errors: list) -> None:
    if_tok = s.advance()  # 'if'

    open_paren = s.peek()
    if not open_paren or open_paren.value != "(":
        errors.append(SemanticError(
            "Expected '(' after 'if'", if_tok.line, if_tok.col
        ))
        return
    s.advance()

    _check_condition(s, declared, errors)

    close_paren = s.peek()
    if not close_paren or close_paren.value != ")":
        line = close_paren.line if close_paren else if_tok.line
        col = close_paren.col if close_paren else if_tok.col
        errors.append(SemanticError("Expected ')' to close if-condition", line, col))
        return
    s.advance()

    open_brace = s.peek()
    if not open_brace or open_brace.value != "{":
        line = open_brace.line if open_brace else if_tok.line
        col = open_brace.col if open_brace else if_tok.col
        errors.append(SemanticError("Expected '{' to start if-body", line, col))
        return
    s.advance()

    depth = 1
    while not s.eof() and depth > 0:
        t = s.advance()
        if t.value == "{":
            depth += 1
        elif t.value == "}":
            depth -= 1
    if depth != 0:
        errors.append(SemanticError("Unmatched '{' — missing '}'", if_tok.line, if_tok.col))


def _check_condition(s: _Stream, declared: dict, errors: list) -> None:
    while True:
        _check_operand(s, declared, errors)

        rel = s.peek()
        if not rel or rel.value not in REL_OPS:
            line = rel.line if rel else 1
            col = rel.col if rel else 1
            got = rel.value if rel else "end of input"
            errors.append(SemanticError(
                f"Expected relational operator (==, !=, <, >, <=, >=), got '{got}'",
                line, col
            ))
            return
        s.advance()

        _check_operand(s, declared, errors)

        nxt = s.peek()
        if nxt and nxt.value in LOGIC_OPS:
            s.advance()
            continue
        return


def _check_operand(s: _Stream, declared: dict, errors: list) -> None:
    tok = s.peek()
    if tok is None:
        errors.append(SemanticError("Expected operand (variable or number)", 1, 1))
        return

    if tok.type == TokenType.NUMBER.value:
        s.advance()
        return

    if tok.type in (TokenType.VARIABLE.value, TokenType.IDENTIFIER_NAME.value):
        if tok.value not in declared:
            errors.append(SemanticError(
                f"Use of undeclared variable '{tok.value}'",
                tok.line, tok.col
            ))
        s.advance()
        return

    errors.append(SemanticError(
        f"Expected operand (variable or number), got '{tok.value}'",
        tok.line, tok.col
    ))
    s.advance()
