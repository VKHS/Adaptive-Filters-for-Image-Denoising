// Dg: approximate robust scale EMA; update only on completed accepted-clean samples.
module robust_threshold #(parameter W=16,INITIAL_SCALE=205,SHIFT=7,K=4)(
    input wire clk,rst,update_clean,input wire signed [W:0] error_code,
    output wire [W-1:0] threshold
);
    localparam signed [63:0] MAX=(64'sd1<<<W)-1;
    reg signed [63:0] scale;
    wire [W:0] absolute=error_code[W]?$unsigned(-error_code):$unsigned(error_code);
    wire signed [63:0] mag=$signed({1'b0,absolute});
    wire signed [63:0] next_scale=scale+(((mag+(mag>>>1))-scale)>>>SHIFT);
    wire signed [63:0] th=K*scale;
    assign threshold=th>MAX?{W{1'b1}}:th[W-1:0];
    always @(posedge clk) begin
        if(rst) scale<=INITIAL_SCALE;
        else if(update_clean) begin
            if(next_scale<1) scale<=1; else if(next_scale>MAX) scale<=MAX; else scale<=next_scale;
        end
    end
endmodule
