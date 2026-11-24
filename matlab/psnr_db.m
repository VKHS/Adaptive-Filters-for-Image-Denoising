function p = psnr_db(ref, est)
%PSNR_DB Peak signal-to-noise ratio in dB for images in [0, 1]; the estimate is clipped to [0, 1] first.
est = min(max(est, 0), 1);
p = 10 * log10(1 / mean((ref(:) - est(:)).^2));
end
