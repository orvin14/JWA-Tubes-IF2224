import json
import sys
from tokens import Token, TokenType

LOOKUP_TABLE = {
    "program": "KEYWORD", 
    "variabel": "KEYWORD", 
    "mulai": "KEYWORD", 
    "selesai": "KEYWORD",
    "kasus": "KEYWORD",
    "rekaman": "KEYWORD",
    "sampai": "KEYWORD",
    "jika": "KEYWORD", "maka": "KEYWORD", "selain_itu": "KEYWORD", "selama": "KEYWORD",
    "lakukan": "KEYWORD", "untuk": "KEYWORD", "ke": "KEYWORD", "turun_ke": "KEYWORD",
    "integer": "KEYWORD", "real": "KEYWORD", "boolean": "KEYWORD", "char": "KEYWORD",
    "larik": "KEYWORD", "dari": "KEYWORD", "prosedur": "KEYWORD", "fungsi": "KEYWORD",
    "konstanta": "KEYWORD", "tipe": "KEYWORD",
    "bagi": "ARITHMETIC_OPERATOR", "mod": "ARITHMETIC_OPERATOR",
    "dan": "LOGICAL_OPERATOR", "atau": "LOGICAL_OPERATOR", "tidak": "LOGICAL_OPERATOR"
}

class Lexer:
    def __init__(self, rules_file):
        """Memuat aturan DFA dari file JSON."""
        self.rules = self._load_rules(rules_file)
        self.start_state = self.rules['start_state']
        self.char_classes = self.rules['char_classes']
        self.states = self.rules['states']

    def _load_rules(self, rules_file):
        try:
            with open(rules_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File aturan '{rules_file}' tidak ditemukan.")
            sys.exit(1)

    def _find_next_state(self, current_state_name, char):
        state_info = self.states[current_state_name]
        
        for transition in state_info.get('transitions', []):
            if 'class' in transition:
                if char in self.char_classes[transition['class']]:
                    return transition['next_state']
            elif 'chars' in transition:
                if char in transition['chars']:
                    return transition['next_state']
            elif 'default' in transition:
                return transition['next_state']
        
        return None

    def tokenize(self, source_code):
        """
        Tokenize source code dan return list of Token objects.
        Returns: List[Token]
        """
        tokens = []
        current_pos = 0
        line = 1
        column = 1
        
        while current_pos < len(source_code):
            if source_code[current_pos] == '\n':
                line += 1
                column = 1
                current_pos += 1
                continue
                
            if source_code[current_pos] in self.char_classes['whitespace']:
                column += 1
                current_pos += 1
                continue

            current_state_name = self.start_state
            last_accepted_state = None
            last_accepted_pos = -1
            start_column = column

            temp_pos = current_pos
            while temp_pos < len(source_code):
                char = source_code[temp_pos]
                next_state_name = self._find_next_state(current_state_name, char)
                if next_state_name is None:
                    break
                
                current_state_name = next_state_name
                temp_pos += 1

                if self.states[current_state_name].get('is_final', False):
                    last_accepted_state = current_state_name
                    last_accepted_pos = temp_pos
            
            if last_accepted_state:
                token_type_str = self.states[last_accepted_state]['token_type']
                lexeme = source_code[current_pos:last_accepted_pos]

                # Handle comments
                if token_type_str == 'COMMENT':
                    comment_lexeme = source_code[current_pos:last_accepted_pos]
                    if comment_lexeme.startswith('{'):
                        tokens.append(Token(TokenType.COMMENT_START, '{', line, start_column))
                        tokens.append(Token(TokenType.COMMENT_END, '}', line, start_column))
                    elif comment_lexeme.startswith('(*'):
                        tokens.append(Token(TokenType.COMMENT_START, '(*', line, start_column))
                        tokens.append(Token(TokenType.COMMENT_END, '*)', line, start_column))
                    
                    column += len(lexeme)
                    current_pos = last_accepted_pos
                    continue
                
                # Map string to TokenType enum
                token_type_map = {
                    'KEYWORD': TokenType.KEYWORD,
                    'IDENTIFIER': TokenType.IDENTIFIER,
                    'NUMBER': TokenType.NUMBER,
                    'STRING_LITERAL': TokenType.STRING_LITERAL,
                    'CHAR_LITERAL': TokenType.CHAR_LITERAL,
                    'ARITHMETIC_OPERATOR': TokenType.ARITHMETIC_OPERATOR,
                    'RELATIONAL_OPERATOR': TokenType.RELATIONAL_OPERATOR,
                    'LOGICAL_OPERATOR': TokenType.LOGICAL_OPERATOR,
                    'ASSIGN_OPERATOR': TokenType.ASSIGN_OPERATOR,
                    'RANGE_OPERATOR': TokenType.RANGE_OPERATOR,
                    'SEMICOLON': TokenType.SEMICOLON,
                    'COLON': TokenType.COLON,
                    'COMMA': TokenType.COMMA,
                    'DOT': TokenType.DOT,
                    'LPARENTHESIS': TokenType.LPARENTHESIS,
                    'RPARENTHESIS': TokenType.RPARENTHESIS,
                    'LBRACKET': TokenType.LBRACKET,
                    'RBRACKET': TokenType.RBRACKET,
                }
                
                if token_type_str == 'IDENTIFIER':
                    keyword_type = LOOKUP_TABLE.get(lexeme.lower())
                    if keyword_type:
                        token_type_str = keyword_type
                
                token_type = token_type_map.get(token_type_str, TokenType.UNKNOWN)
                
  
                token = Token(token_type, lexeme, line, start_column)
                tokens.append(token)
                
                column += len(lexeme)
                current_pos = last_accepted_pos
            else:
                unknown_char = source_code[current_pos]
                print(f"Error: Karakter tidak dikenal -> '{unknown_char}' di posisi line {line}, column {column}")
                tokens.append(Token(TokenType.UNKNOWN, unknown_char, line, column))
                column += 1
                current_pos += 1
        

        tokens.append(Token(TokenType.EOF, '', line, column))
        return tokens