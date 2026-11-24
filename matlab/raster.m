function v = raster(x)
%RASTER Row-major flattening (row 1 left to right, then row 2, ...), the readout order of a sensor.
v = reshape(x.', [], 1);
end
