function out = median3(img)
%MEDIAN3 3 x 3 median filter (mirror boundary).
out = median(neighbourhood_stack(img, 3), 3);
end
