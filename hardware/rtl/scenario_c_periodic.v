module scenario_c_periodic #(parameter W=16,FRAC=12,TAPS=128,DELAY=8,MU_SHIFT=10)(
    input wire clk,rst,in_valid, output wire in_ready,
    input wire signed [W-1:0] in_primary,in_highband,
    input wire in_adapt,in_row_start,
    output wire out_valid, input wire out_ready,
    output wire signed [W-1:0] out_data,out_prediction,
    output wire signed [W:0] out_error, output wire out_flag
);
    // External high-band splitter. Row-local causal warm-up bypasses the FIR.
    localparam HIST=DELAY+TAPS-1;
    reg signed [W-1:0] history[0:HIST-1];
    integer fill,i;
    wire [TAPS*W-1:0] refs;
    wire bypass=in_row_start||(fill<HIST);
    genvar t;
    generate for(t=0;t<TAPS;t=t+1) begin: tap
        assign refs[t*W +: W]=history[DELAY-1+t];
    end endgenerate
    always @(posedge clk) begin
        if(rst) begin
            fill<=0;
            for(i=0;i<HIST;i=i+1) history[i]<=0;
        end else if(in_valid&&in_ready) begin
            if(in_row_start) begin
                for(i=1;i<HIST;i=i+1) history[i]<=0;
                fill<=1;
            end else begin
                for(i=1;i<HIST;i=i+1) history[i]<=history[i-1];
                if(fill<HIST) fill<=fill+1;
            end
            history[0]<=in_highband;
        end
    end
    lms_serial #(.W(W),.FRAC(FRAC),.TAPS(TAPS),.MU_SHIFT(MU_SHIFT),.INIT_WEIGHT(0)) core(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),
        .in_primary(in_primary),.in_target(in_highband),.in_refs(refs),
        .in_adapt(in_adapt),.in_bypass(bypass),.in_mode(2'd0),.in_threshold({W{1'b0}}),
        .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
        .out_prediction(out_prediction),.out_error(out_error),.out_flag(out_flag));
endmodule
