`timescale 1ns/1ps
module tb;
 reg clk=0,rst_n=0,enable=0,I=0; wire [7:0] O; wire success;
 puzzle dut(.clk(clk),.rst_n(rst_n),.enable(enable),.I(I),.O(O),.success(success));
 wire [91:0] STATE = {dut.i7.Q, dut.i8.Q, dut.i9.Q, dut.i10.Q, dut.i11.Q, dut.i12.Q, dut.i123.Q, dut.i124.Q, dut.i125.Q, dut.i126.Q, dut.i127.Q, dut.i128.Q, dut.i129.Q, dut.i130.Q, dut.i131.Q, dut.i132.Q, dut.i133.Q, dut.i134.Q, dut.i135.Q, dut.i136.Q, dut.i137.Q, dut.i138.Q, dut.i139.Q, dut.i140.Q, dut.i141.Q, dut.i142.Q, dut.i143.Q, dut.i146.Q, dut.i147.Q, dut.i148.Q, dut.i149.Q, dut.i150.Q, dut.i151.Q, dut.i152.Q, dut.i153.Q, dut.i154.Q, dut.i155.Q, dut.i156.Q, dut.i157.Q, dut.i158.Q, dut.i159.Q, dut.i160.Q, dut.i161.Q, dut.i162.Q, dut.i163.Q, dut.i164.Q, dut.i165.Q, dut.i166.Q, dut.i167.Q, dut.i168.Q, dut.i169.Q, dut.i170.Q, dut.i171.Q, dut.i172.Q, dut.i173.Q, dut.i174.Q, dut.i175.Q, dut.i176.Q, dut.i177.Q, dut.i178.Q, dut.i179.Q, dut.i180.Q, dut.i181.Q, dut.i182.Q, dut.i183.Q, dut.i184.Q, dut.i185.Q, dut.i186.Q, dut.i187.Q, dut.i188.Q, dut.i189.Q, dut.i190.Q, dut.i191.Q, dut.i192.Q, dut.i193.Q, dut.i194.Q, dut.i196.Q, dut.i197.Q, dut.i198.Q, dut.i199.Q, dut.i200.Q, dut.i202.Q, dut.i203.Q, dut.i204.Q, dut.i205.Q, dut.i206.Q, dut.i207.Q, dut.i208.Q, dut.i209.Q, dut.i307.Q, dut.i388.Q, dut.i461.Q};
 integer t,c;
 reg [121:0] invec [0:6];
 reg [91:0] st [0:6];
 task step; begin #5 clk=1; #5 clk=0; end endtask
 initial begin
  invec[0] = 122'b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
  invec[1] = 122'b00101111001011011001000010100110100110100101101111010110110100111010110000001111101001011011111011000001000010101001100010;
  invec[2] = 122'b11111100111101010100010001101001110100010011011000010010100101011101110001011010111000000001111110101001010100101000111011;
  invec[3] = 122'b11010011110110001101010011001111010010110110110111000100010001100111000001010101010001011010000101101000010110000001011001;
  invec[4] = 122'b00100010000100100001111110010001111110011010111001001010101011010110100000010100001111001000001101000010011000101111101101;
  invec[5] = 122'b10100100011110001001100111011100010011110100100110011110001010001011101101001101101001000100100111101110010100001001111100;
  invec[6] = 122'b10000110011010101000011001001101101101101110011111010100100001011101001101011001100110001100101010101100001100100110010001;
  for (t=0;t<7;t=t+1) begin
   rst_n=0; enable=0; I=0; step;
   rst_n=1; enable=1;
   for (c=0;c<122;c=c+1) begin I=invec[t][c]; step; end
   st[t]=STATE;
  end
  for (t=0;t<7;t=t+1) $display("STATE %0d %h", t, st[t]);
  $finish; end
endmodule
