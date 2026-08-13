#!/usr/bin/env python3
"""Generate a self-checking Verilog testbench from a VCD trace.

Replays the recorded input signals (clk, rst_n, enable, I) into the
extracted `puzzle` module and, at every timestamp that the VCD records
an output value, checks the simulated O/success against the recorded
value. A clean pass means the GDS-extracted netlist reproduces the real
chip's I/O behavior on this stimulus.
"""
import re
import sys

INPUTS = {"clk", "rst_n", "enable", "I"}
OUTPUTS = {"O", "success"}


def parse_vcd(path):
    id2sig = {}
    widths = {}
    for line in open(path):
        m = re.match(r"\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\w+)(?:\s+\[[\d:]+\])?\s+\$end",
                     line.strip())
        if m:
            w, code, name = int(m.group(1)), m.group(2), m.group(3)
            id2sig[code] = name
            widths[name] = w

    changes = []  # (time, signal, value_str)
    t = 0
    in_defs = True
    for line in open(path):
        s = line.strip()
        if s == "$enddefinitions $end":
            in_defs = False
            continue
        if in_defs:
            continue
        if s.startswith("#"):
            t = int(s[1:])
        elif s and s[0] in "01xzXZ":
            code = s[1:]
            if code in id2sig:
                changes.append((t, id2sig[code], s[0]))
        elif s and s[0] == "b":
            m = re.match(r"b([01xzXZ]+)\s+(\S+)", s)
            if m and m.group(2) in id2sig:
                changes.append((t, id2sig[m.group(2)], m.group(1)))
    return id2sig, widths, changes


def vlit(width, value):
    v = value.replace("X", "x").replace("Z", "z")
    return f"{width}'b{v}"


def main():
    vcd, out_tb = sys.argv[1], sys.argv[2]
    _, widths, changes = parse_vcd(vcd)

    # bucket changes by time
    times = sorted({t for t, _, _ in changes})
    by_time = {t: [] for t in times}
    for t, sig, val in changes:
        by_time[t].append((sig, val))

    L = []
    L.append("`timescale 1ps/1ps")
    L.append("module tb;")
    L.append("  reg clk=0, rst_n=0, enable=0, I=0;")
    L.append("  wire [7:0] O; wire success;")
    L.append("  integer errors=0, checks=0;")
    L.append("  reg [7:0] exp_O; reg exp_success; reg chk_O, chk_success;")
    L.append("  puzzle dut(.clk(clk), .rst_n(rst_n), .enable(enable), .I(I),")
    L.append("             .O(O), .success(success));")
    L.append("  initial begin")
    prev = 0
    for t in times:
        dt = t - prev
        prev = t
        if dt:
            L.append(f"    #{dt};")
        inp_here = False
        for sig, val in by_time[t]:
            if sig in INPUTS:
                L.append(f"    {sig} = {vlit(widths[sig], val)};")
                inp_here = True
        # settle combinational after input/clock edge, then check any
        # recorded outputs at this timestamp
        outs = [(sig, val) for sig, val in by_time[t] if sig in OUTPUTS]
        if outs:
            L.append("    #1;")
            for sig, val in outs:
                if "x" in val.lower() or "z" in val.lower():
                    continue  # don't check undefined recorded values
                lit = vlit(widths[sig], val)
                tgt = "O" if sig == "O" else "success"
                L.append(f"    checks=checks+1; if ({tgt} !== {lit}) begin errors=errors+1;")
                L.append(f"      $display(\"MISMATCH t=%0t {sig}: got %b exp %b\", $time, {tgt}, {lit}); end")
    L.append("    $display(\"RESULT checks=%0d errors=%0d %s\", checks, errors, errors==0?\"PASS\":\"FAIL\");")
    L.append("    $finish;")
    L.append("  end")
    L.append("endmodule")
    open(out_tb, "w").write("\n".join(L) + "\n")
    print(f"wrote {out_tb}: {len(times)} timestamps, "
          f"{sum(1 for c in changes if c[1] in OUTPUTS)} recorded output changes")


if __name__ == "__main__":
    main()
