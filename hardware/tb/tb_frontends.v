`timescale 1ns/1ps

module tb_frontends;
    reg clk=0; always #5 clk=~clk;
    reg rst=1,advance=0,frame_start=0,row_start=0,update_clean=0;
    reg [3:0] phase_sel;
    wire signed [15:0] cos_ref,sin_ref;
    reg [255:0] ob;
    wire signed [15:0] ob_mean;
    wire [7:0] phase;
    reg signed [16:0] error_code=0;
    wire [15:0] threshold;
    quadrature_lut_q12 lut(.phase(phase_sel),.cos_ref(cos_ref),.sin_ref(sin_ref));
    ob_mean_pow2 avg(.in_samples(ob),.out_mean(ob_mean));
    phase_raster #(.P(8)) raster(.clk(clk),.rst(rst),.advance(advance),
        .frame_start(frame_start),.row_start(row_start),.step_u(8'd64),.step_v(8'd16),.phase(phase));
    robust_threshold robust(.clk(clk),.rst(rst),.update_clean(update_clean),.error_code(error_code),.threshold(threshold));
    task expect_phase;
        input [7:0] val;
        begin #1; if(phase!==val) $fatal(1,"phase expected %0d got %0d",val,phase);
            @(posedge clk); #1; @(negedge clk); end
    endtask
    initial begin
        phase_sel=0; ob={16{16'hfe00}}; #1;
        if(cos_ref!==16'sd4096 || sin_ref!==16'sd0 || ob_mean!==-16'sd512) $fatal(1,"LUT/OB");
        phase_sel=4; #1; if(cos_ref!==16'sd0 || sin_ref!==16'sd4096) $fatal(1,"quadrature");
        phase_sel=12; #1; if(cos_ref!==16'sd0 || sin_ref!==-16'sd4096) $fatal(1,"negative sine");
        repeat(2) @(posedge clk); @(negedge clk); rst=0; advance=1; frame_start=1;
        expect_phase(0); frame_start=0; expect_phase(16); expect_phase(32);
        advance=0; expect_phase(48); expect_phase(48);
        advance=1; row_start=1; expect_phase(64); row_start=0; expect_phase(80);
        if(threshold!==16'd820) $fatal(1,"initial threshold");
        advance=0; error_code=17'sd1024; update_clean=1;
        @(posedge clk); #1;
        if(threshold!==16'd860) $fatal(1,"robust threshold update");
        @(negedge clk); update_clean=0;
        repeat(2) @(posedge clk); #1;
        if(threshold!==16'd860) $fatal(1,"robust threshold hold");
        $display("PASS frontends: phase, quadrature, optical-black mean, robust threshold"); $finish;
    end
    initial begin #10000; $fatal(1,"frontend watchdog"); end
endmodule
