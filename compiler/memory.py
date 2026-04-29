from dataclasses import dataclass, asdict, field

from .tokens import Token, TokenType


@dataclass
class MemoryStep:
    line: int
    var: str
    value: object
    expression: str
    all_vars: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


_PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "%": 2}
_NUMERIC_TYPES = {"int", "float", "double", "bool"}


# Phase 3: walk declarations + assignments, compute values, return a per-step trace.
def execute(tokens: list[Token]) -> list[MemoryStep]:
    trace: list[MemoryStep] = []
    env: dict[str, object] = {}
    types: dict[str, str] = {}
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.IDENTIFIER.value and tok.value in _NUMERIC_TYPES | {"string", "char"}:
            i = _run_declaration(tokens, i, env, types, trace)
            continue

        if tok.type in (TokenType.VARIABLE.value, TokenType.IDENTIFIER_NAME.value):
            if i + 1 < n and tokens[i + 1].value == "=":
                i = _run_assignment(tokens, i, env, types, trace)
                continue

        if tok.type == TokenType.RESERVED.value and tok.value == "if":
            i = _skip_if(tokens, i)
            continue

        i += 1

    return trace


def _run_declaration(tokens, i, env, types, trace) -> int:
    dtype = tokens[i].value
    i += 1
    if i >= len(tokens):
        return i
    name = tokens[i].value
    i += 1
    types[name] = dtype

    if i < len(tokens) and tokens[i].value == "=":
        i += 1
        end_idx = _find_semicolon(tokens, i)
        expr_tokens = tokens[i:end_idx]
        value = _eval_expression(expr_tokens, env)
        env[name] = _coerce(value, dtype)
        trace.append(MemoryStep(
            line=tokens[i - 2].line,
            var=name,
            value=env[name],
            expression=_pretty(expr_tokens),
            all_vars=dict(env),
        ))
        return end_idx + 1

    env[name] = _default_value(dtype)
    trace.append(MemoryStep(
        line=tokens[i - 1].line,
        var=name,
        value=env[name],
        expression="(default)",
        all_vars=dict(env),
    ))
    if i < len(tokens) and tokens[i].value == ";":
        i += 1
    return i


def _run_assignment(tokens, i, env, types, trace) -> int:
    name = tokens[i].value
    line = tokens[i].line
    i += 2  # skip name + '='
    end_idx = _find_semicolon(tokens, i)
    expr_tokens = tokens[i:end_idx]
    value = _eval_expression(expr_tokens, env)
    if name in types:
        value = _coerce(value, types[name])
    env[name] = value
    trace.append(MemoryStep(
        line=line,
        var=name,
        value=value,
        expression=_pretty(expr_tokens),
        all_vars=dict(env),
    ))
    return end_idx + 1


def _skip_if(tokens, i) -> int:
    while i < len(tokens) and tokens[i].value != "{":
        i += 1
    if i >= len(tokens):
        return i
    depth = 1
    i += 1
    while i < len(tokens) and depth > 0:
        if tokens[i].value == "{":
            depth += 1
        elif tokens[i].value == "}":
            depth -= 1
        i += 1
    return i


def _find_semicolon(tokens, start) -> int:
    j = start
    while j < len(tokens) and tokens[j].value != ";":
        j += 1
    return j


# Shunting-Yard: infix → postfix → evaluate.
def _eval_expression(tokens: list[Token], env: dict) -> object:
    if not tokens:
        return 0

    output: list = []
    op_stack: list[str] = []

    for t in tokens:
        if t.type == TokenType.NUMBER.value:
            output.append(_parse_number(t.value))
        elif t.type == TokenType.STRING.value:
            output.append(t.value.strip('"'))
        elif t.type in (TokenType.VARIABLE.value, TokenType.IDENTIFIER_NAME.value):
            output.append(env.get(t.value, 0))
        elif t.value in _PRECEDENCE:
            while (op_stack and op_stack[-1] != "("
                   and _PRECEDENCE.get(op_stack[-1], 0) >= _PRECEDENCE[t.value]):
                output.append(op_stack.pop())
            op_stack.append(t.value)
        elif t.value == "(":
            op_stack.append("(")
        elif t.value == ")":
            while op_stack and op_stack[-1] != "(":
                output.append(op_stack.pop())
            if op_stack and op_stack[-1] == "(":
                op_stack.pop()
    while op_stack:
        output.append(op_stack.pop())

    stack: list = []
    for item in output:
        if isinstance(item, str) and item in _PRECEDENCE:
            if len(stack) < 2:
                return 0
            b = stack.pop()
            a = stack.pop()
            stack.append(_apply(a, b, item))
        else:
            stack.append(item)
    return stack[-1] if stack else 0


def _apply(a, b, op):
    try:
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/": return a / b if b != 0 else 0
        if op == "%": return a % b if b != 0 else 0
    except TypeError:
        return 0
    return 0


def _parse_number(s: str):
    if "." in s:
        return float(s)
    return int(s)


def _coerce(value, dtype):
    try:
        if dtype in ("int",):
            return int(value)
        if dtype in ("float", "double"):
            return float(value)
        if dtype == "bool":
            return bool(value)
        if dtype in ("string", "char"):
            return str(value)
    except (ValueError, TypeError):
        return value
    return value


def _default_value(dtype):
    if dtype == "int": return 0
    if dtype in ("float", "double"): return 0.0
    if dtype == "bool": return False
    if dtype in ("string", "char"): return ""
    return 0


def _pretty(tokens: list[Token]) -> str:
    return " ".join(t.value for t in tokens)
