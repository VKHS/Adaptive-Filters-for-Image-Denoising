# Image-stream integration and memory planning

[Hardware overview](../README.md)

## Transaction protocol

A transfer occurs on a rising edge with valid and ready high. A synchronous active-high reset clears the adaptive weights to the configured initial value, clears output valid and discards any in-flight transaction. Do not reset F between calibration and inference. A/C/D/E/F hold outputs stable until out_ready is high; while busy they accept no next transaction. B and window_stream_valid use one-entry elastic outputs, so they can consume a replacement input on the same edge as an output handshake.

Pack each signed W-bit word with tap zero at bits W−1:0, then tap one at 2W−1:W. Spatial windows are top-left to bottom-right in row-major order; for radius R the centre index is R(2R+1)+R. The target sample and control flags must align with the window centre, not the newest arriving pixel. Convert intensities to signed fixed point after centring when required; restore mean externally.

## Spatial frontend

[window_stream_valid](../rtl/window_stream_valid.v) receives scalar raster samples and emits square windows and centre coordinates. Parameter WIDTH/HEIGHT must exceed 2R, and R≥1. Assert in_frame_start with the first accepted pixel; send exactly WIDTH × HEIGHT row-major samples per frame. Old line-store contents are overwritten during warm-up. It uses 2R × WIDTH × W bits of line history plus a (2R+1)² × W register window. No border outputs are produced. For a 512 × 512 image, R=2 requires 32,768 history bits plus 400 window bits; R=4 requires 65,536 plus 1,296 bits at W=16. Actual RAM inference is device/tool dependent; the simple RTL uses explicit indexed arrays and may infer registers. For board deployment add a vendor RAM implementation, reflection padding or a separate border policy, frame metadata and a scheduling controller.

Connect out_window/out_centre to D/E input, valid to in_valid and D/E in_ready to out_ready. The window frontend will stall while the serial LMS is busy. If an external camera cannot stop, use an appropriately sized FIFO or a frame-buffer/DMA interface; the current design is not guaranteed to sustain continuous video.

## Scenario-specific scheduling

| Scenario | External system responsibilities |
|---|---|
| A | Spectral peak discovery, frequency-to-phase increment quantisation, image centring and optional raster-phase LUT expansion |
| B | Previous preliminary corrected row, row replay and full offset sequence for Gaussian slow-offset restoration; row 0 bypass |
| C | 33-pixel horizontal windows, Gaussian high-band alignment, row-start markers, reflected or valid boundary policy |
| D | Centring, window construction, threshold controller, repeated-pass frame storage; original target retained for Dg |
| E | Correlation calibration, select R/H, centred window, repeated-pass storage |
| F | Dark/scene phase controller, synchronized optical-black or reference-output samples, reference-tap alignment |

## FPGA development roadmap

1. Verify the default top and chosen parameter set with simulation and generic synthesis.
2. Add target-specific clock/reset constraints, registered memory interfaces and AXI-stream wrappers. Use the chosen device part, not an assumed FPGA.
3. Replace wide dynamic vector multiplexers and coefficient arrays with banked memory where beneficial. A lane-parallel LMS must preserve update order or document altered adaptation.
4. Quantise the original software stimuli, compare output against a fixed-point model, and run a precision/step-size sweep before attempting image-quality claims.
5. Perform post-synthesis/post-route timing and resource evaluation, then board-level PSNR/SSIM and throughput measurements. Do not infer those from smoke vectors.

No clock frequency, LUT/DSP/BRAM usage, energy or FPGA deployment has been measured here.
