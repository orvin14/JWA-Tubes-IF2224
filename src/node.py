from typing import List, Optional
from tokens import Token

class ParseNode:
    """Node untuk parse tree - langsung compatible dengan M3"""
    def __init__(self, name: str, token: Optional[Token] = None):
        self.name = name
        self.children: List['ParseNode'] = []
        self.token = token

    def add_child(self, node: 'ParseNode'):
        if node:
            self.children.append(node)

    def print_tree(self, level: int = 0):
        if level == 0:
            indent = ""
            prefix = ""
        else:
            indent = "   " * (level - 1)
            prefix = "└─ "
        
        if self.token:
            token_type = self.token.type.name
            token_value = self.token.value
            print(f"{indent}{prefix}{token_type}({token_value!r})")
        else:
            print(f"{indent}{prefix}{self.name}")
            
        for child in self.children:
            child.print_tree(level + 1)
    
    def __repr__(self):
        return f"ParseNode({self.name})"