# Test image

`camera.png` (512 x 512, 8-bit gray) is the default test image. It carries no copyright restrictions (CC0).

To run everything on another image, put it here as `lena.png` (also accepted: `lena.tif`, `lena.bmp`,
`lena.jpg`, `lenna.png`, `lena512.bmp`). Both the Python and the MATLAB code then use it instead of
`camera.png`. Color images are converted to gray with the BT.601 weights (0.2989, 0.5870, 0.1140), and other
sizes are resized to 512 x 512. Then regenerate the results and figures:

```bash
cd python
python run_benchmark.py
python make_figures.py
```
