function x = unraster(v, H, W)
%UNRASTER Inverse of RASTER: a raster-order vector back to an H x W image.
x = reshape(v, W, H).';
end
