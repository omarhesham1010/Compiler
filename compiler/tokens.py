from dataclasses import dataclass, asdict
from enum import Enum


class TokenType(str, Enum):
    IDENTIFIER = "Identifier"
    RESERVED = "Reserved"
    VARIABLE = "Variable"
    IDENTIFIER_NAME = "Identifier_Name"
    NUMBER = "Number"
    STRING = "String"
    SYMBOL = "Symbol"
    UNKNOWN = "Unknown"


DATA_TYPES = {"int", "float", "string", "double", "bool", "char"}
RESERVED_WORDS = {"for", "while", "if", "do", "return", "break", "continue", "end"}

TWO_CHAR_SYMBOLS = {"==", "!=", "<=", ">=", "&&", "||", "++", "--"}
ONE_CHAR_SYMBOLS = set("+-*/%=<>!(){},;")


@dataclass
class Token:
    value: str
    type: str
    line: int
    col: int

    def to_dict(self) -> dict:
        return asdict(self)
