// C optional horizontal Gaussian high-band frontend: sigma=4 px, radius=16.
// Supply 33 aligned, row-major signed Q12 samples; boundaries supplied by caller.
// Integer coefficients sum to 4096 exactly; this approximates the software Gaussian.
module gaussian_highband_q12(
    input wire [527:0] in_row_window,
    output wire signed [15:0] out_primary,out_lowband,out_highband
);
    function signed [15:0] coef;
        input integer j;
        begin case(j)
            0: coef=16'sd0;
            1: coef=16'sd0;
            2: coef=16'sd1;
            3: coef=16'sd2;
            4: coef=16'sd5;
            5: coef=16'sd9;
            6: coef=16'sd18;
            7: coef=16'sd33;
            8: coef=16'sd55;
            9: coef=16'sd88;
            10: coef=16'sd133;
            11: coef=16'sd187;
            12: coef=16'sd248;
            13: coef=16'sd308;
            14: coef=16'sd361;
            15: coef=16'sd396;
            16: coef=16'sd408;
            17: coef=16'sd396;
            18: coef=16'sd361;
            19: coef=16'sd308;
            20: coef=16'sd248;
            21: coef=16'sd187;
            22: coef=16'sd133;
            23: coef=16'sd88;
            24: coef=16'sd55;
            25: coef=16'sd33;
            26: coef=16'sd18;
            27: coef=16'sd9;
            28: coef=16'sd5;
            29: coef=16'sd2;
            30: coef=16'sd1;
            31: coef=16'sd0;
            32: coef=16'sd0;
            default: coef=0;
        endcase end
    endfunction
    function signed [15:0] sat;
        input signed [63:0] a;
        begin
            if(a>32767) sat=16'sh7fff;
            else if(a< -32768) sat=16'sh8000;
            else sat=a[15:0];
        end
    endfunction
    integer j;
    reg signed [63:0] sum;
    reg signed [31:0] product;
    reg signed [15:0] sample;
    always @* begin
        sum=0;
        for(j=0;j<33;j=j+1) begin
            sample=$signed(in_row_window[j*16 +: 16]);
            product=sample*coef(j);
            sum=sum+product;
        end
    end
    assign out_primary=$signed(in_row_window[256 +: 16]);
    assign out_lowband=sat(sum>>>12);
    wire signed [63:0] p={{48{out_primary[15]}},out_primary};
    wire signed [63:0] low={{48{out_lowband[15]}},out_lowband};
    assign out_highband=sat(p-low);
endmodule
