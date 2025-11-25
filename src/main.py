import sys
import os


from lexical_analyzer import Lexer
from parser import Parser

from semantic import SemanticAnalyzer, print_decorated_ast, print_symbol_tables

def main():

    if len(sys.argv) == 2:
        pascal_filename = sys.argv[1]
    else:
        pascal_filename = input("Masukkan nama file Pascal (.pas): ").strip()
        if not pascal_filename.endswith('.pas'):
            pascal_filename += '.pas'


    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    root_dir = os.path.dirname(script_dir)                  


    input_file_path = os.path.join(root_dir, 'test', 'milestone-2', pascal_filename)
    rules_file_path = os.path.join(script_dir, 'lexical_rules.json')


    try:
        with open(input_file_path, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"\n[ERROR] File input tidak ditemukan di path:")
        print(f" -> {input_file_path}")
        print(f"Pastikan file '{pascal_filename}' ada di dalam folder 'test/milestone-2'.")
        sys.exit(1)

    # ---------------------------------------------------------
    # 2. LEXICAL ANALYSIS (Tokenizing)
    # ---------------------------------------------------------
    token_list = []
    try:
        lexer = Lexer(rules_file_path)
        token_list = lexer.tokenize(source_code)
        
        print(f"\n--- Hasil Tokenisasi untuk {pascal_filename} ---")

        print(f"Berhasil: Ditemukan {len(token_list)} token.")
        print("------------------------------------------")

    except Exception as e:
        print(f"[LEXICAL ERROR] Terjadi error saat tokenisasi: {e}")
        sys.exit(1)

    # ---------------------------------------------------------
    # 3. SYNTAX ANALYSIS (Parsing)
    # ---------------------------------------------------------
    parse_tree = None
    try:
        print("\n------- Memulai Syntax Analysis -------")
        parser = Parser(token_list)

        parse_tree = parser.parse() 
        
        if parse_tree:
            print("[SUCCESS] Parse Tree berhasil dibangun.")
        else:
            print("[ERROR] Parser tidak mengembalikan tree (None).")
            sys.exit(1)

    except SyntaxError as e:
        print(f"\n[SYNTAX ERROR]: Berhenti.")
        print(f"Pesan: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[INTERNAL ERROR] Saat parsing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


    try:
        print("\n------- Memulai Semantic Analysis -------")
        analyzer = SemanticAnalyzer()
        
        # Lakukan analisis semantic pada parse tree
        decorated_ast = analyzer.analyze(parse_tree)

        # Cek apakah ada error semantic
        if analyzer.errors:
            print("\n[SEMANTIC ERRORS FOUND]")
            for err in analyzer.errors:
                print(f" - {err}")
        else:
            print("[SUCCESS] Semantic Analysis selesai tanpa error.")
            
            # Tampilkan Decorated AST (Panggil fungsi dari ast_printer.py)
            print("\n=========== DECORATED AST ===========")
            print_decorated_ast(decorated_ast)
            
            # Tampilkan Symbol Table (Panggil fungsi dari ast_printer.py)
            print_symbol_tables(analyzer)

    except Exception as e:
        print(f"\n[SEMANTIC ERROR CRASH]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()