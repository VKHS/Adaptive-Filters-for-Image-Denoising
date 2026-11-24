// A: spatial phase modulo 2**P. Advance only for accepted samples.
module phase_raster #(parameter P=24)(
    input wire clk,rst,advance,frame_start,row_start,
    input wire [P-1:0] step_u,step_v,output wire [P-1:0] phase
);
    reg [P-1:0] row_phase,next_phase;
    assign phase=frame_start?{P{1'b0}}:(row_start?row_phase+step_u:next_phase);
    always @(posedge clk) begin
        if(rst) begin row_phase<=0; next_phase<=0; end
        else if(advance) begin
            if(frame_start) row_phase<=0; else if(row_start) row_phase<=row_phase+step_u;
            next_phase<=phase+step_v;
        end
    end
endmodule
