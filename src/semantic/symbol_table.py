from typing import List, Dict, Any, Optional
from enum import Enum, auto

class ObjType(Enum):
    """Jenis object dalam symbol table"""
    CONSTANT = auto()
    VARIABLE = auto()
    TYPE = auto()
    PROCEDURE = auto()
    FUNCTION = auto()
    PROGRAM = auto()

class BaseType(Enum):
    """Tipe data dasar Pascal-S"""
    INTEGER = 1
    REAL = 2
    BOOLEAN = 3
    CHAR = 4
    STRING = 5
    ARRAY = 6
    RECORD = 7
    VOID = 8
    RANGE = 9

class SymbolTable:
    """
    Symbol Table untuk Pascal-S Compiler
    Implementasi sesuai spesifikasi dengan 3 tabel: tab, btab, atab
    """
    
    def __init__(self):
        self.tab: List[Optional[Dict[str, Any]]] = []

        self.btab: List[Dict[str, Any]] = []
        
        self.atab: List[Dict[str, Any]] = []
        
        self._init_reserved_words()
        
        self.display: List[int] = []
        

        self.level: int = -1
        
        self.next_adr: int = 0
    
        self.user_id_start = 31
        self.next_user_id = 31
        
        self.const_values: Dict[str, Any] = {}
        
    def _init_reserved_words(self):
        """Initialize reserved words dan built-in types (indices 0-28)"""
        reserved_types = [
            ("integer", BaseType.INTEGER),
            ("real", BaseType.REAL), 
            ("boolean", BaseType.BOOLEAN),
            ("char", BaseType.CHAR),
            ("string", BaseType.STRING)
        ]
        
        for name, base_type in reserved_types:
            self.tab.append({
                "name": name,
                "obj": ObjType.TYPE,
                "type": base_type.value,
                "ref": 0,
                "nrm": 1,
                "lev": 0,
                "adr": 0,
                "link": 0
            })
        
        other_keywords = [
            "program", "variabel", "mulai", "selesai", "jika", "maka", "selain_itu",
            "selama", "lakukan", "untuk", "ke", "turun_ke", "larik", "dari", 
            "prosedur", "fungsi", "konstanta", "tipe", "kasus", "rekaman", 
            "ulangi", "sampai"
        ]
        
        for name in other_keywords:
            self.tab.append({
                "name": name,
                "obj": ObjType.TYPE,
                "type": BaseType.VOID.value,
                "ref": 0,
                "nrm": 1,
                "lev": 0,
                "adr": 0,
                "link": len(self.tab) - 1 if self.tab else 0
            })
        
        built_ins = [
            ("writeln", ObjType.PROCEDURE, BaseType.VOID.value),
            ("readln", ObjType.PROCEDURE, BaseType.VOID.value),
            ("write", ObjType.PROCEDURE, BaseType.VOID.value),
            ("read", ObjType.PROCEDURE, BaseType.VOID.value)
        ]
        
        for name, obj_type, data_type in built_ins:
            self.tab.append({
                "name": name,
                "obj": obj_type,
                "type": data_type,
                "ref": 0,
                "nrm": 1,
                "lev": 0,
                "adr": 0,
                "link": len(self.tab) - 1
            })
    
    def enter_block(self) -> int:
        """
        Memasuki block baru (procedure, function, atau compound statement)
        Returns: index dari block yang baru dibuat
        """
        self.level += 1
        block_index = len(self.btab)
        
        self.btab.append({
            "last": 0,      
            "lpar": 0,      
            "psze": 0,      
            "vsze": 0       
        })
        
        self.display.append(block_index)
        return block_index
    
    def leave_block(self):
        """Keluar dari block saat ini"""
        if self.level > 0:
            self.level -= 1
            self.display.pop()
    
    def enter_identifier(self, name: str, obj_type: ObjType, data_type: int, 
                        ref: int = 0, nrm: int = 1, size: int = 1, 
                        const_value: Any = None) -> int:
        """
        Memasukkan identifier baru ke symbol table
        Returns: index dari identifier yang baru dimasukkan
        """
        tab_index = self.next_user_id
        self.next_user_id += 1
        
        if obj_type == ObjType.VARIABLE:
            adr = self.next_adr
            self.next_adr += size
        else:
            adr = 0

        current_block_idx = self.display[self.level]
        current_block = self.btab[current_block_idx]
        prev_last = current_block["last"]
        
        if tab_index >= len(self.tab):
            while len(self.tab) <= tab_index:
                self.tab.append(None)
        

        link_value = prev_last 
      
        self.tab[tab_index] = {
            "name": name,
            "obj": obj_type,
            "type": data_type,
            "ref": ref,
            "nrm": nrm,
            "lev": self.level,
            "adr": adr,
            "link": link_value
        }
        if obj_type == ObjType.CONSTANT and const_value is not None:
            self.const_values[name] = const_value
        current_block["last"] = tab_index
        
        if obj_type == ObjType.VARIABLE:
            current_block["vsze"] += size
            
        return tab_index

    def find_identifier(self, name: str) -> Optional[int]:
        for level in range(self.level, -1, -1):
            block_index = self.display[level]
            last_idx = self.btab[block_index]["last"]
            
            current_idx = last_idx
            while current_idx >= self.user_id_start:
                entry = self.tab[current_idx]
                if entry is not None and entry["name"] == name:
                    return current_idx
                if entry is None:
                    break
                current_idx = entry["link"]
        
            for i in range(self.user_id_start):
                if i < len(self.tab) and self.tab[i] and self.tab[i]["name"] == name:
                    return i
                        
        return None
    def get_constant_value(self, name: str) -> Optional[Any]:
        """Mengambil nilai konstanta"""
        return self.const_values.get(name)
    
    def enter_array(self, index_type: int, element_type: int, 
                   low_bound: int, high_bound: int, 
                   element_size: int = 1) -> int:
        """
        Memasukkan array type ke array table
        Returns: index di atab
        """
        array_size = (high_bound - low_bound + 1) * element_size
        
        atab_index = len(self.atab)
        self.atab.append({
            "index_type": index_type,
            "element_type": element_type,
            "eref": 0,
            "low": low_bound,
            "high": high_bound,
            "element_size": element_size,
            "size": array_size
        })
        
        return atab_index