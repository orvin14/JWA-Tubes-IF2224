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
        
        # Start dengan global scope - block 0
        global_block_idx = self.symbol_table.enter_block()
        
        # Build AST dan perform semantic analysis
        self.current_ast = self.visit(parse_tree)
        
        # Leave global scope
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
        # Bersihkan nama node agar cocok dengan method
        clean_node_name = self.clean_name(node.name).replace("-", "_")
        method_name = f'visit_{clean_node_name}'
        
        # Cari method yang sesuai, jika tidak ada pakai visit_default
        method = getattr(self, method_name, self.visit_default)
        
        try:
            return method(node)
        except Exception as e:
            # Fallback mechanism agar tidak crash total jika struktur tree aneh
            # print(f"DEBUG: Error in {method_name}: {e}") # Uncomment untuk debug
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
    
    # ========== Program ==========
    
    def visit_program(self, node: ParseNode) -> ASTNode:
        """Visit program node"""
        program_name = "Unknown"
        header_node = None
        token_ref = None

        # Cari program-header secara fleksibel (dengan atau tanpa bracket)
        for child in node.children:
            if "program-header" in self.clean_name(child.name):
                header_node = child
                break
        
        if header_node:
            # Struktur: KEYWORD('program') -> IDENTIFIER -> SEMICOLON
            # Kita cari child yang merupakan IDENTIFIER
            for h_child in header_node.children:
                if h_child.name == "IDENTIFIER" and h_child.token:
                    program_name = h_child.token.value
                    token_ref = h_child.token
                    break
        
        # Enter program ke symbol table
        program_idx = self.symbol_table.enter_identifier(
            program_name, ObjType.PROGRAM, BaseType.VOID.value
        )
        
        # Create program node
        ast_node = ProgramNode(
            "Program", 
            name=program_name,
            token=token_ref,
            data_type=BaseType.VOID, 
            tab_index=program_idx
        )
        
        # Process children (Declarations & Compound Statement)
        for child in node.children:
            name = self.clean_name(child.name)
            
            if name == "declaration-part":
                decl_ast = self.visit(child)
                ast_node.add_child(decl_ast)
            elif name == "compound-statement":
                # Enter main block
                main_block_idx = self.symbol_table.enter_block()
                compound_ast = self.visit(child)
                compound_ast.block_index = main_block_idx
                ast_node.add_child(compound_ast)
                self.symbol_table.leave_block()
        
        return ast_node
    
    # ========== Declarations ==========
    
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
    
    def visit_var_declaration(self, node: ParseNode) -> ASTNode:
        """Visit variable declaration"""
        ast_node = ASTNode("VarDeclaration")
        
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "var-item":
                var_item_ast = self.visit(child)
                for var_decl in var_item_ast.children:
                    ast_node.add_child(var_decl)
        
        return ast_node
    
    def visit_var_item(self, node: ParseNode) -> ASTNode:
        """Visit var item (identifier list + type)"""
        identifiers = []
        type_ast = None
        
        # Extract identifiers dan type
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "identifier-list":
                identifiers = self.extract_identifiers(child)
            elif name == "type":
                type_ast = self.visit(child)
        
        var_ast = ASTNode("VarItem")
        
        if identifiers and type_ast:
            base_type = type_ast.data_type
            
            # Masukkan setiap identifier ke symbol table
            for identifier in identifiers:
                # Check duplicate
                if not self.check_duplicate_identifier(identifier):
                    var_idx = self.symbol_table.enter_identifier(
                        identifier, ObjType.VARIABLE, base_type.value, size=1
                    )
                    
                    # Create VarDeclNode
                    ident_ast = VarDeclNode(
                        "Variable", 
                        identifier=identifier,
                        token=Token(TokenType.IDENTIFIER, identifier, 0, 0),
                        data_type=base_type, 
                        tab_index=var_idx, 
                        block_index=0
                    )
                    var_ast.add_child(ident_ast)
        
        return var_ast
    
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
        """Visit array type"""
        element_type_node = None
        low_bound = 1
        high_bound = 10
        
        for child in node.children:
            name = self.clean_name(child.name)
            
            if name in ["range", "index-specification"]:
                range_result = self.parse_range(child)
                if range_result:
                    low_bound, high_bound = range_result
            elif name == "type":
                element_type_node = self.visit(child)
        
        if element_type_node:
            # Create array table entry
            array_idx = self.symbol_table.enter_array(
                BaseType.INTEGER.value,
                element_type_node.data_type.value,
                low_bound,
                high_bound,
                1
            )
            return ASTNode("ArrayType", data_type=BaseType.ARRAY, tab_index=array_idx)
        
        return ASTNode("ArrayType", data_type=BaseType.ARRAY)
    
    # ========== Statements ==========
    
    def visit_compound_statement(self, node: ParseNode) -> ASTNode:
        """Visit compound statement (mulai...selesai)"""
        current_block = self.symbol_table.display[-1] if self.symbol_table.display else 0
        ast_node = ASTNode("CompoundStatement", block_index=current_block)
        
        for child in node.children:
            name = self.clean_name(child.name)
            if name == "statement-list":
                stmt_list = self.visit(child)
                for stmt in stmt_list.children:
                    ast_node.add_child(stmt)
        
        return ast_node
    
    def visit_statement_list(self, node: ParseNode) -> ASTNode:
        """Visit statement list"""
        ast_node = ASTNode("StatementList")
        
        for child in node.children:
            name = self.clean_name(child.name)
            # Daftar node yang dianggap statement
            if name in ["statement", "assignment-statement", "procedure-call", "compound-statement", 
                        "if-statement", "while-statement", "for-statement", "repeat-statement"]:
                stmt_ast = self.visit(child)
                if stmt_ast:
                    ast_node.add_child(stmt_ast)
        
        return ast_node
    
    def visit_statement(self, node: ParseNode) -> ASTNode:
        """Visit statement wrapper"""
        if node.children:
            return self.visit(node.children[0])
        return ASTNode("Statement", data_type=BaseType.VOID)
    
    def visit_assignment_statement(self, node: ParseNode) -> ASTNode:
        """Visit assignment statement"""
        target_node = None
        value_node = None
        
        for i, child in enumerate(node.children):
            name = self.clean_name(child.name)
            
            if name == "IDENTIFIER" and i == 0:
                # Target Variable
                var_name = child.token.value
                var_idx = self.symbol_table.find_identifier(var_name)
                
                if var_idx is not None:
                    var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
                    target_node = VariableNode(
                        "Variable", 
                        identifier=var_name,
                        token=child.token,
                        data_type=var_type, 
                        tab_index=var_idx
                    )
                else:
                    self.error(f"Undefined variable '{var_name}'", child.token)
                    target_node = VariableNode(
                        "Variable",
                        identifier=var_name,
                        token=child.token,
                        data_type=BaseType.VOID
                    )
            elif name == "expression":
                # Value Expression
                value_node = self.visit(child)
        
        # Type checking
        if target_node and value_node:
            if target_node.data_type and value_node.data_type:
                if not self.is_type_compatible(target_node.data_type, value_node.data_type):
                    self.error(
                        f"Type mismatch: cannot assign {value_node.data_type.name} "
                        f"to {target_node.data_type.name}"
                    )
        
        # Create assignment node
        ast_node = AssignmentNode("Assignment", data_type=BaseType.VOID)
        if target_node:
            ast_node.add_child(target_node)
        if value_node:
            ast_node.add_child(value_node)
        
        return ast_node
    
    # ========== Expressions ==========
    
    def visit_expression(self, node: ParseNode) -> ASTNode:
        """Visit expression"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
        else:
            # Binary expression dengan relational operator
            left_expr = self.visit(node.children[0])
            
            if len(node.children) < 3:
                return left_expr
                
            operator_node = node.children[1]
            right_expr = self.visit(node.children[2])
            
            # Extract operator value
            operator_value = self.get_operator_value(operator_node)
            
            # Determine result type
            result_type = self.get_expression_type(
                left_expr.data_type, 
                right_expr.data_type, 
                operator_value
            )
            
            ast_node = BinaryExpressionNode(
                "BinaryExpression",
                data_type=result_type,
                operator=operator_value
            )
            ast_node.add_child(left_expr)
            ast_node.add_child(right_expr)
            return ast_node
    
    def visit_simple_expression(self, node: ParseNode) -> ASTNode:
        """Visit simple expression"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
        
        # Handle multiple terms dengan additive operators
        result_node = self.visit(node.children[0])
        
        i = 1
        while i < len(node.children) - 1:
            operator_node = node.children[i]
            right_term = self.visit(node.children[i + 1])
            
            operator_value = self.get_operator_value(operator_node)
            
            result_type = self.get_expression_type(
                result_node.data_type,
                right_term.data_type,
                operator_value
            )
            
            new_result = BinaryExpressionNode(
                "BinaryExpression",
                data_type=result_type,
                operator=operator_value
            )
            new_result.add_child(result_node)
            new_result.add_child(right_term)
            result_node = new_result
            i += 2
        
        return result_node
    
    def visit_term(self, node: ParseNode) -> ASTNode:
        """Visit term"""
        if len(node.children) == 1:
            return self.visit(node.children[0])
        
        result_node = self.visit(node.children[0])
        
        i = 1
        while i < len(node.children) - 1:
            operator_node = node.children[i]
            right_factor = self.visit(node.children[i + 1])
            
            operator_value = self.get_operator_value(operator_node)
            
            result_type = self.get_expression_type(
                result_node.data_type,
                right_factor.data_type,
                operator_value
            )
            
            new_result = BinaryExpressionNode(
                "BinaryExpression",
                data_type=result_type,
                operator=operator_value
            )
            new_result.add_child(result_node)
            new_result.add_child(right_factor)
            result_node = new_result
            i += 2
        
        return result_node
    
    def visit_factor(self, node: ParseNode) -> ASTNode:
        """Visit factor"""
        if not node.children:
            return ASTNode("Factor", data_type=BaseType.VOID)
        
        first_child = node.children[0]
        name = self.clean_name(first_child.name)
        
        # Number literal
        if name == "NUMBER" and first_child.token:
            value_str = first_child.token.value
            if '.' in value_str:
                return NumberNode("Number", token=first_child.token, data_type=BaseType.REAL, value=float(value_str))
            else:
                return NumberNode("Number", token=first_child.token, data_type=BaseType.INTEGER, value=int(value_str))
        
        # String literal
        elif name == "STRING_LITERAL" and first_child.token:
            return StringNode("String", token=first_child.token, data_type=BaseType.STRING, value=first_child.token.value)
        
        # Identifier (variable)
        elif name == "IDENTIFIER" and first_child.token:
            var_name = first_child.token.value
            var_idx = self.symbol_table.find_identifier(var_name)
            
            if var_idx is not None:
                var_type = BaseType(self.symbol_table.tab[var_idx]["type"])
                return VariableNode(
                    "Variable", token=first_child.token, data_type=var_type, 
                    tab_index=var_idx, identifier=var_name
                )
            else:
                self.error(f"Undefined identifier '{var_name}'", first_child.token)
                return VariableNode("Variable", token=first_child.token, data_type=BaseType.VOID, identifier=var_name)
        
        # Parenthesized expression
        elif name == "LPARENTHESIS":
            if len(node.children) > 1:
                return self.visit(node.children[1])
                
        # Handle Logical NOT / Unary operators if any
        elif name == "LOGICAL_OPERATOR" or name == "factor": 
             if len(node.children) > 0:
                 # Recursively visit (simplified)
                 return self.visit(node.children[-1])

        return ASTNode("Factor", data_type=BaseType.VOID)
    
    def visit_procedure_call(self, node: ParseNode) -> ASTNode:
        """Visit procedure call"""
        proc_name = ""
        
        # Attempt to find procedure name from children
        for child in node.children:
            if child.name == "IDENTIFIER" and child.token:
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
        identifiers = []
        for child in node.children:
            if child.name == "IDENTIFIER" and child.token:
                identifiers.append(child.token.value)
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
        
        # Sekarang extract dari range
        # Structure: expression .. expression
        # Karena expression complex, kita pakai helper recursive
        
        # Kita kumpulkan semua angka yang ada di subtree ini
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