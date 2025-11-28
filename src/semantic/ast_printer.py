from .ast_nodes import *
from .semantic_analyzer import SemanticAnalyzer

def print_decorated_ast(node: ASTNode, level: int = 0, prefix: str = "", is_last: bool = True):
    indent = "    " * level
    connector = "└─ " if is_last else "├─ "
    child_prefix = "    " if is_last else "│   "

    if level == 0:
        print(f"ProgramNode(name: '{node.name}')")
        decl_node = None
        block_node = None
        for child in node.children:
            if child.node_type == "Declarations":
                decl_node = child
            elif child.node_type == "CompoundStatement":
                block_node = child

        if decl_node:
            print(" ├─ Declarations")
            for i, child in enumerate(decl_node.children):
                last = i == len(decl_node.children) - 1
                print_decorated_ast(child, level + 2, " │   " if not last else "     ", last)

        if block_node:
            print(f" └─ Block → block_index:{block_node.block_index}, lev:1")
            for i, stmt in enumerate(block_node.children):
                last = i == len(block_node.children) - 1
                print_decorated_ast(stmt, level + 2, "     ", last)
        return

    # VarDecl
    if isinstance(node, VarDeclNode):
        deco = f"tab_index:{node.tab_index}, type:{node.data_type.name.lower()}, lev:0"
        print(f"{prefix}{connector}VarDecl('{node.identifier}') → {deco}")
        return

    # Assignment
    if isinstance(node, AssignmentNode) and len(node.children) >= 2:
        target = node.children[0]
        value = node.children[1]

        target_name = target.identifier if hasattr(target, 'identifier') else "???"

        # Format value
        if isinstance(value, NumberNode):
            val_str = f"{value.value} → type={'integer' if isinstance(value.value, int) else 'real'}"
        elif isinstance(value, CharNode):
            val_str = f"'{value.value}' → type:char"
        elif isinstance(value, CharNode):
            val_str = f"'{value.value}' → type:char"
        elif isinstance(value, UnaryExpressionNode):
            opd = value.children[0]
            inner = str(opd).split("→")[0].strip() if "→" in str(opd) else str(opd)
            val_str = f"NotExpression({inner}) → type:boolean"
        elif isinstance(value, BinaryExpressionNode):
            op_map = {'GT': '>', 'LT': '<', 'GE': '>=', 'LE': '<=', 'EQ': '=', 'NE': '<>'}
            op = op_map.get(value.operator, value.operator)
            l = f"'{value.children[0].identifier}'" if hasattr(value.children[0], 'identifier') else str(value.children[0])
            r = str(value.children[1])
            val_str = f"({l} {op} {r}) → type:boolean"
        else:
            val_str = str(value)

        print(f"{prefix}{connector}Assign('{target_name}' := {val_str}) → type:void")

        # Target detail
        tgt_deco = f"tab_index:{target.tab_index}, type:{target.data_type.name.lower()}"
        print(f"{prefix}{child_prefix}├─ target '{target_name}' → {tgt_deco}")

        # Value detail
        print(f"{prefix}{child_prefix}└─ value {val_str.split('→')[0].strip()} → {val_str.split('→')[-1].strip()}")
        return

    # Fallback
    print(f"{prefix}{connector}{node}")
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