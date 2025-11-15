from node import Node
class Parser:
    def __init__(self, tokens):
        if not tokens:
            raise ValueError("Token list is empty! Cannot initialize parser.")
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.skip_comments()

    def skip_comments(self):
        # Melewatkan token COMMENT_START dan COMMENT_END
        while self.current_token and self.current_token[0] in ('COMMENT_START', 'COMMENT_END'):
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            else:
                self.current_token = None
                break

    def advance(self):
        # Maju ke token berikutnya
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
            self.skip_comments()
        else:
            self.current_token = None
            

    def peek(self):
        # Mengintip token berikutnya
        peek_pos = self.pos + 1
        while peek_pos < len(self.tokens):
            token = self.tokens[peek_pos]
            if token[0] not in ('COMMENT_START', 'COMMENT_END'):
                return token # Kembalikan token non-komentar pertama
            peek_pos += 1
        return None 

    def eat(self, token_type, token_value=None):
        # Memeriksa token, membuat node terminal, dan maju.
        if (self.current_token and 
            self.current_token[0] == token_type and
            (token_value is None or self.current_token[1].lower() == token_value)):
            
            token = self.current_token
            self.advance()
            
            node_name = f"{token[0]}({token[1]!r})"
            return Node(node_name, token)
        else:
            expected = f"{token_type} ('{token_value}')" if token_value else token_type
            found = f"{self.current_token[0]} ('{self.current_token[1]}')" if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected {expected} but got {found}")

    def parse(self):
        # Mulai proses parsing dari aturan top-level: <program>.
        root = self.parse_program()
        if self.current_token and self.current_token[0] != 'EOF':
            token_info = f"{self.current_token[0]} ('{self.current_token[1]}')"
            raise SyntaxError(f"Syntax Error: Unexpected token {token_info} after end of program.")
        root.print_tree()


    def parse_program(self):
        node = Node("program")
        node.add_child(self.parse_program_header())
        node.add_child(self.parse_declaration_part())
        node.add_child(self.parse_compound_statement())
        node.add_child(self.eat("DOT"))
        return node

    def parse_program_header(self):
        node = Node("program-header")
        node.add_child(self.eat("KEYWORD", "program"))
        node.add_child(self.eat("IDENTIFIER"))
        node.add_child(self.eat("SEMICOLON"))
        return node

    def parse_declaration_part(self):
        node = Node("declaration-part")
        if self.current_token and self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'variabel':
            node.add_child(self.parse_var_declaration())
        return node

    def parse_var_declaration(self):
        node = Node("var-declaration")
        node.add_child(self.eat("KEYWORD", "variabel"))
        
        while self.current_token and self.current_token[0] == 'IDENTIFIER':
            node.add_child(self.parse_identifier_list())
            node.add_child(self.eat("COLON"))
            node.add_child(self.parse_type())
            node.add_child(self.eat("SEMICOLON"))
        return node

    def parse_identifier_list(self):
        node = Node("identifier-list")
        node.add_child(self.eat("IDENTIFIER"))
        while self.current_token and self.current_token[0] == 'COMMA':
            node.add_child(self.eat("COMMA"))
            node.add_child(self.eat("IDENTIFIER"))
        return node

    def parse_type(self):
        node = Node("type")
        if self.current_token[0] == 'KEYWORD' and self.current_token[1] in ['integer', 'real', 'boolean', 'char']:
            node.add_child(self.eat("KEYWORD", self.current_token[1]))
        elif self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'larik':
            node.add_child(self.parse_array_type())
        else:
            token_info = f"{self.current_token[0]} ('{self.current_token[1]}')" if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected type specification (integer, real, larik, ...) but got {token_info}")
        return node

    def parse_array_type(self):
        node = Node("array-type")
        node.add_child(self.eat("KEYWORD", "larik"))
        node.add_child(self.eat("LBRACKET"))
        node.add_child(self.parse_range())
        node.add_child(self.eat("RBRACKET"))
        node.add_child(self.eat("KEYWORD", "dari"))
        node.add_child(self.parse_type())
        return node
    
    def parse_range(self):
        node = Node("range")
        node.add_child(self.parse_expression())
        node.add_child(self.eat("RANGE_OPERATOR"))
        node.add_child(self.parse_expression())
        return node

    def parse_compound_statement(self):
        node = Node("compound-statement")
        node.add_child(self.eat("KEYWORD", "mulai"))
        node.add_child(self.parse_statement_list())
        node.add_child(self.eat("KEYWORD", "selesai"))
        return node

    def parse_statement_list(self):
        node = Node("statement-list")
        
        if self.current_token and self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'selesai':
            return node 

        node.add_child(self.parse_statement()) 
        
        while self.current_token and self.current_token[0] == 'SEMICOLON':
            node.add_child(self.eat("SEMICOLON"))
            
            if self.current_token and self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'selesai':
                break
                
            node.add_child(self.parse_statement())
            
        return node

    def parse_statement(self):
        if not self.current_token or (self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'selesai'):
            return Node("empty-statement") 

        if self.current_token[0] == 'IDENTIFIER':
            next_token = self.peek() 
            
            if next_token and next_token[0] == 'ASSIGN_OPERATOR':
                return self.parse_assignment_statement()
            else:
                return self.parse_procedure_or_function_call()
                
        elif self.current_token[0] == 'KEYWORD':
            val = self.current_token[1]
            if val == 'jika':
                return self.parse_if_statement()
            elif val == 'selama':
                return self.parse_while_statement()
            elif val == 'untuk':
                return self.parse_for_statement()
            elif val == 'mulai':
                return self.parse_compound_statement()
            else:
                return Node("empty-statement")
        else:
            return Node("empty-statement")

    def parse_assignment_statement(self):
        node = Node("assignment-statement")
        node.add_child(self.eat("IDENTIFIER"))
        node.add_child(self.eat("ASSIGN_OPERATOR"))
        node.add_child(self.parse_expression())
        return node
    
    def parse_parameter_list(self):
        node = Node("parameter-list")
        node.add_child(self.parse_expression())
        while self.current_token and self.current_token[0] == 'COMMA':
            node.add_child(self.eat("COMMA"))
            node.add_child(self.parse_expression())
        return node

    def parse_if_statement(self):
        node = Node("if-statement")
        node.add_child(self.eat("KEYWORD", "jika"))
        node.add_child(self.parse_expression())
        node.add_child(self.eat("KEYWORD", "maka"))
        node.add_child(self.parse_statement())
        if self.current_token and self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'selain_itu':
            node.add_child(self.eat("KEYWORD", "selain_itu"))
            node.add_child(self.parse_statement())
        return node
    
    def parse_while_statement(self):
        node = Node("while-statement")
        node.add_child(self.eat("KEYWORD", "selama"))
        node.add_child(self.parse_expression())
        node.add_child(self.eat("KEYWORD", "lakukan"))
        node.add_child(self.parse_statement())
        return node
        
    def parse_for_statement(self):
        node = Node("for-statement")
        node.add_child(self.eat("KEYWORD", "untuk"))
        node.add_child(self.eat("IDENTIFIER"))
        node.add_child(self.eat("ASSIGN_OPERATOR"))
        node.add_child(self.parse_expression())
        
        if self.current_token and self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'ke':
            node.add_child(self.eat("KEYWORD", "ke"))
        elif self.current_token and self.current_token[0] == 'KEYWORD' and self.current_token[1] == 'turun_ke':
            node.add_child(self.eat("KEYWORD", "turun_ke"))
        else:
            raise SyntaxError("Syntax Error: Expected 'ke' or 'turun_ke' in for loop")
            
        node.add_child(self.parse_expression())
        node.add_child(self.eat("KEYWORD", "lakukan"))
        node.add_child(self.parse_statement())
        return node

    def parse_expression(self):
        node = Node("expression")
        node.add_child(self.parse_simple_expression())
        if self.current_token and self.current_token[0] == 'RELATIONAL_OPERATOR':
            rel_op_node = self.eat("RELATIONAL_OPERATOR")
            node.add_child(rel_op_node)
            node.add_child(self.parse_simple_expression())
        return node

    def parse_simple_expression(self):
        node = Node("simple-expression")
        
        if self.current_token and self.current_token[0] == 'ARITHMETIC_OPERATOR' and self.current_token[1] in ['+', '-']:
            node.add_child(self.eat("ARITHMETIC_OPERATOR", self.current_token[1]))
            
        node.add_child(self.parse_term())
        
        while (self.current_token and 
               ( (self.current_token[0] == 'ARITHMETIC_OPERATOR' and self.current_token[1] in ['+', '-']) or 
                 (self.current_token[0] == 'LOGICAL_OPERATOR' and self.current_token[1] == 'atau') ) ):
            if self.current_token[1] == 'atau':
                node.add_child(self.eat("LOGICAL_OPERATOR", "atau"))
            else:
                node.add_child(self.eat("ARITHMETIC_OPERATOR", self.current_token[1]))
            node.add_child(self.parse_term())
        return node

    def parse_term(self):
        node = Node("term")
        node.add_child(self.parse_factor())
        
        while (self.current_token and
               ( (self.current_token[0] == 'ARITHMETIC_OPERATOR' and self.current_token[1] in ['*', '/', 'bagi', 'mod']) or
                 (self.current_token[0] == 'LOGICAL_OPERATOR' and self.current_token[1] == 'dan') ) ):
            
            if self.current_token[1] in ['*', '/']:
                node.add_child(self.eat("ARITHMETIC_OPERATOR", self.current_token[1]))
            elif self.current_token[1] in ['bagi', 'mod']:
                 node.add_child(self.eat("ARITHMETIC_OPERATOR", self.current_token[1]))
            elif self.current_token[1] == 'dan':
                 node.add_child(self.eat("LOGICAL_OPERATOR", "dan"))
                 
            node.add_child(self.parse_factor())
        return node

    def parse_factor(self):
        node = Node("factor")
        
        if not self.current_token:
            raise SyntaxError("Syntax Error: Unexpected EOF, expected a factor")

        if self.current_token[0] == 'IDENTIFIER':
            next_token = self.peek()
            
            if next_token and next_token[0] == 'LPARENTHESIS':
                return self.parse_procedure_or_function_call()
            else:
                node.add_child(self.eat("IDENTIFIER"))
        elif self.current_token[0] == 'NUMBER':
            node.add_child(self.eat("NUMBER"))
        elif self.current_token[0] == 'CHAR_LITERAL':
            node.add_child(self.eat("CHAR_LITERAL"))
        elif self.current_token[0] == 'STRING_LITERAL':
            node.add_child(self.eat("STRING_LITERAL"))
        elif self.current_token[0] == 'LPARENTHESIS':
            node.add_child(self.eat("LPARENTHESIS"))
            node.add_child(self.parse_expression()) 
            node.add_child(self.eat("RPARENTHESIS"))
        elif self.current_token[0] == 'LOGICAL_OPERATOR' and self.current_token[1] == 'tidak':
            node.add_child(self.eat("LOGICAL_OPERATOR", "tidak"))
            node.add_child(self.parse_factor()) 
        else:
            token_info = f"{self.current_token[0]} ('{self.current_token[1]}')" if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected factor (ID, Number, '(', 'tidak', ...) but got {token_info}")
        return node
        
    def parse_procedure_or_function_call(self):
        node = Node("procedure/function-call") 
        
        if self.current_token[0] == 'IDENTIFIER':
            node.add_child(self.eat("IDENTIFIER"))
        else:
            raise SyntaxError(f"Syntax Error: Expected procedure or function name but got {self.current_token[0]}")

        node.add_child(self.eat("LPARENTHESIS"))
        if self.current_token and self.current_token[0] != 'RPARENTHESIS':
            node.add_child(self.parse_parameter_list())    
        node.add_child(self.eat("RPARENTHESIS"))
        return node