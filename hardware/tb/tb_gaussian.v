`timescale 1ns/1ps

module tb_gaussian;
    reg [527:0] x;
    wire signed [15:0] p,l,h;
    gaussian_highband_q12 dut(.in_row_window(x),.out_primary(p),.out_lowband(l),.out_highband(h));
    initial begin
        x={33{16'hfe00}}; #1;
        if(p!==-16'sd512||l!==-16'sd512||h!==16'sd0) $fatal(1,"DC preservation");
        x=0; x[256 +:16]=16'sd4096; #1;
        if(p!==16'sd4096||l!==16'sd408||h!==16'sd3688) $fatal(1,"impulse response");
        $display("PASS Gaussian high-band frontend: DC and centre impulse"); $finish;
    end
endmodule
