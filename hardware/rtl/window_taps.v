// Compile-time row-major spatial tap selector. No target/hole samples enter the MAC.
module window_taps #(parameter W=16,R=2,H=0,N=(2*R+1)*(2*R+1),
    TAPS=N-(2*H+1)*(2*H+1))(
    input wire [N*W-1:0] in_window, output wire [TAPS*W-1:0] out_taps
);
    function integer rank_before;
        input integer p;
        integer k,a,b;
        begin
            rank_before=0;
            for(k=0;k<p;k=k+1) begin
                a=k/(2*R+1)-R; b=k%(2*R+1)-R;
                if(a< -H||a>H||b< -H||b>H) rank_before=rank_before+1;
            end
        end
    endfunction
    genvar j;
    generate for(j=0;j<N;j=j+1) begin: pixel
        localparam A=j/(2*R+1)-R, B=j%(2*R+1)-R;
        if(A< -H||A>H||B< -H||B>H) begin: kept
            localparam K=rank_before(j);
            assign out_taps[K*W +: W]=in_window[j*W +: W];
        end
    end endgenerate
endmodule
