program ArrayTest;
var
  arr: array[1..5] of integer;
begin
  arr[1] := 10;
  writeln('Array[1] = ', arr[1]);
end.