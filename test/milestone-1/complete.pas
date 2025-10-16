program AllTokensTest;

{ 
  Ini adalah program demonstrasi untuk menguji lexical scanner.
  Waktu sekarang: Minggu, 12 Oktober 2025, 10:24 WIB di Bandung.
}

const
  count = 22;

type
  IndexRange = 1..count;
  DataSet = array[IndexRange] of real;

var
  x, y, z     : integer;
  sum, avg    : real;
  isComplete  : boolean;
  initial     : char;
  message     : string;
  myData      : DataSet;

procedure CalculateSum(var a: integer; b: integer);
begin
  a := a + b;
  writeln('Prosedur selesai dijalankan');
end;

function IsPositive(num: integer): boolean;
begin
  IsPositive := num > 0;
end;

(* Program utama dimulai di sini *)
begin
  x := 2018;
  y := x - 1996; { Operator aritmatika: +, -, *, / }
  sum := (x + y) * 1.0;
  avg := sum / 2.0;

  z := x div 100;
  y := count mod 3;

  (* Blok kondisional dengan operator relasional dan logika *)
  if (y = 1) and not (x <= 1000) then
  begin
    isComplete := (z > 0) or (x <> y);
    writeln('Kondisi pertama terpenuhi.');
  end
  else
  begin
    isComplete := false;
  end;

  while y < 5 do
  begin
    y := y + 1;
  end;

  for x := 1 to 5 do
  begin
    myData[x] := x;
  end;

  for z := count downto 20 do
  begin
    writeln('Hitung mundur: ', z);
  end;
  
  initial := 'a';
  CalculateSum(y, 3);
  
  writeln('tbfo', ' seru sekali');
end.