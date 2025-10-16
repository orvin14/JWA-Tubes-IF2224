import json
import sys

LOOKUP_TABLE = {
    "program": "KEYWORD", 
    "var": "KEYWORD", 
    "begin": "KEYWORD", 
    "end": "KEYWORD",
    "if": "KEYWORD", "then": "KEYWORD", "else": "KEYWORD", "while": "KEYWORD",
    "do": "KEYWORD", "for": "KEYWORD", "to": "KEYWORD", "downto": "KEYWORD",
    "integer": "KEYWORD", "real": "KEYWORD", "boolean": "KEYWORD", "char": "KEYWORD",
    "array": "KEYWORD", "of": "KEYWORD", "procedure": "KEYWORD", "function": "KEYWORD",
    "const": "KEYWORD", "type": "KEYWORD",
    "div": "ARITHMETIC_OPERATOR", "mod": "ARITHMETIC_OPERATOR",
    "and": "LOGICAL_OPERATOR", "or": "LOGICAL_OPERATOR", "not": "LOGICAL_OPERATOR"
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
        tokens = []
        current_pos = 0
        
        while current_pos < len(source_code):
            if source_code[current_pos] in self.char_classes['whitespace']:
                current_pos += 1
                continue

            current_state_name = self.start_state
            last_accepted_state = None
            last_accepted_pos = -1

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
                token_type = self.states[last_accepted_state]['token_type']
                lexeme = source_code[current_pos:last_accepted_pos]

                if token_type == 'COMMENT':
                    comment_lexeme = source_code[current_pos:last_accepted_pos]
                    if comment_lexeme.startswith('{'):
                        tokens.append(('COMMENT_START', '{'))
                        tokens.append(('COMMENT_END', '}'))
                    elif comment_lexeme.startswith('(*'):
                        tokens.append(('COMMENT_START', '(*'))
                        tokens.append(('COMMENT_END', '*)'))
                    
                    current_pos = last_accepted_pos
                    continue
                
                if token_type == 'IDENTIFIER':
                    token_type = LOOKUP_TABLE.get(lexeme.lower(), 'IDENTIFIER')
                
                tokens.append((token_type, lexeme))
                current_pos = last_accepted_pos
            else:
                unknown_char = source_code[current_pos]
                print(f"Error: Karakter tidak dikenal -> '{unknown_char}' di posisi {current_pos}")
                tokens.append(('UNKNOWN', unknown_char))
                current_pos += 1
                
        tokens.append(('EOF', ''))
        return tokens