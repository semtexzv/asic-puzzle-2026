// Formal wrapper. `success` is an output port so tools can address it.
// rst_n held high -> flop `initial` values model the post-reset state.
module top (input clk, input en, input i, input rstn, output success, output [7:0] O);
  puzzle dut (.clk(clk), .rst_n(rstn), .enable(en), .I(i), .O(O), .success(success));
`ifdef FORMAL
  always @(posedge clk) begin
    assume (rstn);
    assert (!success);      // CEX = winning input trace
  end
`endif
endmodule
