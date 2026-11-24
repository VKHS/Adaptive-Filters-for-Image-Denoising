// Sign-error constant-reference estimator and two-phase row replay.
module scenario_b_bias #(parameter W=16,FRAC=12,MU_SHIFT=8)(
    input wire clk,rst,in_valid, output wire in_ready,
    input wire signed [W-1:0] in_primary,in_previous,in_slow_offset,
    input wire in_estimate,in_row_start,
    output reg out_valid, input wire out_ready,
    output reg signed [W-1:0] out_data,out_bias, output reg out_applied
);
    localparam signed [63:0] HI=(64'sd1<<<(W-1))-1,LO=-(64'sd1<<<(W-1));
    localparam signed [63:0] STEP=(64'sd1<<<(FRAC-MU_SHIFT));
    reg signed [W-1:0] bias;
    function signed [W-1:0] sat;
        input signed [63:0] a;
        begin
            if(a>HI) sat=HI[W-1:0]; else if(a<LO) sat=LO[W-1:0]; else sat=a[W-1:0];
        end
    endfunction
    wire signed [63:0] d={{(64-W){in_primary[W-1]}},in_primary};
    wire signed [63:0] prev={{(64-W){in_previous[W-1]}},in_previous};
    wire signed [63:0] slow={{(64-W){in_slow_offset[W-1]}},in_slow_offset};
    wire signed [63:0] b=in_row_start?64'sd0:$signed({{(64-W){bias[W-1]}},bias});
    wire signed [63:0] e=d-prev-b;
    wire signed [W-1:0] next_bias=sat(b+((e>0)?STEP:((e<0)?-STEP:64'sd0)));
    assign in_ready=!out_valid||out_ready;
    always @(posedge clk) begin
        if(rst) begin bias<=0; out_valid<=0; out_data<=0; out_bias<=0; out_applied<=0; end
        else if(in_ready) begin
            out_valid<=in_valid;
            if(in_valid) begin
                out_applied<=!in_estimate;
                if(in_estimate) begin bias<=next_bias; out_bias<=next_bias; out_data<=in_primary; end
                else begin bias<=sat(b); out_bias<=sat(b); out_data<=sat(d-b+slow); end
            end
        end
    end
endmodule
