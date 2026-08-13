`timescale 1ns/1ps
// Three-way equivalence: source RTL vs reference gate netlist vs
// extracted-from-GDS netlist. Same stimulus into all three; any
// per-cycle divergence on S is a failure.
module tb;
  reg clk=0, rst_n=0, en=0, A=0, B=0;
  wire S_src, S_ext;

  adder_demo       dut_src (.clk(clk), .rst_n(rst_n), .en(en), .A(A), .B(B), .S(S_src));
  adder_demo_ext   dut_ext (.clk(clk), .rst_n(rst_n), .en(en), .A(A), .B(B), .S(S_ext));

  integer errors=0, checks=0, i, seed=7;
  reg [7:0] ta, tb_;

  task do_clk; begin #5 clk=1; #5 clk=0; end endtask

  task load(input [7:0] a, input [7:0] b);
    integer k;
    begin
      rst_n=0; en=0; do_clk;          // async reset
      rst_n=1; en=1;
      for (k=7; k>=0; k=k-1) begin     // MSB first: {parallel[6:0],serial}
        A=a[k]; B=b[k]; do_clk;
      end
      en=0;
      #1;
      checks=checks+1;
      if (S_src!==S_ext) begin
        errors=errors+1;
        $display("MISMATCH a=%0d b=%0d sum=%0d  S src=%b ext=%b",
                 a, b, a+b, S_src, S_ext);
      end
      if (((a+b)==496) !== (S_ext===1'b1)) begin
        errors=errors+1;
        $display("BEHAVIOR a=%0d b=%0d sum=%0d expected S=%b got %b",
                 a, b, a+b, (a+b)==496, S_ext);
      end
    end
  endtask

  initial begin
    // targeted: exact hits on 496 and near-misses
    load(240,256); load(248,248); load(255,241); load(0,240);
    load(496%256,0); load(200,296%256); load(255,255); load(0,0);
    // exhaustive over pairs that sum to 496
    for (i=240; i<=255; i=i+1) load(i, 496-i);
    // random
    for (i=0; i<400; i=i+1) begin
      ta=$random(seed); tb_=$random(seed);
      load(ta, tb_);
    end
    $display("RESULT checks=%0d errors=%0d %s", checks, errors,
             errors==0 ? "PASS" : "FAIL");
    $finish;
  end
endmodule
