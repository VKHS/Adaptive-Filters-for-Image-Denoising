// F: mean of power-of-two signed optical-black samples.
module ob_mean_pow2 #(parameter W=16,LOG_N=4,N=(1<<LOG_N))(
    input wire [N*W-1:0] in_samples,output wire signed [W-1:0] out_mean
);
    integer j;
    reg signed [W+LOG_N-1:0] total;
    always @* begin
        total=0;
        for(j=0;j<N;j=j+1) total=total+$signed(in_samples[j*W +: W]);
    end
    assign out_mean=total>>>LOG_N;
endmodule
