function p = offset_aligned_psnr(ref, est)
%OFFSET_ALIGNED_PSNR PSNR after removing the global mean error (a drift canceller cannot know the level).
e = est - ref;
e = e - mean(e(:));
p = 10 * log10(1 / mean(e(:).^2));
end
