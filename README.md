# JWA-Tubes-IF2224
### **Identitas Kelompok**

* **Kode Kelompok:** JWA 
* **Kelas:** K01


|            Nama             |      NIM      |
| --------------------------  | ------------- |
| Muhammad Alfansya           |    13523005   |
| Orvin Andika Ikhsan Abhista |    13523017   |
| Dzaky Aurelia Fawwaz        |    13523065   |
| Ferdin Arsenarendra Purtadi |    13523117   |

---
### **Deskripsi Program**

Program ini adalah sebuah Lexical Scanner untuk bahasa pemrograman Pascal-S. Tugas utamanya adalah membaca file kode sumber (`.pas`) dan memecahnya menjadi serangkaian token.

Setiap token adalah unit leksikal dasar dari bahasa, seperti `KEYWORD`, `IDENTIFIER`, `NUMBER`, `OPERATOR`, dan simbol lainnya. *Scanner* ini diimplementasikan menggunakan model **Deterministic Finite Automaton (DFA)** yang aturannya didefinisikan dalam file eksternal `lexical_rules.json`.

Output dari program adalah daftar token yang berhasil diidentifikasi, lengkap dengan tipe dan nilai.

---
### **Requirements**

* Python

---
### **Cara Instalasi dan Penggunaan Program**

1.  **Clone Repositori**
    ```bash
    git clone https://github.com/orvin14/JWA-Tubes-IF2224
    cd JWA-Tubes-IF2224
    ```

2.  **Siapkan File Aturan dan Kode Sumber**
    * Pastikan file `main.py` dan `lexical_rules.json` berada di direktori yang sama.
    * Siapkan file kode sumber Pascal-S yang ingin diuji (misalnya, `program.pas`).

3.  **Jalankan Program**
    Program dieksekusi melalui terminal atau command prompt dengan memberikan file kode sumber Pascal-S sebagai argumen.

    ```bash
    python main.py program.pas
    ```


---
### **Pembagian Tugas**
|            Nama             |      NIM      |               Pembagian Tugas               |
| --------------------------  | ------------- | ------------------------------------------- |
| Muhammad Alfansya           |    13523005   | DFA, Laporan                                |
| Orvin Andika Ikhsan Abhista |    13523017   | DFA, Laporan                                |
| Dzaky Aurelia Fawwaz        |    13523065   | DFA, Testing, Laporan                       |
| Ferdin Arsenarendra Purtadi |    13523117   | DFA, Laporan, Implementasi main.py          |
