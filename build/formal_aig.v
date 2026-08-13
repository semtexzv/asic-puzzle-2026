module top (input clk, input i, output success);
  wire [7:0] O;
  puzzle dut (.clk(clk), .rst_n(1'b1), .enable(1'b1), .I(i), .O(O), .success(success));
endmodule
