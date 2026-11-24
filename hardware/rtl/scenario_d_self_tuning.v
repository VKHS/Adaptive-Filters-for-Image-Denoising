module scenario_d_self_tuning #(parameter W=16,FRAC=12,R=2,MU_SHIFT=8,
    parameter signed [W-1:0] INIT_WEIGHT=0,
    parameter N=(2*R+1)*(2*R+1),TAPS=N-1)(
    input wire clk,rst,in_valid, output wire in_ready,
    input wire signed [W-1:0] in_primary,
    input wire [N*W-1:0] in_window,
    input wire in_adapt,in_gate,input wire [W-1:0] in_threshold,
    output wire out_valid, input wire out_ready,
    output wire signed [W-1:0] out_data,out_prediction,
    output wire signed [W:0] out_error, output wire out_flag
);
    // D: centred target. Use uniform INIT_WEIGHT for gated variant.
    wire [TAPS*W-1:0] refs;
    window_taps #(.W(W),.R(R),.H(0),.N(N),.TAPS(TAPS)) mask(
        .in_window(in_window),.out_taps(refs));
    lms_serial #(.W(W),.FRAC(FRAC),.TAPS(TAPS),.MU_SHIFT(MU_SHIFT),.INIT_WEIGHT(INIT_WEIGHT)) core(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),
        .in_primary(in_primary),.in_target(in_primary),.in_refs(refs),
        .in_adapt(in_adapt),.in_bypass(1'b0),.in_mode(in_gate?2'd2:2'd1),.in_threshold(in_threshold),
        .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
        .out_prediction(out_prediction),.out_error(out_error),.out_flag(out_flag));
endmodule
