program Loop;
variabel
  i, x : integer;
mulai
  x := 0;
  
  untuk i := 1 ke 10 lakukan
    mulai
      x := x + i;
      jika (i = 5) maka
        writeln('Setengah jalan!')
      selain_itu
        writeln(i);
    selesai;
  
  selama x > 100 lakukan
    x := x - 1;
    
selesai.