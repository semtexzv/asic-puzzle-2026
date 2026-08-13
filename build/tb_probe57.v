`timescale 1ns/1ps
module tb;
 reg clk=0,rst_n=0,enable=0,I=0; wire [7:0] O; wire success;
 integer g,c,NG; reg [120:0] G [0:255];
 wire [56:0] ST = {dut.i123.Q, dut.i124.Q, dut.i130.Q, dut.i131.Q, dut.i132.Q, dut.i133.Q, dut.i134.Q, dut.i135.Q, dut.i136.Q, dut.i137.Q, dut.i139.Q, dut.i140.Q, dut.i141.Q, dut.i143.Q, dut.i146.Q, dut.i148.Q, dut.i151.Q, dut.i152.Q, dut.i153.Q, dut.i154.Q, dut.i155.Q, dut.i156.Q, dut.i157.Q, dut.i158.Q, dut.i159.Q, dut.i160.Q, dut.i161.Q, dut.i162.Q, dut.i165.Q, dut.i166.Q, dut.i167.Q, dut.i171.Q, dut.i172.Q, dut.i173.Q, dut.i174.Q, dut.i175.Q, dut.i176.Q, dut.i177.Q, dut.i178.Q, dut.i179.Q, dut.i181.Q, dut.i182.Q, dut.i183.Q, dut.i184.Q, dut.i185.Q, dut.i186.Q, dut.i187.Q, dut.i188.Q, dut.i191.Q, dut.i192.Q, dut.i193.Q, dut.i194.Q, dut.i196.Q, dut.i203.Q, dut.i206.Q, dut.i209.Q, dut.i388.Q};
 puzzle dut(.clk(clk),.rst_n(rst_n),.enable(enable),.I(I),.O(O),.success(success));
 task step; begin #5 clk=1; #5 clk=0; end endtask
 initial begin if(!$value$plusargs("ng=%d",NG)) NG=0; $readmemb("build/probe.mem",G);
  for(g=0;g<NG;g=g+1) begin rst_n=0;enable=0;I=0;step; rst_n=1;enable=1;
   for(c=0;c<121;c=c+1) begin I=G[g][120-c]; step; end
   $display("ST %0d %h",g,ST);
  end $finish; end
endmodule
