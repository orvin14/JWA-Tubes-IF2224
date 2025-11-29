from typing import List, Optional, Tuple
from node import ParseNode
from tokens import Token, TokenType
from .symbol_table import SymbolTable, ObjType, BaseType
from .ast_nodes import *

class SemanticAnalyzer:
    """
    Semantic Analyzer untuk Pascal-S Compiler
    Melakukan type checking, scope checking, dan membangun decorated AST
    """
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_ast: Optional[ASTNode] = None
        self.errors: List[str] = []
        
    def analyze(self, parse_tree: ParseNode) -> ASTNode:
        """
        Main entry point untuk semantic analysis
        Input: Parse tree dari parser
        Output: Decorated AST
        """
        self.errors.clear()
        
        global_block_idx = self.symbol_table.enter_block()
        self.current_ast = self.visit(parse_tree)
        
        self.symbol_table.leave_block()

            
        return self.current_ast

    def error(self, message: str, token: Token = None):
        """Record semantic error"""
        if token:
            location = f" at line {token.line}, column {token.column}"
        else:
            location = ""
        self.errors.append(f"Semantic Error{location}: {message}")
    
    def clean_name(self, name: str) -> str:
        """Helper untuk membersihkan nama node dari < > dan spasi"""
        return name.replace("<", "").replace(">", "").strip()

    def visit(self, node: ParseNode) -> ASTNode:
        """
        Visitor pattern - dispatch ke method yang sesuai.
        Otomatis menormalisasi nama node (contoh: <program-header> -> visit_program_header)
        """
        clean_node_name = self.clean_name(node.name).replace("-", "_")

        if clean_node_name == "procedure/function_call":
            method_name = "visit_procedure_call"
        else:
            method_name = f'visit_{clean_node_name}'

        method = getattr(self, method_name, self.visit_default)
        
        try:
            return method(node)
        except Exception as e:
    #         print(f"\nBUG DI METHOD: {method_name}")
    #         print(f"Node name: {node.name}")
    #         print(f"Error: {e}")
    #         import traceback
    #         traceback.print_exc()  
            ast_node = ASTNode(node.name)
            for child in node.children:
                try:
                    res = self.visit(child)
                    if res: ast_node.add_child(res)
                except:
                    continue
            return ast_node
    
    def visit_default(self, node: ParseNode) -> ASTNode:
        """Default visitor - just traverse children"""
        ast_node = ASTNode(node.name)
        for child in node.children:
            res = self.visit(child)
            if res:
                ast_node.add_child(res)
        return ast_node
    
        
    def visit_program(self, node: ParseNode) -> ASTNode:
        """Visit program - VERSI YANG BENAR (FIXED 100%)"""
        program_name = "Unknown"
        
        if node.children and node.children[0].name == "<program-header>":
            header_children = node.children[0].children
            if len(header_children) > 1 and header_children[1].token:
                program_name = header_children[1].token.value
        
        # 1. Masukkan nama program ke symbol table (Level 0, Block 0)
        program_idx = self.symbol_table.enter_identifier(
            program_name, ObjType.PROGRAM, BaseType.VOID.value
        )
        
        # 2. PENTING: BUAT BLOCK UTAMA PROGRAM (Block 1, Level 1)
        main_block_idx = self.symbol_table.enter_block() 
        
        ast_node = ProgramNode("Program", name=program_name, 
                            token=node.children[0].children[1].token if node.children else None,
                            data_type=BaseType.VOID, tab_index=program_idx)
        
        for child in node.children:
            if child.name == "<declaration-part>":
                # 3. Proses deklarasi. Variabel sekarang akan masuk ke Block 1.
                decl_ast = self.visit(child)
                ast_node.add_child(decl_ast)
            elif child.name == "<compound-statement>":
                # 4. Proses statement body.
                compound_ast = self.visit(child)
                compound_ast.block_index = main_block_idx
                ast_node.add_child(compound_ast)
        
        # 5. Keluar dari block utama
        self.symbol_table.leave_block()
        
        return ast_node
    
    def visit_declaration_part(self, node: ParseNode) -> ASTNode:
        """Visit declaration part - support const, type, var, subprograms"""
        ast_node = ASTNode("Declarations")
        
        for child in node.children:
            name = self.clean_name(child.name)
            
            if name == "const-declaration":
                const_ast = self.visit(child)
                for const_child in const_ast.children:
                    ast_node.add_child(const_child)
            
            elif name == "type-declaration":
                type_ast = self.visit(child)
                for type_child in type_ast.children:
                    ast_node.add_child(type_child)
            
            elif name == "var-declaration":
                var_decl_ast = self.visit(child)
                for var_decl_child in var_decl_ast.children:
                    if isinstance(var_decl_child, VarDeclNode):
                        var_decl_child.block_index = 0
                        ast_node.add_child(var_decl_child)
            
            elif name == "subprogram-declaration":
                subprogram_ast = self.visit(child)
                if subprogram_ast:
                    ast_node.add_child(subprogram_ast)
        
        return ast_node
    def visit_block(self, node: ParseNode) -> ASTNode:
        """Visit block - handle declarations dan compound statement"""
        ast_node = ASTNode("Block", block_index=self.symbol_table.display[-1])
        
        for child in node.children:
            if child.name == "<declaration-part>":
                decl_ast = self.visit(child)
                ast_node.add_child(decl_ast)
            elif child.name == "<compound-statement>":
                compound_ast = self.visit(child)
                ast_node.add_child(compound_ast)
        
        return ast_node
    def visit_variable(self, node: ParseNode) -> ASTNode:
        """Visit variable (including array access)"""
        if (len(node.children) >= 4 and
            node.children[0].name == "IDENTIFIER" and
            node.children[1].name == "LBRACKET"):
            
            array_name = node.children[0].token.value
            array_idx = self.symbol_table.find_identifier(array_name)
            
            rbrace_idx = -1
            for i in range(2, len(node.children)):
                if node.children[i].name == "RBRACKET":
                    rbrace_idx = i
                    break
            
            if rbrace_idx > 2 and array_idx is not None:
                array_entry = self.symbol_table.tab[array_idx]
                
                if array_entry["type"] == BaseType.ARRAY.value:
                    array_ref = array_entry["ref"]
                    if array_ref < len(self.symbol_table.atab):
                        element_type = BaseType(self.symbol_table.atab[array_ref]["element_type"])
                        
                        index_expressions = []
                        for i in range(2, rbrace_idx):
                            name = self.clean_name(node.children[i].name)
                            if name == "expression":
                                index_expr = self.visit(node.children[i])
                                index_expressions.append(index_expr)
                                if hasattr(index_expr, 'value'):
                                    array_info = self.symbol_table.atab[array_ref]
                                    idx_val = int(index_expr.value)
                                    if idx_val < array_info["low"] or idx_val > array_info["high"]:
                                        self.error(
                                            f"Array index {idx_val} out of bounds "
                                            f"[{array_info['low']}..{array_info['high']}]"
                                        )
                        
                        var_node = VariableNode("ArrayElement", identifier=array_name,
                                            token=node.children[0].token,
                                            data_type=element_type, tab_index=array_idx)
                        var_node.is_array_element = True
                        var_node.index_expressions = index_expressions
                        return var_node
        
        for child in node.children:
            if child.name == "IDENTIFIER" and child.token:
                var_name = child.token.value
                var_idx = self.symbol_table.find_identifier(var_name)
                
                if var_idx is not None:
                    var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
                    return VariableNode("Variable", identifier=var_name,
                                    token=child.token, data_type=var_type, 
                                    tab_index=var_idx)
                else:
                    self.error(f"Undefined variable '{var_name}'", child.token)
                    return VariableNode("Variable", identifier=var_name,
                                    token=child.token, data_type=BaseType.VOID)
        
        return ASTNode("Variable", data_type=BaseType.VOID)

    
    def visit_var_declaration(self, node: ParseNode) -> ASTNode:
        ast_node = ASTNode("VarDeclaration")
        
        for child in node.children:
            # Skip keyword 'variabel'
            if child.name.startswith("KEYWORD"):
                continue
                
            # Proses setiap <var-item>
            if child.name == "<var-item>":
                var_item_ast = self.visit(child)
                
                # Extract VarDecl nodes
                for var_decl in var_item_ast.children:
                    if isinstance(var_decl, VarDeclNode):
                        # PENTING: Perbaiki block index agar sesuai dengan level saat ini (self.symbol_table.level)
                        var_decl.block_index = self.symbol_table.level 
                        ast_node.add_child(var_decl)
        
        return ast_node
    
    def visit_var_item(self, node: ParseNode) -> ASTNode:
        identifiers = []
        type_ast = None
        token_ref = None
        
        for child in node.children:
            if child.name == "<identifier-list>":
                identifiers = self.extract_identifiers(child)
                # Ambil token dari identifier pertama
                for id_child in child.children:
                    if id_child.name == "IDENTIFIER" and id_child.token:
                        token_ref = id_child.token
                        break
            elif child.name == "<type>":
                type_ast = self.visit(child)
        
        if not identifiers or not type_ast:
            return ASTNode("VarItem")
        
        var_item_node = ASTNode("VarItem")
        base_type = type_ast.data_type
        
        # KUNCI: Register setiap identifier ke symbol table
        for identifier in identifiers:
            # Check duplicate
            existing_idx = self.symbol_table.find_identifier(identifier)
            if existing_idx is not None:
                existing_entry = self.symbol_table.tab[existing_idx]
                if existing_entry["lev"] == self.symbol_table.level:
                    self.error(f"Duplicate identifier '{identifier}'", token_ref)
                    continue
            
            # REGISTER KE SYMBOL TABLE!
            var_idx = self.symbol_table.enter_identifier(
                identifier, ObjType.VARIABLE, base_type.value, size=1
            )
            
            # Buat VarDecl node
            var_decl = VarDeclNode(
                "Variable",
                identifier=identifier,
                token=token_ref,
                data_type=base_type,
                tab_index=var_idx,
                block_index=self.symbol_table.level
            )
            var_item_node.add_child(var_decl)
        
        return var_item_node

    def visit_type(self, node: ParseNode) -> ASTNode:
        """Visit type specification"""
        if not node.children:
            return ASTNode("Type", data_type=BaseType.VOID)
            
        first_child = node.children[0]
        name = self.clean_name(first_child.name)
        
        # Handle built-in types (via Token)
        if first_child.token:
            token_value = first_child.token.value.lower()
            type_map = {
                "integer": BaseType.INTEGER,
                "real": BaseType.REAL,
                "boolean": BaseType.BOOLEAN,
                "char": BaseType.CHAR,
                "string": BaseType.STRING
            }
            if token_value in type_map:
                return ASTNode("Type", data_type=type_map[token_value])
        
        # Handle array type
        if name == "array-type":
            return self.visit_array_type(first_child)
        
        return ASTNode("Type", data_type=BaseType.VOID)
    

    def visit_array_type(self, node: ParseNode) -> ASTNode:
        """Visit array type - FIXED to save array_ref"""
        index_spec = None
        element_type_node = None
        low_bound = 1
        high_bound = 10
        
        for child in node.children:
            if child.name == "<index-specification>":
                index_spec = child
                # Parse range
                range_result = self.parse_range(index_spec)
                if range_result:
                    low_bound, high_bound = range_result
            elif child.name == "<range>":  # Bisa langsung <range> juga
                range_result = self.parse_range(child)
                if range_result:
                    low_bound, high_bound = range_result
            elif child.name == "<type>":
                element_type_node = self.visit(child)
        
        if element_type_node:
            # Cek invalid bounds
            if low_bound > high_bound:
                self.error(f"Invalid array bounds: {low_bound}..{high_bound}", 
                        node.children[0].token if node.children else None)
            
            # Buat array table entry
            array_idx = self.symbol_table.enter_array(
                BaseType.INTEGER.value,  # index type
                element_type_node.data_type.value,  # element type
                low_bound,
                high_bound,
                1  # element size
            )
            
            # KUNCI: Simpan array_ref di node!
            array_node = ASTNode("ArrayType", data_type=BaseType.ARRAY, tab_index=array_idx)
            array_node.array_ref = array_idx  # ← INI PENTING!
            return array_node
        
        return ASTNode("ArrayType", data_type=BaseType.ARRAY)
    def visit_const_declaration(self, node: ParseNode) -> ASTNode:
        """Visit constant declaration"""
        ast_node = ASTNode("ConstDeclaration")
        
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "const-item":
                const_item_ast = self.visit(child)
                if const_item_ast:
                    ast_node.add_child(const_item_ast)
        
        return ast_node

    def visit_const_item(self, node: ParseNode) -> ASTNode:
        """Visit const item - FIXED VERSION"""
        identifier = None
        value_node = None
        const_value = None
        
        for child in node.children:
            if child.name == "IDENTIFIER" and child.token:
                identifier = child.token.value
            elif child.name == "<const-value>":
                value_node = self.visit(child)
                if hasattr(value_node, 'value'):
                    const_value = value_node.value
                elif value_node.children and hasattr(value_node.children[0], 'value'):
                    const_value = value_node.children[0].value
                
    
                if isinstance(const_value, str):
                    # Ini mungkin identifier constant
                    ref_idx = self.symbol_table.find_identifier(const_value)
                    if ref_idx is not None:
                        ref_entry = self.symbol_table.tab[ref_idx]
                        if ref_entry["obj"] == ObjType.CONSTANT:
                            const_value = self.symbol_table.get_constant_value(const_value)
        
        if identifier and value_node:
            if self.check_duplicate_identifier(identifier, node.children[0].token if node.children else None):
                const_node = ASTNode("ConstItem", 
                                token=node.children[0].token if node.children else None,
                                data_type=value_node.data_type, tab_index=-1)
                const_node.add_child(value_node)
                return const_node
            
            const_type = value_node.data_type
            
            const_idx = self.symbol_table.enter_identifier(
                identifier, ObjType.CONSTANT, const_type.value, const_value=const_value
            )
            
            const_node = ASTNode("ConstItem", 
                            token=node.children[0].token if node.children else None,
                            data_type=const_type, tab_index=const_idx)
            const_node.identifier = identifier  # ← Tambahkan ini
            const_node.add_child(value_node)
            return const_node
        
        return ASTNode("ConstItem")
    def visit_const_value(self, node: ParseNode) -> ASTNode:
        """Visit constant value"""
        if node.children:
            child = node.children[0]
            
            if child.token:
                token_type = child.token.type
                token_value = child.token.value
                
                # Number
                if token_type == TokenType.NUMBER:
                    if '.' in token_value:
                        data_type = BaseType.REAL
                        value = float(token_value)
                    else:
                        data_type = BaseType.INTEGER
                        value = int(token_value)
                    
                    ast_node = ASTNode("ConstValue", token=child.token, 
                                    data_type=data_type)
                    ast_node.value = value
                    return ast_node
                
                # String/Char
                elif token_type == TokenType.STRING_LITERAL:
                    # Detect char literal (length 3, single quotes)
                    if len(token_value) == 3 and token_value[0] == "'" and token_value[-1] == "'":
                        data_type = BaseType.CHAR
                        value = token_value[1]
                    else:
                        data_type = BaseType.STRING
                        value = token_value
                    
                    ast_node = ASTNode("ConstValue", token=child.token, 
                                    data_type=data_type)
                    ast_node.value = value
                    return ast_node
        
        return ASTNode("ConstValue", data_type=BaseType.VOID)
    
    # ========== Statements ==========
        
    def visit_compound_statement(self, node: ParseNode) -> ASTNode:
        """Visit compound statement (mulai...selesai)"""
        current_block = self.symbol_table.display[-1] if self.symbol_table.display else 0
        ast_node = ASTNode("CompoundStatement", block_index=current_block)
        
        for i, child in enumerate(node.children):
            name = self.clean_name(child.name)
            print(f"Child {i}: {child.name} (cleaned: {name})")
            
            if name == "statement-list":
                print(f"  → Visiting statement-list...")
                stmt_list = self.visit(child)
                for stmt in stmt_list.children:
                    print(f"    → Adding statement: {stmt.name if hasattr(stmt, 'name') else type(stmt)}")
                    ast_node.add_child(stmt)
        
        return ast_node
    def visit_statement_list(self, node: ParseNode) -> ASTNode:
        """Visit statement list - WITH DEBUG"""
        ast_node = ASTNode("StatementList")
        
        for i, child in enumerate(node.children):
            child_name = self.clean_name(child.name)
            print(f"Child {i}: {child.name} (cleaned: {child_name})")
            
            if child_name == "SEMICOLON" or child.name.startswith("SEMICOLON"):
                    continue
            # Dispatch ke method yang tepat
            if child_name == "assignment-statement":
                print(f"  → Calling visit_assignment_statement")
                stmt = self.visit_assignment_statement(child)
                print(f"  → Got: {type(stmt).__name__}, name={stmt.name if hasattr(stmt, 'name') else 'N/A'}")
                ast_node.add_child(stmt)
                
            elif child_name == "if-statement":
                stmt = self.visit_if_statement(child)
                ast_node.add_child(stmt)
                
            elif child_name == "while-statement":
                stmt = self.visit_while_statement(child)
                ast_node.add_child(stmt)
                
            elif child_name == "for-statement":
                stmt = self.visit_for_statement(child)
                ast_node.add_child(stmt)
                
            elif child_name == "compound-statement":
                stmt = self.visit_compound_statement(child)
                ast_node.add_child(stmt)
                
            elif child_name == "procedure-call" or child_name == "procedure/function-call":
                stmt = self.visit_procedure_call(child)
                ast_node.add_child(stmt)
                
            elif child_name == "SEMICOLON":
                print(f"  → Skipping SEMICOLON")
                continue
                
            else:
                print(f"  → FALLBACK: calling visit() for {child_name}")
                stmt = self.visit(child)
                print(f"  → Got: {type(stmt).__name__}, name={stmt.name if hasattr(stmt, 'name') else 'N/A'}")
                if stmt and stmt.name != "SEMICOLON":
                        ast_node.add_child(stmt)
                
        print(f"StatementList final children count: {len(ast_node.children)}")
        return ast_node
    # def visit_assignment_statement(self, node: ParseNode) -> ASTNode:
    #     if len(node.children) < 3:
    #         return AssignmentNode("Assignment", data_type=BaseType.VOID)
        
    #     # Children: [IDENTIFIER, ASSIGN_OPERATOR, <expression>]
    #     target_child = node.children[0]
    #     expr_child = node.children[2]
        
    #     # Parse target (IDENTIFIER langsung, bukan <variable>!)
    #     if target_child.name == "IDENTIFIER" and target_child.token:
    #         var_name = target_child.token.value
    #         var_idx = self.symbol_table.find_identifier(var_name)
            
    #         if var_idx is not None:
    #             var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
    #             target_node = VariableNode("Variable", identifier=var_name,
    #                                     token=target_child.token, data_type=var_type,
    #                                     tab_index=var_idx)
    #         else:
    #             self.error(f"Undefined variable '{var_name}'", target_child.token)
    #             target_node = VariableNode("Variable", identifier=var_name,
    #                                     token=target_child.token, data_type=BaseType.VOID)
    #     else:
    #         target_node = ASTNode("UnknownTarget")
        
    #     # Parse expression
    #     value_node = self.visit(expr_child)
        
    #     # Type checking
    #     if (target_node.data_type != BaseType.VOID and 
    #         value_node.data_type != BaseType.VOID):
    #         if not self.is_type_compatible(target_node.data_type, value_node.data_type):
    #             self.error(f"Type mismatch: cannot assign {value_node.data_type.name} to {target_node.data_type.name}")
        
    #     # Buat assignment node
    #     assign_node = AssignmentNode("Assignment", data_type=BaseType.VOID)
    #     assign_node.add_child(target_node)
    #     assign_node.add_child(value_node)
        
    #     if hasattr(target_node, 'identifier'):
    #         assign_node.identifier = target_node.identifier
        
    #     return assign_node
    def visit_assignment_statement(self, node: ParseNode) -> ASTNode:
        if len(node.children) < 3:
            print("  → ERROR: Not enough children!")
            return AssignmentNode("Assignment", data_type=BaseType.VOID)

        for i, child in enumerate(node.children):
            print(f"  Child {i}: {child.name}")

        target_child = node.children[0]
        assign_child = node.children[1]
        expr_child   = node.children[2]

        # --- TARGET: IDENTIFIER ---
        if target_child.name.startswith("IDENTIFIER") and target_child.token:
            var_name = target_child.token.value
            print(f"  → Target variable: {var_name}")
            var_idx = self.symbol_table.find_identifier(var_name)
            
            if var_idx is not None:
                var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
                print(f"  → Found in symbol table: idx={var_idx}, type={var_type}")
                target_node = VariableNode("Variable", identifier=var_name,
                                        token=target_child.token, data_type=var_type,
                                        tab_index=var_idx)
            else:
                print(f"  → ERROR: Variable not found!")
                self.error(f"Undefined variable '{var_name}'", target_child.token)
                target_node = VariableNode("Variable", identifier=var_name,
                                        token=target_child.token, data_type=BaseType.VOID)
        else:
            print(f"  → ERROR: Target is not IDENTIFIER!")
            target_node = ASTNode("UnknownTarget")

        # --- VALUE: Expression ---
        print(f"  → Visiting expression...")
        value_node = self.visit(expr_child)
        print(f"  → Expression result: {type(value_node).__name__}")

        if (hasattr(target_node, 'data_type') and target_node.data_type != BaseType.VOID and 
            value_node.data_type != BaseType.VOID):
            if not self.is_type_compatible(target_node.data_type, value_node.data_type):
                self.error(f"Type mismatch: cannot assign {value_node.data_type.name} to {target_node.data_type.name}")

        # --- Create Assignment Node ---
        assign_node = AssignmentNode("Assignment", data_type=BaseType.VOID)
        assign_node.add_child(target_node)
        assign_node.add_child(value_node)
        
        if hasattr(target_node, 'identifier'):
            assign_node.identifier = target_node.identifier

        print(f"  → Created AssignmentNode with {len(assign_node.children)} children")
        return assign_node
    def visit_expression(self, node: ParseNode) -> ASTNode:
        """Visit expression - FIXED VERSION"""
        
        if len(node.children) == 1:
            # ✅ Langsung return hasil dari simple-expression
            return self.visit_simple_expression(node.children[0])
        
        elif len(node.children) >= 3:
            # Binary relational expression (a > b, dll)
            left = self.visit_simple_expression(node.children[0])
            op_node = node.children[1]
            right = self.visit_simple_expression(node.children[2])
            
            op = op_node.token.value if op_node.token else ""
            
            bin_node = BinaryExpressionNode("RelationalExpression", 
                                        data_type=BaseType.BOOLEAN, operator=op)
            bin_node.add_child(left)
            bin_node.add_child(right)
            return bin_node  # ✅ Harus return node ini!
        
        else:
            return ASTNode("InvalidExpression", data_type=BaseType.VOID)

    def visit_simple_expression(self, node: ParseNode) -> ASTNode:
        children = [c for c in node.children if c.name != "<empty>"]
        if not children:
            return ASTNode("EmptySimpleExpr", data_type=BaseType.VOID)
        
        # Visit term pertama
        result = self.visit(children[0])
        
        i = 1
        while i < len(children):
            op_node = children[i]
            term_node = children[i+1]
            right = self.visit(term_node)
            
            op = op_node.token.value if hasattr(op_node, 'token') and op_node.token else ""
            
            if op in ['+', '-']:
                # Arithmetic: INTEGER atau REAL
                new_type = self.arithmetic_type_promotion(result.data_type, right.data_type)
                bin_node = BinaryExpressionNode("AdditiveExpression", 
                                            data_type=new_type, operator=op)
            elif op == 'atau':
                # Logical: BOOLEAN
                bin_node = BinaryExpressionNode("OrExpression", 
                                            data_type=BaseType.BOOLEAN, operator="atau")
            else:
                bin_node = ASTNode("UnknownOp", data_type=BaseType.VOID)
            
            bin_node.add_child(result)
            bin_node.add_child(right)
            result = bin_node
            i += 2
        
        return result
    def visit_term(self, node: ParseNode) -> ASTNode:
        children = [c for c in node.children if c.name != "<empty>"]
        if not children:
            return ASTNode("EmptyTerm", data_type=BaseType.VOID)
        
        # Visit factor pertama
        result = self.visit(children[0])
        
        i = 1
        while i < len(children):
            op_node = children[i]
            factor_node = children[i+1]
            right = self.visit(factor_node)
            
            op = op_node.token.value if hasattr(op_node, 'token') and op_node.token else ""
            
            # ✅ FIX: Set type sesuai operator!
            if op in ['*', '/', 'bagi', 'mod']:
                # Arithmetic: INTEGER atau REAL
                new_type = self.arithmetic_type_promotion(result.data_type, right.data_type)
                bin_node = BinaryExpressionNode("MultiplicativeExpression", 
                                            data_type=new_type, operator=op)
            elif op == 'dan':
                # Logical: BOOLEAN
                bin_node = BinaryExpressionNode("AndExpression", 
                                            data_type=BaseType.BOOLEAN, operator="dan")
            else:
                bin_node = ASTNode("UnknownOp", data_type=BaseType.VOID)
            
            bin_node.add_child(result)
            bin_node.add_child(right)
            result = bin_node
            i += 2
        
        return result
    def arithmetic_type_promotion(self, left_type: BaseType, right_type: BaseType) -> BaseType:
        """Type promotion untuk operasi aritmatika"""
        if left_type == BaseType.REAL or right_type == BaseType.REAL:
            return BaseType.REAL
        elif left_type == BaseType.INTEGER and right_type == BaseType.INTEGER:
            return BaseType.INTEGER
        else:
            return BaseType.VOID



    def visit_factor(self, node: ParseNode) -> ASTNode:
        first_child = node.children[0]
        
        # NUMBER
        if first_child.name.startswith("NUMBER"):
            val = int(first_child.token.value) if '.' not in first_child.token.value else float(first_child.token.value)
            return NumberNode("Number", data_type=BaseType.INTEGER if isinstance(val, int) else BaseType.REAL, value=val)
        
        # CHAR_LITERAL → 'a'
        elif first_child.name.startswith("CHAR_LITERAL") or first_child.name.startswith("STRING_LITERAL"):
            val = first_child.token.value.strip("'")
            return CharNode("Char", data_type=BaseType.CHAR, value=val)
        
        # IDENTIFIER → variabel biasa
        elif first_child.name.startswith("IDENTIFIER"):
            var_name = first_child.token.value
            var_idx = self.symbol_table.find_identifier(var_name)
            if var_idx is not None:
                var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
                return VariableNode("Variable", identifier=var_name, token=first_child.token,
                                data_type=var_type, tab_index=var_idx)
            else:
                self.error(f"Undefined variable '{var_name}'", first_child.token)
                return VariableNode("Variable", identifier=var_name, data_type=BaseType.VOID)
        
        # ( expression )
        elif first_child.name.startswith("LPARENTHESIS"):
            return self.visit(node.children[1])  # langsung visit expression di dalam kurung
        
        # tidak <factor>
        elif first_child.name.startswith("LOGICAL_OPERATOR") and first_child.token.value == "tidak":
            operand = self.visit(node.children[1])
            not_node = UnaryExpressionNode("NotExpression", data_type=BaseType.BOOLEAN, operator="tidak")
            not_node.add_child(operand)
            return not_node
        
        else:
            return ASTNode("UnknownFactor", data_type=BaseType.VOID)
    def visit_procedure_call(self, node: ParseNode) -> ASTNode:
        """Visit procedure call"""
        proc_name = ""
        
        # Attempt to find procedure name from children
        for child in node.children:
            if child.name.startswith("IDENTIFIER") and child.token:
                proc_name = child.token.value
                break
            elif child.name.startswith("KEYWORD") and child.token:
                if child.token.value.lower() in ['writeln', 'readln', 'write', 'read']:
                    proc_name = child.token.value
                    break
        
        proc_idx = self.symbol_table.find_identifier(proc_name)
        ast_node = ProcedureCallNode("ProcedureCall", data_type=BaseType.VOID, procedure_name=proc_name)
        
        if proc_idx is not None:
            ast_node.tab_index = proc_idx
        
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "parameter-list":
                param_ast = self.visit(child)
                for param_expr in param_ast.children:
                    ast_node.add_child(param_expr)
        
        return ast_node
    
    def visit_parameter_list(self, node: ParseNode) -> ASTNode:
        ast_node = ASTNode("ParameterList")
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "expression":
                ast_node.add_child(self.visit(child))
        return ast_node

    # ========== Helper Methods ==========
    def extract_identifiers(self, node: ParseNode) -> List[str]:
        """Extract identifiers dari identifier-list node - FIXED"""
        identifiers = []
        # print(f"DEBUG extract_identifiers: node.name={node.name}, children count={len(node.children)}")
        
        for child in node.children:
            # print(f"  child.name={child.name}, has_token={child.token is not None}")
            
            if child.token and child.token.type == TokenType.IDENTIFIER:
                identifiers.append(child.token.value)
                # print(f"    -> Found identifier: {child.token.value}")
            
            # (untuk handle kasus parser yang bikin name jadi "IDENTIFIER('value')")
            elif child.name.startswith("IDENTIFIER") and child.token:
                identifiers.append(child.token.value)
                # print(f"    -> Found identifier via name: {child.token.value}")
            
            elif child.name == "IDENTIFIER" and child.token:
                identifiers.append(child.token.value)
                # print(f"    -> Found identifier exact match: {child.token.value}")
        # print(f"  RESULT: identifiers={identifiers}")
        return identifiers        

    
    def get_operator_value(self, node: ParseNode) -> str:
        """Safely extract operator value from a node"""
        if node.token:
            return node.token.value
        if node.children and node.children[0].token:
            return node.children[0].token.value
        return ""

    def check_duplicate_identifier(self, name: str) -> bool:
        existing_idx = self.symbol_table.find_identifier(name)
        if existing_idx is not None:
            existing_entry = self.symbol_table.tab[existing_idx]
            if existing_entry["lev"] == self.symbol_table.level:
                self.error(f"Duplicate identifier '{name}'")
                return True
        return False
    
    def is_type_compatible(self, target_type: BaseType, source_type: BaseType) -> bool:
        if target_type == source_type:
            return True
        if target_type == BaseType.REAL and source_type == BaseType.INTEGER:
            return True
        if target_type == BaseType.VOID or source_type == BaseType.VOID:
            return True
        return False
    
    def get_expression_type(self, left_type: BaseType, right_type: BaseType, operator: str) -> BaseType:
        if left_type is None: left_type = BaseType.VOID
        if right_type is None: right_type = BaseType.VOID
        
        # Arithmetic
        if operator in ['+', '-', '*', '/', 'bagi', 'mod']:
            if left_type == BaseType.REAL or right_type == BaseType.REAL:
                return BaseType.REAL
            elif left_type == BaseType.INTEGER and right_type == BaseType.INTEGER:
                return BaseType.INTEGER
        
        # Relational & Logical
        elif operator in ['=', '<>', '<', '<=', '>', '>=', 'dan', 'atau', 'tidak']:
            return BaseType.BOOLEAN
            
        return BaseType.VOID
    
    def parse_range(self, node: ParseNode) -> Optional[Tuple[int, int]]:
        """Parse range specification untuk array"""
        # Node bisa berupa <range> atau langsung child-childnya
        target_node = node
        
        # Jika node ini adalah wrapper (misal index-specification), cari child <range>
        for child in node.children:
            if self.clean_name(child.name) == "range":
                target_node = child
                break
        
        values = []
        self._collect_numbers(target_node, values)
        
        if len(values) >= 2:
            return (values[0], values[-1])
            
        return None
        
    def _collect_numbers(self, node: ParseNode, numbers: List[int]):
        """Helper rekursif untuk mencari angka dalam range"""
        if node.name == "NUMBER" and node.token:
            try:
                numbers.append(int(node.token.value))
            except:
                pass
        for child in node.children:
            self._collect_numbers(child, numbers)
    
    def evaluate_constant_expression(self, node: ParseNode) -> Optional[int]:
        """Evaluate constant expression untuk array bounds"""
        vals = []
        self._collect_numbers(node, vals)
        if vals:
            return vals[0]
        return None
    def visit_if_statement(self, node: ParseNode) -> ASTNode:
        """Visit if-then-else statement"""
        condition_node = None
        then_node = None
        else_node = None
        
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "expression":
                condition_node = self.visit(child)
            elif name == "statement" or name == "compound-statement":
                if then_node is None:
                    then_node = self.visit(child)
                else:
                    else_node = self.visit(child)
        
        # Type check: condition harus boolean
        if condition_node and condition_node.data_type != BaseType.BOOLEAN:
            self.error(f"If condition must be boolean, got {condition_node.data_type.name}")
        
        ast_node = ASTNode("IfStatement", data_type=BaseType.VOID)
        if condition_node:
            ast_node.add_child(condition_node)
        if then_node:
            ast_node.add_child(then_node)
        if else_node:
            ast_node.add_child(else_node)
        
        return ast_node

    def visit_while_statement(self, node: ParseNode) -> ASTNode:
        """Visit while-do statement"""
        condition_node = None
        body_node = None
        
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "expression":
                condition_node = self.visit(child)
            elif name == "statement" or name == "compound-statement":
                body_node = self.visit(child)
        
        # Type check: condition harus boolean
        if condition_node and condition_node.data_type != BaseType.BOOLEAN:
            self.error(f"While condition must be boolean, got {condition_node.data_type.name}")
        
        ast_node = ASTNode("WhileStatement", data_type=BaseType.VOID)
        if condition_node:
            ast_node.add_child(condition_node)
        if body_node:
            ast_node.add_child(body_node)
        
        return ast_node

    def visit_for_statement(self, node: ParseNode) -> ASTNode:


        control_var = None
        start_expr = None
        end_expr = None
        body_node = None
        is_downto = False

        for child in node.children:
            name = self.clean_name(child.name)
            
            if name == "IDENTIFIER" and control_var is None:
                var_name = child.token.value
                var_idx = self.symbol_table.find_identifier(var_name)
                if var_idx is not None:
                    var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
                    control_var = VariableNode("Variable", identifier=var_name,
                                            token=child.token, data_type=var_type, 
                                            tab_index=var_idx)
                else:
                    self.error(f"Undefined variable '{var_name}'", child.token)
            
            elif name == "expression":
                if start_expr is None:
                    start_expr = self.visit(child)
                else:
                    end_expr = self.visit(child)
            
            elif child.token and child.token.value.lower() == "turunke":
                is_downto = True
            
            elif name in ["statement", "compound-statement"]:
                body_node = self.visit(child)
        
        # Type checking
        if control_var and control_var.data_type not in [BaseType.INTEGER, BaseType.CHAR]:
            self.error("For loop control variable must be integer or char")

        # INI YANG HARUS DIPERBAIKI: TAMBAHKAN control_var KE CHILD!
        for_node = ForStatementNode("ForStatement", data_type=BaseType.VOID)
        for_node.is_downto = is_downto
        
        if control_var: 
            for_node.add_child(control_var)   # INI YANG LUPA!
        if start_expr: 
            for_node.add_child(start_expr)
        if end_expr:   
            for_node.add_child(end_expr)
        if body_node:  
            for_node.add_child(body_node)
        
        return for_node
    def visit_repeat_statement(self, node: ParseNode) -> ASTNode:
        """Visit repeat-until statement"""
        body_nodes = []
        condition_node = None
        
        for child in node.children:
            name = self.clean_name(child.name)
            
            if name == "statement-list":
                stmt_list = self.visit(child)
                body_nodes = stmt_list.children
            elif name == "expression":
                condition_node = self.visit(child)
        
        # Type check: condition harus boolean
        if condition_node and condition_node.data_type != BaseType.BOOLEAN:
            self.error(f"Repeat-until condition must be boolean")
        
        ast_node = ASTNode("RepeatStatement", data_type=BaseType.VOID)
        for stmt in body_nodes:
            ast_node.add_child(stmt)
        if condition_node:
            ast_node.add_child(condition_node)
        
        return ast_node
    def visit_subprogram_declaration(self, node: ParseNode) -> ASTNode:
        """Visit subprogram declaration wrapper"""
        if node.children:
            return self.visit(node.children[0])
        return ASTNode("SubprogramDeclaration")

    def visit_procedure_declaration(self, node: ParseNode) -> ASTNode:
        """Visit procedure declaration"""
        proc_name = ""
        
        for child in node.children:
            if child.name == "IDENTIFIER" and child.token:
                proc_name = child.token.value
                break
        
        if not proc_name:
            return ASTNode("ProcedureDeclaration")
        
        # Check duplicate
        if self.check_duplicate_identifier(proc_name):
            return ASTNode("ProcedureDeclaration")
        
        # Enter procedure ke symbol table
        proc_idx = self.symbol_table.enter_identifier(
            proc_name, ObjType.PROCEDURE, BaseType.VOID.value
        )
        
        proc_node = ASTNode("ProcedureDeclaration", data_type=BaseType.VOID, 
                        tab_index=proc_idx)
        proc_node.procedure_name = proc_name
        
        # Enter procedure block
        proc_block_idx = self.symbol_table.enter_block()
        
        # Store block index
        if proc_idx < len(self.symbol_table.tab):
            self.symbol_table.tab[proc_idx]["block_index"] = proc_block_idx
        
        # Process parameters
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "formal-parameter-list":
                param_ast = self.visit(child)
                proc_node.add_child(param_ast)
        
        # Process body (block)
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "block":
                block_ast = self.visit(child)
                block_ast.block_index = proc_block_idx
                proc_node.add_child(block_ast)
        
        self.symbol_table.leave_block()
        
        return proc_node

    def visit_function_declaration(self, node: ParseNode) -> ASTNode:
        """Visit function declaration"""
        func_name = ""
        return_type = BaseType.VOID
        
        for child in node.children:
            name = self.clean_name(child.name)
            
            if child.name == "IDENTIFIER" and child.token:
                func_name = child.token.value
            elif name == "type":
                type_ast = self.visit(child)
                return_type = type_ast.data_type if type_ast.data_type else BaseType.VOID
        
        if not func_name:
            return ASTNode("FunctionDeclaration")
        
        if self.check_duplicate_identifier(func_name):
            return ASTNode("FunctionDeclaration")
        
        func_idx = self.symbol_table.enter_identifier(
            func_name, ObjType.FUNCTION, return_type.value
        )
        
        func_node = ASTNode("FunctionDeclaration", data_type=return_type, 
                        tab_index=func_idx)
        func_node.function_name = func_name
        
        func_block_idx = self.symbol_table.enter_block()
        
        if func_idx < len(self.symbol_table.tab):
            self.symbol_table.tab[func_idx]["block_index"] = func_block_idx
        
        # Process parameters and body
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "formal-parameter-list":
                param_ast = self.visit(child)
                func_node.add_child(param_ast)
            elif name == "block":
                block_ast = self.visit(child)
                block_ast.block_index = func_block_idx
                func_node.add_child(block_ast)
        
        self.symbol_table.leave_block()
        
        return func_node

    def visit_function_call(self, node: ParseNode) -> ASTNode:
        """Visit function call"""
        func_name = ""
        
        for child in node.children:
            if child.name == "IDENTIFIER" and child.token:
                func_name = child.token.value
                break
        
        if not func_name:
            return ASTNode("FunctionCall", data_type=BaseType.VOID)
        
        func_idx = self.symbol_table.find_identifier(func_name)
        return_type = BaseType.VOID
        
        if func_idx is not None:
            func_entry = self.symbol_table.tab[func_idx]
            if func_entry["obj"] == ObjType.FUNCTION:
                return_type = BaseType(func_entry["type"])
        
        ast_node = ASTNode("FunctionCall", data_type=return_type, 
                        tab_index=func_idx)
        ast_node.function_name = func_name
        
        # Process parameters
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "parameter-list":
                param_ast = self.visit(child)
                for param_expr in param_ast.children:
                    ast_node.add_child(param_expr)
        
        return ast_node