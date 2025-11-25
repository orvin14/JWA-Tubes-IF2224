from .ast_nodes import *
from .semantic_analyzer import SemanticAnalyzer

def print_decorated_ast(node: ASTNode, level: int = 0, prefix: str = "", is_last: bool = True):
    """
    Print decorated AST dengan informasi tipe dan symbol table references
    Format output sesuai contoh di spesifikasi
    """
    
    if level == 0:
        connector = ""
        child_prefix = ""
    else:
        connector = " └─ " if is_last else " ├─ "
        child_prefix = "    " if is_last else " │  "
    
    # Print ProgramNode
    if isinstance(node, ProgramNode):
        print(f"ProgramNode(name: '{node.name}')")
        
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            new_prefix = prefix + child_prefix
            print_decorated_ast(child, level + 1, new_prefix, is_last_child)
    
    # Print Declarations
    elif node.node_type == "Declarations":
        print(prefix + connector + "Declarations")
        
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            new_prefix = prefix + child_prefix
            print_decorated_ast(child, level + 1, new_prefix, is_last_child)
    
    # Print VarDecl
    elif isinstance(node, VarDeclNode):
        decorators = []
        if node.tab_index >= 0:
            decorators.append(f"tab_index:{node.tab_index}")
        if node.data_type:
            decorators.append(f"type:{node.data_type.name.lower()}")
        decorators.append(f"lev:{node.block_index}")
        
        decorator_str = f" → {', '.join(decorators)}"
        print(prefix + connector + f"VarDecl('{node.identifier}'){decorator_str}")
    
    # Print CompoundStatement (Block)
    elif node.node_type == "CompoundStatement":
        decorators = []
        if node.block_index >= 0:
            decorators.append(f"block_index:{node.block_index}")
        decorators.append(f"lev:1")
        
        decorator_str = f" → {', '.join(decorators)}"
        print(prefix + connector + f"Block{decorator_str}")
        
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            new_prefix = prefix + child_prefix
            print_decorated_ast(child, level + 1, new_prefix, is_last_child)
    
    # Print Assignment
    elif isinstance(node, AssignmentNode):
        if len(node.children) >= 2:
            target = node.children[0]
            value = node.children[1]
            
            target_str = f"'{target.identifier}'" if isinstance(target, VariableNode) else str(target)
            
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
            
            assign_str = f"Assign({target_str} := {value_str})"
        else:
            assign_str = "Assign(?)"
        
        decorators = []
        if node.data_type:
            decorators.append(f"type:{node.data_type.name.lower()}")
        
        decorator_str = f" → {', '.join(decorators)}" if decorators else ""
        print(prefix + connector + f"{assign_str}{decorator_str}")
        
        # Print children details
        if len(node.children) >= 2:
            target = node.children[0]
            value = node.children[1]
            
            if isinstance(target, VariableNode):
                decorators = []
                if target.tab_index >= 0:
                    decorators.append(f"tab_index:{target.tab_index}")
                if target.data_type:
                    decorators.append(f"type:{target.data_type.name.lower()}")
                
                decorator_str = f" → {', '.join(decorators)}" if decorators else ""
                print(prefix + child_prefix + " ├─ " + f"target '{target.identifier}'{decorator_str}")
            
            if isinstance(value, BinaryExpressionNode):
                decorators = []
                if value.data_type:
                    decorators.append(f"type:{value.data_type.name.lower()}")
                
                decorator_str = f" → {', '.join(decorators)}" if decorators else ""
                print(prefix + child_prefix + " └─ " + f"BinOp '{value.operator}'{decorator_str}")
                
                if len(value.children) >= 2:
                    left = value.children[0]
                    right = value.children[1]
                    
                    # Left operand
                    if isinstance(left, (VariableNode, NumberNode)):
                        left_decorators = []
                        if hasattr(left, 'tab_index') and left.tab_index >= 0:
                            left_decorators.append(f"tab_index:{left.tab_index}")
                        if left.data_type:
                            left_decorators.append(f"type:{left.data_type.name.lower()}")
                        
                        left_decorator_str = f" → {', '.join(left_decorators)}" if left_decorators else ""
                        left_repr = f"'{left.identifier}'" if isinstance(left, VariableNode) else str(left)
                        print(prefix + child_prefix + "     ├─ " + f"{left_repr}{left_decorator_str}")
                    
                    # Right operand
                    if isinstance(right, (VariableNode, NumberNode)):
                        right_decorators = []
                        if hasattr(right, 'tab_index') and right.tab_index >= 0:
                            right_decorators.append(f"tab_index:{right.tab_index}")
                        if right.data_type:
                            right_decorators.append(f"type:{right.data_type.name.lower()}")
                        
                        right_decorator_str = f" → {', '.join(right_decorators)}" if right_decorators else ""
                        right_repr = f"'{right.identifier}'" if isinstance(right, VariableNode) else str(right)
                        print(prefix + child_prefix + "     └─ " + f"{right_repr}{right_decorator_str}")
    
    # Print ProcedureCall
    elif isinstance(node, ProcedureCallNode):
        decorators = []
        if node.tab_index >= 0:
            if node.procedure_name in ['writeln', 'readln', 'write', 'read']:
                decorators.append("predefined")
            decorators.append(f"tab_index:{node.tab_index}")
        
        decorator_str = f" → {', '.join(decorators)}" if decorators else ""
        print(prefix + connector + f"{node.procedure_name}(...){decorator_str}")
    
    # Default: process children
    else:
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            new_prefix = prefix + child_prefix
            print_decorated_ast(child, level + 1, new_prefix, is_last_child)


def print_symbol_tables(analyzer: SemanticAnalyzer):
    """
    Print symbol tables (tab, btab, atab)
    """
    print("\n=== SYMBOL TABLES ===")
    
    # Print tab (identifier table)
    print("\nIdentifier Table (tab):")
    print("Idx  Name        Obj        Type    Ref  Nrm  Lev  Adr  Link")
    print("-" * 60)
    
    for i, entry in enumerate(analyzer.symbol_table.tab):
        if entry is not None:
            obj_name = entry['obj'].name if hasattr(entry['obj'], 'name') else str(entry['obj'])
            
            # Convert type to name
            from .symbol_table import BaseType
            try:
                type_name = BaseType(entry['type']).name if isinstance(entry['type'], int) else str(entry['type'])
            except:
                type_name = str(entry['type'])
            
            print(f"{i:3}  {entry['name']:10}  {obj_name:10}  {type_name:6}  "
                  f"{entry['ref']:3}  {entry['nrm']:3}  {entry['lev']:3}  "
                  f"{entry['adr']:3}  {entry['link']:4}")
    
    # Print btab (block table)
    print("\nBlock Table (btab):")
    print("Idx  Last  Lpar  Psze  Vsze")
    print("-" * 25)
    
    for i, entry in enumerate(analyzer.symbol_table.btab):
        print(f"{i:3}  {entry['last']:4}  {entry['lpar']:4}  "
              f"{entry['psze']:4}  {entry['vsze']:4}")
    
    # Print atab (array table)
    print("\nArray Table (atab):")
    if analyzer.symbol_table.atab:
        print("Idx  IdxType  ElemType  Eref  Low  High  ElemSize  Size")
        print("-" * 50)
        
        for i, entry in enumerate(analyzer.symbol_table.atab):
            from .symbol_table import BaseType
            try:
                idx_type = BaseType(entry['index_type']).name
                elem_type = BaseType(entry['element_type']).name
            except:
                idx_type = str(entry['index_type'])
                elem_type = str(entry['element_type'])
            
            print(f"{i:3}  {idx_type:7}  {elem_type:8}  {entry['eref']:4}  "
                  f"{entry['low']:3}  {entry['high']:4}  "
                  f"{entry['element_size']:8}  {entry['size']:4}")
    else:
        print("(empty)")