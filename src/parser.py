from typing import List, Optional
from tokens import Token, TokenType
from node import ParseNode

class Parser:
    def __init__(self, tokens: List[Token]):  
        if not tokens:
            raise ValueError("Token list is empty! Cannot initialize parser.")
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.skip_comments()

    def skip_comments(self):
        while self.current_token and self.current_token.type in (TokenType.COMMENT_START, TokenType.COMMENT_END):
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            else:
                self.current_token = None
                break

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
            self.skip_comments()
        else:
            self.current_token = None

    def peek(self):
        peek_pos = self.pos + 1
        while peek_pos < len(self.tokens):
            token = self.tokens[peek_pos]
            if token.type not in (TokenType.COMMENT_START, TokenType.COMMENT_END):
                return token
            peek_pos += 1
        return None

    def eat(self, token_type: TokenType, token_value=None):
        """
        Memeriksa token, membuat ParseNode terminal, dan maju.
        """
        if (self.current_token and 
            self.current_token.type == token_type and
            (token_value is None or self.current_token.value.lower() == token_value)):
            
            token = self.current_token
            self.advance()
            
            # Return ParseNode langsung
            node_name = f"{token.type.name}({token.value!r})"
            return ParseNode(node_name, token)
        else:
            expected = f"{token_type.name} ('{token_value}')" if token_value else token_type.name
            found = f"{self.current_token.type.name} ('{self.current_token.value}')" if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected {expected} but got {found}")

    def parse(self):
        root = self.parse_program()
        if self.current_token and self.current_token.type != TokenType.EOF:
            token_info = f"{self.current_token.type.name} ('{self.current_token.value}')"
            raise SyntaxError(f"Syntax Error: Unexpected token {token_info} after end of program.")
        root.print_tree()
        return root

    def parse_program(self):
        node = ParseNode("<program>")
        node.add_child(self.parse_program_header())
        node.add_child(self.parse_declaration_part())
        node.add_child(self.parse_compound_statement())
        node.add_child(self.eat(TokenType.DOT))
        return node

    def parse_program_header(self):
        node = ParseNode("<program-header>")
        node.add_child(self.eat(TokenType.KEYWORD, "program"))
        node.add_child(self.eat(TokenType.IDENTIFIER))
        node.add_child(self.eat(TokenType.SEMICOLON))
        return node

    def parse_var_declaration(self):
        node = ParseNode("<var-declaration>")
        node.add_child(self.eat(TokenType.KEYWORD, "variabel"))
        
        # PERUBAHAN: Gunakan parse_var_item() dalam loop
        while (self.current_token and 
            self.current_token.type == TokenType.IDENTIFIER):
            node.add_child(self.parse_var_item())  # ← BARU!
        
        return node
    
    def parse_declaration_part(self):
        node = ParseNode("<declaration-part>")
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'variabel':
            node.add_child(self.parse_var_declaration())
        return node
    
    def parse_var_item(self):
        """Parse satu kelompok deklarasi variabel"""
        node = ParseNode("<var-item>")
        node.add_child(self.parse_identifier_list())
        node.add_child(self.eat(TokenType.COLON))
        node.add_child(self.parse_type())
        node.add_child(self.eat(TokenType.SEMICOLON))
        return node
    
    def parse_identifier_list(self):
        node = ParseNode("<identifier-list>")
        node.add_child(self.eat(TokenType.IDENTIFIER))
        while self.current_token and self.current_token.type == TokenType.COMMA:
            node.add_child(self.eat(TokenType.COMMA))
            node.add_child(self.eat(TokenType.IDENTIFIER))
        return node

    def parse_type(self):
        node = ParseNode("<type>")
        if self.current_token.type == TokenType.KEYWORD and self.current_token.value in ['integer', 'real', 'boolean', 'char']:
            node.add_child(self.eat(TokenType.KEYWORD, self.current_token.value))
        elif self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'larik':
            node.add_child(self.parse_array_type())
        else:
            token_info = f"{self.current_token.type.name} ('{self.current_token.value}')" if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected type specification but got {token_info}")
        return node

    def parse_array_type(self):
        node = ParseNode("<array-type>")
        node.add_child(self.eat(TokenType.KEYWORD, "larik"))
        node.add_child(self.eat(TokenType.LBRACKET))
        node.add_child(self.parse_range())
        node.add_child(self.eat(TokenType.RBRACKET))
        node.add_child(self.eat(TokenType.KEYWORD, "dari"))
        node.add_child(self.parse_type())
        return node
    
    def parse_range(self):
        node = ParseNode("<range>")
        node.add_child(self.parse_expression())
        node.add_child(self.eat(TokenType.RANGE_OPERATOR))
        node.add_child(self.parse_expression())
        return node

    def parse_compound_statement(self):
        node = ParseNode("<compound-statement>")
        node.add_child(self.eat(TokenType.KEYWORD, "mulai"))
        node.add_child(self.parse_statement_list())
        node.add_child(self.eat(TokenType.KEYWORD, "selesai"))
        return node

    def parse_statement_list(self):
        node = ParseNode("<statement-list>")
        
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'selesai':
            return node

        node.add_child(self.parse_statement())
        
        while self.current_token and self.current_token.type == TokenType.SEMICOLON:
            node.add_child(self.eat(TokenType.SEMICOLON))
            
            if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'selesai':
                break
                
            node.add_child(self.parse_statement())
            
        return node

    def parse_statement(self):
        if not self.current_token or (self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'selesai'):
            return ParseNode("<empty-statement>")

        if self.current_token.type == TokenType.IDENTIFIER:
            next_token = self.peek()
            
            if next_token and next_token.type == TokenType.ASSIGN_OPERATOR:
                return self.parse_assignment_statement()
            else:
                return self.parse_procedure_or_function_call()
                
        elif self.current_token.type == TokenType.KEYWORD:
            val = self.current_token.value
            if val == 'jika':
                return self.parse_if_statement()
            elif val == 'selama':
                return self.parse_while_statement()
            elif val == 'untuk':
                return self.parse_for_statement()
            elif val == 'mulai':
                return self.parse_compound_statement()
            else:
                return ParseNode("<empty-statement>")
        else:
            return ParseNode("<empty-statement>")

    def parse_assignment_statement(self):
        node = ParseNode("<assignment-statement>")
        node.add_child(self.eat(TokenType.IDENTIFIER))
        node.add_child(self.eat(TokenType.ASSIGN_OPERATOR))
        node.add_child(self.parse_expression())
        return node
    
    def parse_parameter_list(self):
        node = ParseNode("<parameter-list>")
        node.add_child(self.parse_expression())
        while self.current_token and self.current_token.type == TokenType.COMMA:
            node.add_child(self.eat(TokenType.COMMA))
            node.add_child(self.parse_expression())
        return node

    def parse_if_statement(self):
        node = ParseNode("<if-statement>")
        node.add_child(self.eat(TokenType.KEYWORD, "jika"))
        node.add_child(self.parse_expression())
        node.add_child(self.eat(TokenType.KEYWORD, "maka"))
        node.add_child(self.parse_statement())
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'selain_itu':
            node.add_child(self.eat(TokenType.KEYWORD, "selain_itu"))
            node.add_child(self.parse_statement())
        return node
    
    def parse_while_statement(self):
        node = ParseNode("<while-statement>")
        node.add_child(self.eat(TokenType.KEYWORD, "selama"))
        node.add_child(self.parse_expression())
        node.add_child(self.eat(TokenType.KEYWORD, "lakukan"))
        node.add_child(self.parse_statement())
        return node
        
    def parse_for_statement(self):
        node = ParseNode("<for-statement>")
        node.add_child(self.eat(TokenType.KEYWORD, "untuk"))
        node.add_child(self.eat(TokenType.IDENTIFIER))
        node.add_child(self.eat(TokenType.ASSIGN_OPERATOR))
        node.add_child(self.parse_expression())
        
        if self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'ke':
            node.add_child(self.eat(TokenType.KEYWORD, "ke"))
        elif self.current_token and self.current_token.type == TokenType.KEYWORD and self.current_token.value == 'turun_ke':
            node.add_child(self.eat(TokenType.KEYWORD, "turun_ke"))
        else:
            raise SyntaxError("Syntax Error: Expected 'ke' or 'turun_ke' in for loop")
            
        node.add_child(self.parse_expression())
        node.add_child(self.eat(TokenType.KEYWORD, "lakukan"))
        node.add_child(self.parse_statement())
        return node

    def parse_expression(self):
        node = ParseNode("<expression>")
        node.add_child(self.parse_simple_expression())
        if self.current_token and self.current_token.type == TokenType.RELATIONAL_OPERATOR:
            rel_op_node = self.eat(TokenType.RELATIONAL_OPERATOR)
            node.add_child(rel_op_node)
            node.add_child(self.parse_simple_expression())
        return node

    def parse_simple_expression(self):
        node = ParseNode("<simple-expression>")
        
        if self.current_token and self.current_token.type == TokenType.ARITHMETIC_OPERATOR and self.current_token.value in ['+', '-']:
            node.add_child(self.eat(TokenType.ARITHMETIC_OPERATOR, self.current_token.value))
            
        node.add_child(self.parse_term())
        
        while (self.current_token and 
               ((self.current_token.type == TokenType.ARITHMETIC_OPERATOR and self.current_token.value in ['+', '-']) or 
                (self.current_token.type == TokenType.LOGICAL_OPERATOR and self.current_token.value == 'atau'))):
            if self.current_token.value == 'atau':
                node.add_child(self.eat(TokenType.LOGICAL_OPERATOR, "atau"))
            else:
                node.add_child(self.eat(TokenType.ARITHMETIC_OPERATOR, self.current_token.value))
            node.add_child(self.parse_term())
        return node

    def parse_term(self):
        node = ParseNode("<term>")
        node.add_child(self.parse_factor())
        
        while (self.current_token and
               ((self.current_token.type == TokenType.ARITHMETIC_OPERATOR and self.current_token.value in ['*', '/', 'bagi', 'mod']) or
                (self.current_token.type == TokenType.LOGICAL_OPERATOR and self.current_token.value == 'dan'))):
            
            if self.current_token.value in ['*', '/']:
                node.add_child(self.eat(TokenType.ARITHMETIC_OPERATOR, self.current_token.value))
            elif self.current_token.value in ['bagi', 'mod']:
                 node.add_child(self.eat(TokenType.ARITHMETIC_OPERATOR, self.current_token.value))
            elif self.current_token.value == 'dan':
                 node.add_child(self.eat(TokenType.LOGICAL_OPERATOR, "dan"))
                 
            node.add_child(self.parse_factor())
        return node

    def parse_factor(self):
        node = ParseNode("<factor>")
        
        if not self.current_token:
            raise SyntaxError("Syntax Error: Unexpected EOF, expected a factor")

        if self.current_token.type == TokenType.IDENTIFIER:
            next_token = self.peek()
            
            if next_token and next_token.type == TokenType.LPARENTHESIS:
                return self.parse_procedure_or_function_call()
            else:
                node.add_child(self.eat(TokenType.IDENTIFIER))
        elif self.current_token.type == TokenType.NUMBER:
            node.add_child(self.eat(TokenType.NUMBER))
        elif self.current_token.type == TokenType.CHAR_LITERAL:
            node.add_child(self.eat(TokenType.CHAR_LITERAL))
        elif self.current_token.type == TokenType.STRING_LITERAL:
            node.add_child(self.eat(TokenType.STRING_LITERAL))
        elif self.current_token.type == TokenType.LPARENTHESIS:
            node.add_child(self.eat(TokenType.LPARENTHESIS))
            node.add_child(self.parse_expression())
            node.add_child(self.eat(TokenType.RPARENTHESIS))
        elif self.current_token.type == TokenType.LOGICAL_OPERATOR and self.current_token.value == 'tidak':
            node.add_child(self.eat(TokenType.LOGICAL_OPERATOR, "tidak"))
            node.add_child(self.parse_factor())
        else:
            token_info = f"{self.current_token.type.name} ('{self.current_token.value}')" if self.current_token else "EOF"
            raise SyntaxError(f"Syntax Error: Expected factor but got {token_info}")
        return node
        
    def parse_procedure_or_function_call(self):
        node = ParseNode("procedure/function-call")
        
        if self.current_token.type == TokenType.IDENTIFIER:
            node.add_child(self.eat(TokenType.IDENTIFIER))
        else:
            raise SyntaxError(f"Syntax Error: Expected procedure or function name")

        node.add_child(self.eat(TokenType.LPARENTHESIS))
        if self.current_token and self.current_token.type != TokenType.RPARENTHESIS:
            node.add_child(self.parse_parameter_list())
        node.add_child(self.eat(TokenType.RPARENTHESIS))
        return node