`timescale 1ns/1ps
module tb;
 reg clk=0,rst_n=0,enable=0,I=0; wire [7:0] O; wire success;
 integer t,c,seed; reg [7:0] msg [0:15];
 puzzle dut(.clk(clk),.rst_n(rst_n),.enable(enable),.I(I),.O(O),.success(success));
 task step; begin #5 clk=1; #5 clk=0; end endtask
 initial begin seed=12345;
  for (t=0;t<600;t=t+1) begin
   rst_n=0; enable=0; I=0; step; rst_n=1; enable=1;
   for (c=0;c<121;c=c+1) begin I=$random(seed)&1; step; end
   I=0;
   for (c=0;c<10;c=c+1) step;           // let display settle
   $write("MSG ");
   for (c=0;c<16;c=c+1) begin step; $write("%c",(O>=8'h20&&O<8'h7f)?O:8'h5f); end
   $display(" %b",success);
  end $finish; end
endmodule
