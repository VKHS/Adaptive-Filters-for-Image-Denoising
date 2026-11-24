// Streaming square-window frontend with line delays and ready/valid flow control.
// Emits only valid interior centres; no synthetic border pixels are produced.
// The first 2R rows overwrite the old line stores before any output is valid.
module window_stream_valid #(parameter W=16,R=2,WIDTH=512,HEIGHT=512,
    SIDE=2*R+1,N=SIDE*SIDE)(
    input wire clk,rst,in_valid,output wire in_ready,
    input wire in_frame_start,input wire signed [W-1:0] in_pixel,
    output reg out_valid,input wire out_ready,
    output reg [N*W-1:0] out_window,
    output wire signed [W-1:0] out_centre,
    output reg [31:0] out_row,out_col
);
    reg signed [W-1:0] lines[0:2*R*WIDTH-1];
    integer row,col,i,j;
    wire [31:0] row_now=in_frame_start?0:row;
    wire [31:0] col_now=in_frame_start?0:col;
    assign in_ready=!out_valid||out_ready;
    assign out_centre=$signed(out_window[(R*SIDE+R)*W +: W]);
    always @(posedge clk) begin
        if(rst) begin
            row<=0; col<=0; out_valid<=0; out_window<=0; out_row<=0; out_col<=0;
        end else if(in_ready) begin
            out_valid<=0;
            if(in_valid) begin
                for(i=2*R-1;i>0;i=i-1) lines[i*WIDTH+col_now]<=lines[(i-1)*WIDTH+col_now];
                lines[col_now]<=in_pixel;
                for(i=0;i<SIDE;i=i+1) begin
                    for(j=0;j<SIDE-1;j=j+1)
                        out_window[(i*SIDE+j)*W +: W]<=col_now==0?{W{1'b0}}:
                            out_window[(i*SIDE+j+1)*W +: W];
                    if(i==SIDE-1) out_window[(i*SIDE+SIDE-1)*W +: W]<=in_pixel;
                    else out_window[(i*SIDE+SIDE-1)*W +: W]<=lines[(SIDE-2-i)*WIDTH+col_now];
                end
                if(row_now>=2*R && col_now>=2*R) begin
                    out_valid<=1; out_row<=row_now-R; out_col<=col_now-R;
                end
                if(col_now==WIDTH-1) begin
                    col<=0; row<=row_now==HEIGHT-1?0:row_now+1;
                end else begin col<=col_now+1; row<=row_now; end
            end
        end
    end
endmodule
