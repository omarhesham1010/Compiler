from .tokens import (
    DATA_TYPES,
    ONE_CHAR_SYMBOLS,
    RESERVED_WORDS,
    Token,
    TokenType,
    TWO_CHAR_SYMBOLS,
)


# Phase 1: turn raw source code into a flat list of classified tokens.
def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    line = 1
    col = 1
    prev_was_datatype = False
    n = len(source)

    while i < n:
        ch = source[i]

        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        if ch.isdigit():
            start_col = col
            num = ""
            seen_dot = False
            while i < n and (source[i].isdigit() or (source[i] == "." and not seen_dot)):
                if source[i] == ".":
                    seen_dot = True
                num += source[i]
                i += 1
                col += 1
            tokens.append(Token(num, TokenType.NUMBER.value, line, start_col))
            prev_was_datatype = False
            continue

        if ch == '"':
            start_col = col
            i += 1
            col += 1
            buf = ""
            while i < n and source[i] != '"' and source[i] != "\n":
                buf += source[i]
                i += 1
                col += 1
            if i < n and source[i] == '"':
                i += 1
                col += 1
            tokens.append(Token(f'"{buf}"', TokenType.STRING.value, line, start_col))
            prev_was_datatype = False
            continue

        if ch.isalpha() or ch == "_":
            start_col = col
            word = ""
            while i < n and (source[i].isalnum() or source[i] == "_"):
                word += source[i]
                i += 1
                col += 1

            if word in DATA_TYPES:
                tokens.append(Token(word, TokenType.IDENTIFIER.value, line, start_col))
                prev_was_datatype = True
            elif word in RESERVED_WORDS:
                tokens.append(Token(word, TokenType.RESERVED.value, line, start_col))
                prev_was_datatype = False
            elif prev_was_datatype:
                tokens.append(Token(word, TokenType.VARIABLE.value, line, start_col))
                prev_was_datatype = False
            else:
                tokens.append(Token(word, TokenType.IDENTIFIER_NAME.value, line, start_col))
                prev_was_datatype = False
            continue

        if i + 1 < n:
            two = source[i:i + 2]
            if two in TWO_CHAR_SYMBOLS:
                tokens.append(Token(two, TokenType.SYMBOL.value, line, col))
                i += 2
                col += 2
                prev_was_datatype = False
                continue

        if ch in ONE_CHAR_SYMBOLS:
            tokens.append(Token(ch, TokenType.SYMBOL.value, line, col))
            i += 1
            col += 1
            prev_was_datatype = False
            continue

        tokens.append(Token(ch, TokenType.UNKNOWN.value, line, col))
        i += 1
        col += 1
        prev_was_datatype = False

    return tokens
