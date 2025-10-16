import sys
import os
from lexical_analyzer import Lexer

def main():
    #input pascal file name
    if len(sys.argv) == 2:
        pascal_filename = sys.argv[1]
    else:
        pascal_filename = input("Masukkan nama file Pascal (.pas): ").strip()
        if not pascal_filename.endswith('.pas'):
            pascal_filename += '.pas'

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    #Path to input .pas file and lexical rules file
    input_file_path = os.path.join(root_dir, 'test', 'milestone-1', pascal_filename)
    rules_file_path = os.path.join(script_dir, 'lexical_rules.json')

    # Read source code from .pas file
    try:
        with open(input_file_path, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File input '{input_file_path}' tidak ditemukan.")
        print(f"Pastikan file '{pascal_filename}' ada di dalam folder 'test/milestone-1'.")
        sys.exit(1)

    # Tokenize source code
    try:
        lexer = Lexer(rules_file_path)
        token_list = lexer.tokenize(source_code)
        
        print(f"--- Hasil Tokenisasi untuk {pascal_filename} ---")
        for token_type, token_value in token_list:
            print(f"{token_type}({token_value})")
        print("------------------------------------------\n")

    except Exception as e:
        print(f"Terjadi error saat proses tokenisasi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()