program LogicTest;
var
  x, y: boolean;
begin
  x := true;
  y := not x and (x or false);
  writeln('Logic = ', y);
end.