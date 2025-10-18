program ErrorTest;
var
  a: integer;
begin
  a := 5; { This is a comment }
  b := a + $; { Invalid symbol }
  writeln(a);
end.