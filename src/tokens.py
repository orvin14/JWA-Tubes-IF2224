from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    KEYWORD = auto()
    
    # Identifiers and Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()
    
    # Operators
    ARITHMETIC_OPERATOR = auto()
    RELATIONAL_OPERATOR = auto()
    LOGICAL_OPERATOR = auto()
    ASSIGN_OPERATOR = auto()
    RANGE_OPERATOR = auto()
    
    # Delimiters
    SEMICOLON = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    LPARENTHESIS = auto()
    RPARENTHESIS = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    
    # Comments
    COMMENT_START = auto()
    COMMENT_END = auto()
    
    # End of file
    EOF = auto()
    UNKNOWN = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int = 0
    column: int = 0
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"