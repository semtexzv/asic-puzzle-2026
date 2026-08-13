`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,enable=0,I=0; wire [7:0] O; wire success;
  integer g,c,NG; reg [120:0] G [0:4095];
  puzzle dut(.clk(clk),.rst_n(rst_n),.enable(enable),.I(I),.O(O),.success(success));
  task step; begin #5 clk=1; #5 clk=0; end endtask
  initial begin
    if(!$value$plusargs("ng=%d",NG)) NG=0;
    $readmemb("build/grids.mem", G);
    for (g=0; g<NG; g=g+1) begin
      rst_n=0; enable=0; I=0; step; rst_n=1; enable=1;
      for (c=0;c<121;c=c+1) begin I=G[g][120-c]; step; end   // bit 120 = cell0
      I=0; $write("G%0d ",g);
      for (c=0;c<13;c=c+1) begin step; $write("%c",(O>=8'h20&&O<8'h7f)?O:8'h5f); end
      $display("");
    end $finish;
  end
endmodule
