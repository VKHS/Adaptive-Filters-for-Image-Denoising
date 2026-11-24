module scenario_e_line_enhancer #(parameter W=16,FRAC=12,R=3,H=0,MU_SHIFT=9,
    parameter N=(2*R+1)*(2*R+1),TAPS=N-(2*H+1)*(2*H+1))(
    input wire clk,rst,in_valid, output wire in_ready,
    input wire signed [W-1:0] in_primary,
    input wire [N*W-1:0] in_window,input wire in_adapt,
    output wire out_valid, input wire out_ready,
    output wire signed [W-1:0] out_data,out_prediction,
    output wire signed [W:0] out_error, output wire out_flag
);
    // E: centred target. Choose hole radius from calibration before elaboration.
    wire [TAPS*W-1:0] refs;
    window_taps #(.W(W),.R(R),.H(H),.N(N),.TAPS(TAPS)) mask(
        .in_window(in_window),.out_taps(refs));
    lms_serial #(.W(W),.FRAC(FRAC),.TAPS(TAPS),.MU_SHIFT(MU_SHIFT),.INIT_WEIGHT(0)) core(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),
        .in_primary(in_primary),.in_target(in_primary),.in_refs(refs),
        .in_adapt(in_adapt),.in_bypass(1'b0),.in_mode(2'd1),.in_threshold({W{1'b0}}),
        .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
        .out_prediction(out_prediction),.out_error(out_error),.out_flag(out_flag));
endmodule
