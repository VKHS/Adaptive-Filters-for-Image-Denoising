module scenario_f_reference #(parameter W=16,FRAC=12,TAPS=1,MU_SHIFT=6)(
    input wire clk,rst,in_valid, output wire in_ready,
    input wire signed [W-1:0] in_primary,
    input wire [TAPS*W-1:0] in_reference,input wire in_adapt,
    output wire out_valid, input wire out_ready,
    output wire signed [W-1:0] out_data,out_prediction,
    output wire signed [W:0] out_error, output wire out_flag
);
    // F: calibrate using dark frames (adapt=1), then freeze on scene (adapt=0).
    lms_serial #(.W(W),.FRAC(FRAC),.TAPS(TAPS),.MU_SHIFT(MU_SHIFT),.INIT_WEIGHT(0)) core(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),
        .in_primary(in_primary),.in_target(in_primary),.in_refs(in_reference),
        .in_adapt(in_adapt),.in_bypass(1'b0),.in_mode(2'd0),.in_threshold({W{1'b0}}),
        .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
        .out_prediction(out_prediction),.out_error(out_error),.out_flag(out_flag));
endmodule
