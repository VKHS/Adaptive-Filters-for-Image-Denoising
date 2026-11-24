function root = adf_setup()
%ADF_SETUP Return the repository root and make sure this folder is on the path.
%   root = adf_setup() is called by the demo scripts. All functions live in this one folder and use base
%   MATLAB only (no toolboxes): filtering, padding, Poisson sampling and SSIM are written out explicitly.
here = fileparts(mfilename('fullpath'));
addpath(here);
root = fileparts(here);
end
