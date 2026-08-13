`timescale 1ns/1ps
module tb;
 reg clk=0,rst_n=0,enable=0,I=0; wire [7:0] O; wire success;
 integer k; reg hit=0; integer hitcyc=-1;
 puzzle dut(.clk(clk),.rst_n(rst_n),.enable(enable),.I(I),.O(O),.success(success));
 task step; begin #5 clk=1; #5 clk=0; end endtask
 initial begin
  rst_n=0; enable=0; I=0; step;   // reset
  rst_n=1;
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=1; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=2; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=3; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=4; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=5; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=6; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=7; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=8; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=9; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=10; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=11; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=12; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=13; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=14; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=15; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=16; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=17; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=18; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=19; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=20; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=21; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=22; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=23; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=24; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=25; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=26; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=27; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=28; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=29; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=30; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=31; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=32; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=33; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=34; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=35; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=36; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=37; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=38; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=39; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=40; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=41; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=42; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=43; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=44; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=45; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=46; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=47; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=48; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=49; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=50; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=51; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=52; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=53; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=54; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=55; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=56; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=57; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=58; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=59; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=60; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=61; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=62; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=63; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=64; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=65; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=66; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=67; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=68; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=69; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=70; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=71; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=72; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=73; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=74; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=75; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=76; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=77; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=78; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=79; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=80; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=81; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=82; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=83; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=84; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=85; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=86; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=87; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=88; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=89; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=90; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=91; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=92; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=93; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=94; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=95; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=96; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=97; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=98; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=99; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=100; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=101; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=102; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=103; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=104; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=105; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=106; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=107; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=108; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=109; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=110; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=111; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=112; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=113; end
  I=1; enable=1; step; if(success && !hit) begin hit=1; hitcyc=114; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=115; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=116; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=117; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=118; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=119; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=120; end
  I=0; enable=1; step; if(success && !hit) begin hit=1; hitcyc=121; end
  I=0; enable=0; step; if(success && !hit) begin hit=1; hitcyc=122; end
  I=0; enable=0; step; if(success && !hit) begin hit=1; hitcyc=123; end
  #1;
  $display("success=%b first_high_cycle=%0d final_O=%h", success, hitcyc, O);
  if (success) $display("VERIFIED: success asserted"); else $display("NOT verified");
  $finish; end
endmodule
