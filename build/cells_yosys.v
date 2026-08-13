// auto-generated yosys-friendly sky130 cell models

`default_nettype none

module sky130_fd_sc_hd__a2111oi (A1, A2, B1, C1, D1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  input D1;
  output Y;
  assign Y = (~A1&~B1&~C1&~D1) | (~A2&~B1&~C1&~D1);
endmodule

module sky130_fd_sc_hd__a211o (A1, A2, B1, C1, X);
  input A1;
  input A2;
  input B1;
  input C1;
  output X;
  assign X = (A1&A2) | (B1) | (C1);
endmodule

module sky130_fd_sc_hd__a211oi (A1, A2, B1, C1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  output Y;
  assign Y = (~A1&~B1&~C1) | (~A2&~B1&~C1);
endmodule

module sky130_fd_sc_hd__a21bo (A1, A2, B1_N, X);
  input A1;
  input A2;
  input B1_N;
  output X;
  assign X = (A1&A2) | (~B1_N);
endmodule

module sky130_fd_sc_hd__a21boi (A1, A2, B1_N, Y);
  input A1;
  input A2;
  input B1_N;
  output Y;
  assign Y = (~A1&B1_N) | (~A2&B1_N);
endmodule

module sky130_fd_sc_hd__a21o (A1, A2, B1, X);
  input A1;
  input A2;
  input B1;
  output X;
  assign X = (A1&A2) | (B1);
endmodule

module sky130_fd_sc_hd__a21oi (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1);
endmodule

module sky130_fd_sc_hd__a221o (A1, A2, B1, B2, C1, X);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output X;
  assign X = (B1&B2) | (A1&A2) | (C1);
endmodule

module sky130_fd_sc_hd__a221oi (A1, A2, B1, B2, C1, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output Y;
  assign Y = (~A1&~B1&~C1) | (~A1&~B2&~C1) | (~A2&~B1&~C1) | (~A2&~B2&~C1);
endmodule

module sky130_fd_sc_hd__a22o (A1, A2, B1, B2, X);
  input A1;
  input A2;
  input B1;
  input B2;
  output X;
  assign X = (B1&B2) | (A1&A2);
endmodule

module sky130_fd_sc_hd__a22oi (A1, A2, B1, B2, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  output Y;
  assign Y = (~A1&~B1) | (~A1&~B2) | (~A2&~B1) | (~A2&~B2);
endmodule

module sky130_fd_sc_hd__a311o (A1, A2, A3, B1, C1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input C1;
  output X;
  assign X = (A1&A2&A3) | (B1) | (C1);
endmodule

module sky130_fd_sc_hd__a31o (A1, A2, A3, B1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  output X;
  assign X = (A1&A2&A3) | (B1);
endmodule

module sky130_fd_sc_hd__a31oi (A1, A2, A3, B1, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1) | (~A3&~B1);
endmodule

module sky130_fd_sc_hd__a32o (A1, A2, A3, B1, B2, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output X;
  assign X = (A1&A2&A3) | (B1&B2);
endmodule

module sky130_fd_sc_hd__a41oi (A1, A2, A3, A4, B1, Y);
  input A1;
  input A2;
  input A3;
  input A4;
  input B1;
  output Y;
  assign Y = (~A1&~B1) | (~A2&~B1) | (~A3&~B1) | (~A4&~B1);
endmodule

module sky130_fd_sc_hd__and2 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A&B);
endmodule

module sky130_fd_sc_hd__and2b (A_N, B, X);
  input A_N;
  input B;
  output X;
  assign X = (~A_N&B);
endmodule

module sky130_fd_sc_hd__and3 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (A&B&C);
endmodule

module sky130_fd_sc_hd__and3b (A_N, B, C, X);
  input A_N;
  input B;
  input C;
  output X;
  assign X = (~A_N&B&C);
endmodule

module sky130_fd_sc_hd__and4 (A, B, C, D, X);
  input A;
  input B;
  input C;
  input D;
  output X;
  assign X = (A&B&C&D);
endmodule

module sky130_fd_sc_hd__and4b (A_N, B, C, D, X);
  input A_N;
  input B;
  input C;
  input D;
  output X;
  assign X = (~A_N&B&C&D);
endmodule

module sky130_fd_sc_hd__and4bb (A_N, B_N, C, D, X);
  input A_N;
  input B_N;
  input C;
  input D;
  output X;
  assign X = (~A_N&~B_N&C&D);
endmodule

module sky130_fd_sc_hd__buf (A, X);
  input A;
  output X;
  assign X = (A);
endmodule

module sky130_fd_sc_hd__clkbuf (A, X);
  input A;
  output X;
  assign X = (A);
endmodule

module sky130_fd_sc_hd__conb (HI, LO);
  output HI;
  output LO;
  assign HI = 1'b1;
  assign LO = 1'b0;
endmodule

module sky130_fd_sc_hd__dfrtp (CLK, D, RESET_B, Q);
  input CLK, D, RESET_B; output reg Q;
  initial Q = 1'b0;
  always @(posedge CLK or negedge RESET_B)
    if (!RESET_B) Q <= 1'b0; else Q <= D;
endmodule

module sky130_fd_sc_hd__dfstp (CLK, D, SET_B, Q);
  input CLK, D, SET_B; output reg Q;
  initial Q = 1'b1;
  always @(posedge CLK or negedge SET_B)
    if (!SET_B) Q <= 1'b1; else Q <= D;
endmodule

module sky130_fd_sc_hd__dfxtp (CLK, D, Q);
  input CLK, D; output reg Q;
  initial Q = 1'b0;
  always @(posedge CLK) Q <= D;
endmodule

module sky130_fd_sc_hd__inv (A, Y);
  input A;
  output Y;
  assign Y = (~A);
endmodule

module sky130_fd_sc_hd__mux2 (A0, A1, S, X);
  input A0;
  input A1;
  input S;
  output X;
  assign X = (A0&~S) | (A1&S);
endmodule

module sky130_fd_sc_hd__nand2 (A, B, Y);
  input A;
  input B;
  output Y;
  assign Y = (~A) | (~B);
endmodule

module sky130_fd_sc_hd__nand2b (A_N, B, Y);
  input A_N;
  input B;
  output Y;
  assign Y = (A_N) | (~B);
endmodule

module sky130_fd_sc_hd__nand3 (A, B, C, Y);
  input A;
  input B;
  input C;
  output Y;
  assign Y = (~A) | (~B) | (~C);
endmodule

module sky130_fd_sc_hd__nand3b (A_N, B, C, Y);
  input A_N;
  input B;
  input C;
  output Y;
  assign Y = (A_N) | (~B) | (~C);
endmodule

module sky130_fd_sc_hd__nand4 (A, B, C, D, Y);
  input A;
  input B;
  input C;
  input D;
  output Y;
  assign Y = (~A) | (~B) | (~C) | (~D);
endmodule

module sky130_fd_sc_hd__nor2 (A, B, Y);
  input A;
  input B;
  output Y;
  assign Y = (~A&~B);
endmodule

module sky130_fd_sc_hd__nor3 (A, B, C, Y);
  input A;
  input B;
  input C;
  output Y;
  assign Y = (~A&~B&~C);
endmodule

module sky130_fd_sc_hd__nor3b (A, B, C_N, Y);
  input A;
  input B;
  input C_N;
  output Y;
  assign Y = (~A&~B&C_N);
endmodule

module sky130_fd_sc_hd__nor4 (A, B, C, D, Y);
  input A;
  input B;
  input C;
  input D;
  output Y;
  assign Y = (~A&~B&~C&~D);
endmodule

module sky130_fd_sc_hd__nor4b (A, B, C, D_N, Y);
  input A;
  input B;
  input C;
  input D_N;
  output Y;
  assign Y = (~A&~B&~C&D_N);
endmodule

module sky130_fd_sc_hd__o211a (A1, A2, B1, C1, X);
  input A1;
  input A2;
  input B1;
  input C1;
  output X;
  assign X = (A1&B1&C1) | (A2&B1&C1);
endmodule

module sky130_fd_sc_hd__o211ai (A1, A2, B1, C1, Y);
  input A1;
  input A2;
  input B1;
  input C1;
  output Y;
  assign Y = (~A1&~A2) | (~B1) | (~C1);
endmodule

module sky130_fd_sc_hd__o21a (A1, A2, B1, X);
  input A1;
  input A2;
  input B1;
  output X;
  assign X = (A1&B1) | (A2&B1);
endmodule

module sky130_fd_sc_hd__o21ai (A1, A2, B1, Y);
  input A1;
  input A2;
  input B1;
  output Y;
  assign Y = (~A1&~A2) | (~B1);
endmodule

module sky130_fd_sc_hd__o21ba (A1, A2, B1_N, X);
  input A1;
  input A2;
  input B1_N;
  output X;
  assign X = (A1&~B1_N) | (A2&~B1_N);
endmodule

module sky130_fd_sc_hd__o21bai (A1, A2, B1_N, Y);
  input A1;
  input A2;
  input B1_N;
  output Y;
  assign Y = (~A1&~A2) | (B1_N);
endmodule

module sky130_fd_sc_hd__o221a (A1, A2, B1, B2, C1, X);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  output X;
  assign X = (A1&B1&C1) | (A2&B1&C1) | (A1&B2&C1) | (A2&B2&C1);
endmodule

module sky130_fd_sc_hd__o22a (A1, A2, B1, B2, X);
  input A1;
  input A2;
  input B1;
  input B2;
  output X;
  assign X = (A1&B1) | (A2&B1) | (A1&B2) | (A2&B2);
endmodule

module sky130_fd_sc_hd__o22ai (A1, A2, B1, B2, Y);
  input A1;
  input A2;
  input B1;
  input B2;
  output Y;
  assign Y = (~B1&~B2) | (~A1&~A2);
endmodule

module sky130_fd_sc_hd__o2bb2a (A1_N, A2_N, B1, B2, X);
  input A1_N;
  input A2_N;
  input B1;
  input B2;
  output X;
  assign X = (~A1_N&B1) | (~A2_N&B1) | (~A1_N&B2) | (~A2_N&B2);
endmodule

module sky130_fd_sc_hd__o311a (A1, A2, A3, B1, C1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input C1;
  output X;
  assign X = (A1&B1&C1) | (A2&B1&C1) | (A3&B1&C1);
endmodule

module sky130_fd_sc_hd__o31a (A1, A2, A3, B1, X);
  input A1;
  input A2;
  input A3;
  input B1;
  output X;
  assign X = (A1&B1) | (A2&B1) | (A3&B1);
endmodule

module sky130_fd_sc_hd__o31ai (A1, A2, A3, B1, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  output Y;
  assign Y = (~A1&~A2&~A3) | (~B1);
endmodule

module sky130_fd_sc_hd__o32a (A1, A2, A3, B1, B2, X);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output X;
  assign X = (A1&B1) | (A1&B2) | (A2&B1) | (A3&B1) | (A2&B2) | (A3&B2);
endmodule

module sky130_fd_sc_hd__o32ai (A1, A2, A3, B1, B2, Y);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  output Y;
  assign Y = (~A1&~A2&~A3) | (~B1&~B2);
endmodule

module sky130_fd_sc_hd__or2 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A) | (B);
endmodule

module sky130_fd_sc_hd__or3 (A, B, C, X);
  input A;
  input B;
  input C;
  output X;
  assign X = (A) | (B) | (C);
endmodule

module sky130_fd_sc_hd__or3b (A, B, C_N, X);
  input A;
  input B;
  input C_N;
  output X;
  assign X = (A) | (B) | (~C_N);
endmodule

module sky130_fd_sc_hd__or4 (A, B, C, D, X);
  input A;
  input B;
  input C;
  input D;
  output X;
  assign X = (A) | (B) | (C) | (D);
endmodule

module sky130_fd_sc_hd__or4b (A, B, C, D_N, X);
  input A;
  input B;
  input C;
  input D_N;
  output X;
  assign X = (A) | (B) | (C) | (~D_N);
endmodule

module sky130_fd_sc_hd__or4bb (A, B, C_N, D_N, X);
  input A;
  input B;
  input C_N;
  input D_N;
  output X;
  assign X = (A) | (B) | (~C_N) | (~D_N);
endmodule

module sky130_fd_sc_hd__xnor2 (A, B, Y);
  input A;
  input B;
  output Y;
  assign Y = (~A&~B) | (A&B);
endmodule

module sky130_fd_sc_hd__xor2 (A, B, X);
  input A;
  input B;
  output X;
  assign X = (A&~B) | (~A&B);
endmodule
