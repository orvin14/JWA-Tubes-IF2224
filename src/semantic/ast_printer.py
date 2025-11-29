from .ast_nodes import *
from .semantic_analyzer import SemanticAnalyzer

def format_expression(node: ASTNode) -> str:
    """
    Recursive function to format expressions with proper parentheses
    """
    if isinstance(node, NumberNode):
        return str(node.value)
    
    elif isinstance(node, CharNode):
        return f"'{node.value}'"
    
    elif isinstance(node, VariableNode):
        return f"'{node.identifier}'"
    
    elif isinstance(node, UnaryExpressionNode):
        operand = format_expression(node.children[0])
        return f"tidak {operand}"
    
    elif isinstance(node, BinaryExpressionNode):
        left = format_expression(node.children[0]) if node.children else "?"
        right = format_expression(node.children[1]) if len(node.children) > 1 else "?"
        
        op_map = {
            'GT': '>', 'LT': '<', 'GE': '>=', 'LE': '<=', 
            'EQ': '=', 'NE': '<>', 'atau': 'atau', 'dan': 'dan',
            '+': '+', '-': '-', '*': '*', '/': '/', 
            'bagi': 'bagi', 'mod': 'mod'
        }
        op = op_map.get(node.operator, node.operator)

        needs_parens_left = False
        needs_parens_right = False
        
        if isinstance(node.children[0], BinaryExpressionNode):
            left_op = node.children[0].operator
            if node.operator in ['dan', '*', '/', 'bagi', 'mod']:
                if left_op in ['atau', '+', '-']:
                    needs_parens_left = True
            elif node.operator in ['+', '-']:
                if left_op == 'atau':
                    needs_parens_left = True
        
        if isinstance(node.children[1], BinaryExpressionNode):
            right_op = node.children[1].operator
            if node.operator == 'atau':
                if right_op in ['dan', '+', '-', '*', '/', 'bagi', 'mod']:
                    needs_parens_right = True
            elif node.operator in ['+', '-']:
                if right_op in ['dan', '*', '/', 'bagi', 'mod']:
                    needs_parens_right = True
            elif node.operator == 'dan':
                if right_op in ['*', '/', 'bagi', 'mod']:
                    needs_parens_right = True

        left_str = f"({left})" if needs_parens_left else left
        right_str = f"({right})" if needs_parens_right else right
        
        return f"{left_str}{op}{right_str}"
    
    else:
        return str(node)


def print_decorated_ast(node: ASTNode, level: int = 0, prefix: str = "", is_last: bool = True):
    indent = "    " * level
    connector = "└─ " if is_last else "├─ "
    child_prefix = "    " if is_last else "│   "

    # Root ProgramNode
    if level == 0:
        program_name = node.identifier if hasattr(node, 'identifier') else node.name
        print(f"ProgramNode(name: {program_name!r})")
        
        decl_node = None
        block_node = None
        for child in node.children:
            if child.node_type == "Declarations":
                decl_node = child
            elif child.node_type == "CompoundStatement" or child.node_type == "Block":
                block_node = child

        if decl_node:
            print(" ├─ Declarations")
            for i, child in enumerate(decl_node.children):
                last = i == len(decl_node.children) - 1
                print_decorated_ast(child, level + 2, " │   " if not last else "     ", last)

        if block_node:
            block_idx = block_node.block_index if hasattr(block_node, 'block_index') else 1
            print(f" └─ Block → block_index:{block_idx}, lev:1")
            for i, stmt in enumerate(block_node.children):
                last = i == len(block_node.children) - 1
                print_decorated_ast(stmt, level + 2, "     ", last)
        return

    # VarDecl
    if isinstance(node, VarDeclNode):
        type_str = node.data_type.name.lower() if node.data_type else "unknown"
        deco = f"tab_index:{node.tab_index}, type:{type_str}, lev:0"
        print(f"{prefix}{connector}VarDecl({node.identifier!r}) → {deco}")
        return

    # Assignment
    if isinstance(node, AssignmentNode) and len(node.children) >= 2:
        target = node.children[0]
        value = node.children[1]

        target_name = target.identifier if hasattr(target, 'identifier') else "???"
        
        # Format value expression using recursive formatter
        val_expr = format_expression(value)
        val_type = value.data_type.name.lower() if hasattr(value, 'data_type') and value.data_type else 'unknown'
        
        # Print assignment header
        print(f"{prefix}{connector}Assign('{target_name}' := ({val_expr}) → type:{val_type}) → type:void")

        # Print target detail
        target_type = target.data_type.name.lower() if hasattr(target, 'data_type') and target.data_type else 'unknown'
        tgt_deco = f"tab_index:{target.tab_index}, type:{target_type}"
        print(f"{prefix}{child_prefix}├─ target '{target_name}' → {tgt_deco}")

        # Print value detail
        print(f"{prefix}{child_prefix}└─ value ({val_expr}) → type:{val_type}")
        return

    # IfStatement
    if isinstance(node, ASTNode) and node.node_type == "IfStatement":
        print(f"{prefix}{connector}IfStatement")
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            print_decorated_ast(child, level + 1, prefix + child_prefix, last)
        return

    # WhileStatement
    if isinstance(node, ASTNode) and node.node_type == "WhileStatement":
        print(f"{prefix}{connector}WhileStatement")
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            print_decorated_ast(child, level + 1, prefix + child_prefix, last)
        return

    # ForStatement
    if isinstance(node, ForStatementNode):
        is_downto = "turun_ke" if node.is_downto else "ke"
        print(f"{prefix}{connector}ForStatement ({is_downto})")
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            print_decorated_ast(child, level + 1, prefix + child_prefix, last)
        return

    # ProcedureCall
    if isinstance(node, ProcedureCallNode):
        proc_name = node.procedure_name if hasattr(node, 'procedure_name') else "???"
        print(f"{prefix}{connector}ProcedureCall({proc_name!r})")
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            print_decorated_ast(child, level + 1, prefix + child_prefix, last)
        return

    # Fallback for other nodes
    node_name = node.node_type if hasattr(node, 'node_type') else type(node).__name__
    print(f"{prefix}{connector}{node_name}")
    
    if hasattr(node, 'children') and node.children:
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            print_decorated_ast(child, level + 1, prefix + child_prefix, last)


def print_symbol_tables(analyzer: SemanticAnalyzer):
    """
    Print symbol tables (tab, btab, atab)
    """
    print("\n=== SYMBOL TABLES ===")
    
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