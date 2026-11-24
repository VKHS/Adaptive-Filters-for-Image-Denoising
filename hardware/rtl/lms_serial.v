// Serial fixed-point LMS. Low word is tap zero. Return pre-update output.
module lms_serial #(
    parameter W=16, FRAC=12, TAPS=2, MU_SHIFT=6,
    parameter signed [W-1:0] INIT_WEIGHT=0
)(
    input wire clk,rst,in_valid, output wire in_ready,
    input wire signed [W-1:0] in_primary,in_target,
    input wire [TAPS*W-1:0] in_refs,
    input wire in_adapt,in_bypass,
    input wire [1:0] in_mode, // 0 subtract; 1 prediction; 2 gated
    input wire [W-1:0] in_threshold,
    output wire out_valid, input wire out_ready,
    output reg signed [W-1:0] out_data,out_prediction,
    output reg signed [W:0] out_error, output reg out_flag
);
    localparam IDLE=3'd0,DOT=3'd1,DECIDE=3'd2,UPDATE=3'd3,EMIT=3'd4;
    localparam signed [63:0] HI=(64'sd1<<<(W-1))-1, LO=-(64'sd1<<<(W-1));
    reg [2:0] state;
    reg signed [W-1:0] weights[0:TAPS-1];
    reg [TAPS*W-1:0] refs_q;
    reg signed [W-1:0] primary_q,target_q;
    reg adapt_q,bypass_q;
    reg [1:0] mode_q;
    reg [W-1:0] threshold_q;
    integer idx,i;
    reg signed [63:0] acc;
    function signed [W-1:0] sat;
        input signed [63:0] a;
        begin
            if(a>HI) sat=HI[W-1:0];
            else if(a<LO) sat=LO[W-1:0];
            else sat=a[W-1:0];
        end
    endfunction
    wire signed [W-1:0] x=$signed(refs_q[idx*W +: W]);
    wire signed [2*W-1:0] dot_product=weights[idx]*x;
    wire signed [W-1:0] pred=bypass_q ? {W{1'b0}} : sat(acc>>>FRAC);
    wire signed [W:0] error_now=$signed({target_q[W-1],target_q})-$signed({pred[W-1],pred});
    wire [W:0] abs_error=error_now[W]?$unsigned(-error_now):$unsigned(error_now);
    wire flagged=(mode_q==2'd2)&&(abs_error>{1'b0,threshold_q});
    wire signed [63:0] primary_wide={{(64-W){primary_q[W-1]}},primary_q};
    wire signed [63:0] pred_wide={{(64-W){pred[W-1]}},pred};
    wire signed [2*W:0] grad_product=out_error*x;
    wire signed [63:0] grad_wide={{(63-2*W){grad_product[2*W]}},grad_product};
    wire signed [W-1:0] weight_now=weights[idx];
    wire signed [63:0] weight_wide={{(64-W){weight_now[W-1]}},weight_now};
    wire signed [63:0] delta=grad_wide>>>(FRAC+MU_SHIFT);
    assign in_ready=(state==IDLE);
    assign out_valid=(state==EMIT);
    always @(posedge clk) begin
        if(rst) begin
            state<=IDLE; idx<=0; acc<=0; refs_q<=0; primary_q<=0; target_q<=0;
            adapt_q<=0; bypass_q<=0; mode_q<=0; threshold_q<=0;
            out_data<=0; out_prediction<=0; out_error<=0; out_flag<=0;
            for(i=0;i<TAPS;i=i+1) weights[i]<=INIT_WEIGHT;
        end else case(state)
            IDLE: if(in_valid) begin
                refs_q<=in_refs; primary_q<=in_primary; target_q<=in_target;
                adapt_q<=in_adapt; bypass_q<=in_bypass;
                mode_q<=in_mode; threshold_q<=in_threshold;
                acc<=0; idx<=0; state<=DOT;
            end
            DOT: begin
                acc<=acc+dot_product;
                if(idx==TAPS-1) begin idx<=0; state<=DECIDE; end
                else idx<=idx+1;
            end
            DECIDE: begin
                out_prediction<=pred; out_error<=error_now; out_flag<=flagged&&!bypass_q;
                if(bypass_q) out_data<=primary_q;
                else if(mode_q==2'd1) out_data<=pred;
                else if(mode_q==2'd2) out_data<=flagged?pred:primary_q;
                else out_data<=sat(primary_wide-pred_wide);
                idx<=0;
                if(adapt_q&&!bypass_q&&!flagged) state<=UPDATE; else state<=EMIT;
            end
            UPDATE: begin
                weights[idx]<=sat(weight_wide+delta);
                if(idx==TAPS-1) begin idx<=0; state<=EMIT; end else idx<=idx+1;
            end
            EMIT: if(out_ready) state<=IDLE;
            default: state<=IDLE;
        endcase
    end
endmodule
