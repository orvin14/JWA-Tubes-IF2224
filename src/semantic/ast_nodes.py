from __future__ import annotations
from typing import List, Optional
from dataclasses import dataclass, field
from tokens import Token

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .symbol_table import BaseType

@dataclass
class ASTNode:
    node_type: str
    children: List[ASTNode] = field(default_factory=list)
    token: Optional[Token] = None
    data_type: Optional['BaseType'] = None
    tab_index: int = -1
    block_index: int = -1
    
    def add_child(self, child: ASTNode):
        if child:
            self.children.append(child)
        
    def __repr__(self):
        return f"{self.node_type}(type={self.data_type}, tab_idx={self.tab_index})"

@dataclass
class ProgramNode(ASTNode):
    name: str = ""
    
    def __init__(self, node_type: str, name: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.name = name
    
    def __repr__(self):
        return f"ProgramNode(name: '{self.name}')"

@dataclass
class VarDeclNode(ASTNode):
    identifier: str = ""
    
    def __init__(self, node_type: str, identifier: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.identifier = identifier
    
    def __repr__(self):
        return f"VarDecl('{self.identifier}')"

@dataclass
class AssignmentNode(ASTNode):
    def __repr__(self):
        if len(self.children) >= 2:
            target = self.children[0]
            value = self.children[1]
            
            if isinstance(target, VariableNode):
                target_str = f"'{target.identifier}'"
            else:
                target_str = str(target)
                
            if isinstance(value, BinaryExpressionNode):
                if len(value.children) >= 2:
                    left = value.children[0]
                    right = value.children[1]
                    left_str = f"'{left.identifier}'" if isinstance(left, VariableNode) else str(left)
                    right_str = str(right)
                    value_str = f"{left_str}{value.operator}{right_str}"
                else:
                    value_str = str(value)
            else:
                value_str = str(value)
                
            return f"Assign({target_str} := {value_str})"
        return "Assign(?)"

@dataclass
class BinaryExpressionNode(ASTNode):
    operator: str = ""
    
    def __init__(self, node_type: str, operator: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.operator = operator
    
    def __repr__(self):
        if len(self.children) >= 2:
            left = self.children[0]
            right = self.children[1]
            
            op_map = {
                'GT': '>', 'LT': '<', 'GE': '>=', 'LE': '<=', 
                'EQ': '=', 'NE': '<>', 'AND': ' dan ', 'OR': ' atau ',
                '+': '+', '-': '-', '*': '*', '/': '/', 
                'bagi': ' bagi ', 'mod': ' mod ', 
                'dan': ' dan ', 'atau': ' atau '
            }
            pretty_op = op_map.get(self.operator, self.operator)
            
            def format_operand(operand):
                if isinstance(operand, VariableNode):
                    return f"'{operand.identifier}'"
                elif isinstance(operand, (NumberNode, CharNode)):
                    return repr(operand)
                elif isinstance(operand, (BinaryExpressionNode, UnaryExpressionNode)):
                    return f"({repr(operand)})" 
                return repr(operand)

            left_str = format_operand(left)
            right_str = format_operand(right)
            
            if pretty_op in ['+', '-', '*', '/']:
                 return f"{left_str}{pretty_op}{right_str}"
            else:
                 return f"{left_str}{pretty_op}{right_str}"
                 
        return f"BinOp '{self.operator}'"

@dataclass
class VariableNode(ASTNode):
    identifier: str = ""
    is_array_element: bool = False
    
    def __init__(self, node_type: str, identifier: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.identifier = identifier
    
    def __repr__(self):
        return f"Var('{self.identifier}')"

@dataclass
class NumberNode(ASTNode):
    value: float = 0
    
    def __init__(self, node_type: str, value: float = 0, **kwargs):
        super().__init__(node_type, **kwargs)
        self.value = value
    
    def __repr__(self):
        return f"{self.value}"

@dataclass
class StringNode(ASTNode):
    value: str = ""
    
    def __init__(self, node_type: str, value: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.value = value
    
    def __repr__(self):
        return f"String('{self.value}')"

@dataclass
class BooleanNode(ASTNode):
    value: bool = False
    identifier: str = ""
    
    def __init__(self, node_type: str, value: bool = False, identifier: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.value = value
        self.identifier = identifier
    
    def __repr__(self):
        return f"Boolean('{self.identifier}')"

@dataclass
class ProcedureCallNode(ASTNode):
    procedure_name: str = ""
    is_user_defined: bool = False
    
    def __init__(self, node_type: str, procedure_name: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.procedure_name = procedure_name
    
    def __repr__(self):
        return f"ProcedureCall('{self.procedure_name}')"
    
@dataclass
class CharNode(ASTNode):
    value: str = ""
    
    def __init__(self, node_type: str = "Char", value: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.value = value
    
    def __repr__(self):
        return f"'{self.value}'"

@dataclass
class UnaryExpressionNode(ASTNode):
    operator: str = ""
    
    def __init__(self, node_type: str = "UnaryExpr", operator: str = "", **kwargs):
        super().__init__(node_type, **kwargs)
        self.operator = operator
    
    def __repr__(self):
        if self.children:
            operand = self.children[0]
            op = "tidak " if self.operator == "tidak" else f"{self.operator} "
            return f"{op}({operand})"
        return f"{self.operator}(?)"


@dataclass
class CompoundStatementNode(ASTNode):
    def __repr__(self):
        if self.block_index != -1:
            return f"CompoundStatement → block_index:{self.block_index}"
        return "CompoundStatement"

@dataclass
class ForStatementNode(ASTNode):
    is_downto: bool = False
    
    def __repr__(self):
        if len(self.children) >= 3:
            var = self.children[0]
            start = self.children[1]
            end = self.children[2]
            dir = "downto" if self.is_downto else "to"
            return f"ForStatement({var} := {start} {dir} {end})"
        return "ForStatement(?)"

@dataclass
class IfStatementNode(ASTNode):
    def __repr__(self):
        if self.children:
            cond = self.children[0]
            then_part = " then ..." if len(self.children) > 1 else ""
            else_part = " else ..." if len(self.children) > 2 else ""
            return f"IfStatement({cond}{then_part}{else_part})"
        return "IfStatement(?)"

@dataclass
class WhileStatementNode(ASTNode):
    def __repr__(self):
        if self.children:
            cond = self.children[0]
            return f"WhileStatement({cond})"
        return "WhileStatement(?)"