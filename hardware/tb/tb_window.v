`timescale 1ns/1ps

module tb_window;
    reg clk=0; always #5 clk=~clk;
    reg rst=1,in_valid=0,frame_start=0,out_ready=0;
    reg signed [15:0] pixel;
    wire in_ready,out_valid;
    wire [143:0] window;
    wire signed [15:0] centre;
    wire [31:0] row,col;
    integer i,j,r,c,frame,expected,count=0;
    window_stream_valid #(.R(1),.WIDTH(7),.HEIGHT(6)) dut(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),
        .in_frame_start(frame_start),.in_pixel(pixel),.out_valid(out_valid),
        .out_ready(out_ready),.out_window(window),.out_centre(centre),
        .out_row(row),.out_col(col));
    initial begin
        repeat(2) @(posedge clk); @(negedge clk); rst=0;
        for(frame=0;frame<2;frame=frame+1) begin
            for(r=0;r<6;r=r+1) for(c=0;c<7;c=c+1) begin
                @(negedge clk);
                if(in_ready!==1'b1) $fatal(1,"window not ready");
                in_valid=1; frame_start=(r==0 && c==0); pixel=frame*1000+r*100+c;
                @(posedge clk); #1;
                @(negedge clk); in_valid=0; frame_start=0;
                if(r>=2&&c>=2) begin
                    if(out_valid!==1'b1||row!==r-1||col!==c-1||
                        $signed(centre)!==(frame*1000+(r-1)*100+c-1))
                        $fatal(1,"window coordinate/centre failure");
                    for(i=0;i<3;i=i+1) for(j=0;j<3;j=j+1) begin
                        expected=frame*1000+(r-2+i)*100+c-2+j;
                        if($signed(window[(i*3+j)*16 +: 16])!==expected)
                            $fatal(1,"window frame %0d row %0d col %0d tap %0d,%0d",frame,r,c,i,j);
                    end
                    @(negedge clk);
                    if(in_ready!==1'b0 || out_valid!==1'b1) $fatal(1,"window backpressure");
                    out_ready=1; @(posedge clk); #1; @(negedge clk); out_ready=0;
                    count=count+1;
                end else if(out_valid!==1'b0) $fatal(1,"premature border output");
            end
        end
        if(count!=40) $fatal(1,"wrong window count");
        $display("PASS window frontend: 40 interior windows over two frames"); $finish;
    end
    initial begin #100000; $fatal(1,"window watchdog"); end
endmodule
