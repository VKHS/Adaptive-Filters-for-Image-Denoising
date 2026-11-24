// A: 16-bin, unit-amplitude signed Q12 cosine and sine.
module quadrature_lut_q12(input wire [3:0] phase,output wire signed [15:0] cos_ref,sin_ref);
    function signed [15:0] sin_q12;
        input [3:0] p;
        begin case(p)
            4'd0: sin_q12=16'sd0;
            4'd1: sin_q12=16'sd1567;
            4'd2: sin_q12=16'sd2896;
            4'd3: sin_q12=16'sd3784;
            4'd4: sin_q12=16'sd4096;
            4'd5: sin_q12=16'sd3784;
            4'd6: sin_q12=16'sd2896;
            4'd7: sin_q12=16'sd1567;
            4'd8: sin_q12=16'sd0;
            4'd9: sin_q12=-16'sd1567;
            4'd10: sin_q12=-16'sd2896;
            4'd11: sin_q12=-16'sd3784;
            4'd12: sin_q12=-16'sd4096;
            4'd13: sin_q12=-16'sd3784;
            4'd14: sin_q12=-16'sd2896;
            4'd15: sin_q12=-16'sd1567;
            default: sin_q12=0;
        endcase end
    endfunction
    wire [3:0] cphase=phase+4'd4;
    assign sin_ref=sin_q12(phase);
    assign cos_ref=sin_q12(cphase);
endmodule
