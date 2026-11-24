`timescale 1ns/1ps

module tb_d;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1,in_valid=0,out_ready=0;
    wire in_ready,out_valid;
    reg signed [15:0] d,target,prev,slow;
    reg adapt,gate,row_start;
    reg [15:0] threshold;
    reg [399:0] refs;
    wire signed [15:0] out_data,out_prediction;
    wire signed [16:0] out_error;
    wire out_flag;
    
    scenario_d_self_tuning #(.MU_SHIFT(5),.INIT_WEIGHT(16'sd170)) dut(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_ready(in_ready),
        .in_primary(d),.in_window(refs),.in_adapt(adapt),.in_gate(gate),.in_threshold(threshold),
        .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_prediction(out_prediction),.out_error(out_error),.out_flag(out_flag));
    integer fd,rc,n=0,wait_cycles,j;
    integer vi_d,vi_t,vi_p,vi_s,vi_a,vi_g,vi_r,vi_th,ex_d,ex_y,ex_e,ex_f;
    reg [399:0] vec;
    task check_output;
        begin
            if(out_valid!==1'b1 || $signed(out_data)!==ex_d ||
                $signed(out_prediction)!==ex_y || $signed(out_error)!==ex_e ||
                out_flag!==(ex_f!=0))
                $fatal(1,"D transaction %0d got %0d %0d %0d %0d expected %0d %0d %0d %0d",
                    n,$signed(out_data),$signed(out_prediction),$signed(out_error),out_flag,ex_d,ex_y,ex_e,ex_f);
        end
    endtask
    initial begin
        repeat(3) @(posedge clk);
        @(negedge clk); rst=0;
        fd=$fopen("hardware/vectors/d.txt","r");
        if(!fd) $fatal(1,"cannot open vector file");
        while(!$feof(fd)) begin
            rc=$fscanf(fd,"%d %d %d %d %d %d %d %d %h %d %d %d %d\n",
                vi_d,vi_t,vi_p,vi_s,vi_a,vi_g,vi_r,vi_th,vec,ex_d,ex_y,ex_e,ex_f);
            if(rc!=13) begin
                if(rc!=-1) $fatal(1,"malformed vector %0d fields=%0d",n,rc);
            end else begin
                @(negedge clk);
                if(in_ready!==1'b1) $fatal(1,"expected idle before input");
                d=vi_d; target=vi_t; prev=vi_p; slow=vi_s;
                adapt=vi_a; gate=vi_g; row_start=vi_r; threshold=vi_th; refs=vec;
                in_valid=1;
                @(posedge clk); #1;
                @(negedge clk); in_valid=0;
                wait_cycles=0;
                while(out_valid!==1'b1) begin
                    @(negedge clk); wait_cycles=wait_cycles+1;
                    if(wait_cycles>512) $fatal(1,"response timeout");
                end
                check_output;
                for(j=0;j<(n%3)+1;j=j+1) begin
                    @(negedge clk); check_output;
                    if(in_ready!==1'b0) $fatal(1,"input accepted with stalled output");
                end
                out_ready=1;
                @(posedge clk); #1;
                @(negedge clk); out_ready=0;
                n=n+1;
            end
        end
        $fclose(fd);
        if(n!=40) $fatal(1,"wrong transaction count %0d",n);
        @(negedge clk); rst=1; @(posedge clk); #1;
        if(out_valid!==1'b0 || in_ready!==1'b1) $fatal(1,"reset contract");
        $display("PASS scenario D: %0d bit-exact transactions including backpressure/reset",n);
        $finish;
    end
    initial begin #20000000; $fatal(1,"global watchdog"); end
endmodule
