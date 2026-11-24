function [x, name] = load_test_image(path, sz)
%LOAD_TEST_IMAGE Test image as a sz x sz double in [0, 1] (default 512).
%   Without a path it uses data/lena.png (or another common Lena file name) when present, otherwise
%   data/camera.png. RGB is converted with the BT.601 weights 0.2989, 0.5870, 0.1140.
root = adf_setup();
if nargin < 2
    sz = 512;
end
if nargin < 1 || isempty(path)
    names = {'lena.png', 'lena.tif', 'lena.tiff', 'lena.bmp', 'lena.jpg', 'lenna.png', 'Lenna.png', 'lena512.bmp'};
    path = fullfile(root, 'data', 'camera.png');
    for k = 1:numel(names)
        p = fullfile(root, 'data', names{k});
        if exist(p, 'file')
            path = p;
            break
        end
    end
end
[~, name] = fileparts(path);
img = imread(path);
if isa(img, 'uint8')
    img = double(img) / 255;
elseif isa(img, 'uint16')
    img = double(img) / 65535;
else
    img = double(img);
    if max(img(:)) > 1
        img = img / 255;
    end
end
if ndims(img) == 3
    img = 0.2989 * img(:, :, 1) + 0.5870 * img(:, :, 2) + 0.1140 * img(:, :, 3);
end
if any(size(img) ~= [sz sz])
    [H, W] = size(img);
    [Xq, Yq] = meshgrid(linspace(1, W, sz), linspace(1, H, sz));
    img = interp2(img, Xq, Yq, 'cubic');
end
x = min(max(img, 0), 1);
end
