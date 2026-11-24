"""Scenario D: adaptive self-tuning filter - the delayed-reference structure with the *filter output* kept.

Same wiring as scenario C (the primary, delayed, is the reference), but the output is the filter output y,
not the error. The filter can only reproduce what is predictable across the delay; when the wanted signal is
the predictable (narrowband, correlated) part and the noise is broadband, y is the cleaned signal. The filter
tunes itself to the signal without being told where it is.

Image form: the delay becomes a blind spot. Pixel (i, j) is predicted from its (2r+1) x (2r+1) neighbourhood
without the pixel itself; the image is predictable from its neighbours, white noise is not. See
``predictor.blindspot_lms``.

For sparse noise (salt and pepper, impulses, bursts) the error output is a detector: it is small on clean
pixels and large on corrupted ones. ``self_tuning_gated`` keeps the primary where the error is small,
substitutes the filter output where it is large, and adapts only on clean pixels.
"""
from .predictor import blindspot_lms, blindspot_gated, tap_mask  # noqa: F401


def self_tuning(img, r=2, alpha=0.01, passes=2, record=False):
    """Blind-spot LMS predictor with a single-pixel blind spot. Returns the filter output."""
    return blindspot_lms(img, r=r, hole=0, alpha=alpha, passes=passes, record=record)


def self_tuning_gated(img, r=2, alpha=0.01, k=4.0, passes=3):
    """Error-gated version for sparse noise. Returns (output, mask of replaced pixels)."""
    return blindspot_gated(img, r=r, alpha=alpha, k=k, passes=passes)
