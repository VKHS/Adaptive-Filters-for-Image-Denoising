"""Scenario F: cancelling interference picked up by a dedicated reference sensor.

In the antenna version the reference element is steered at the interferer, so it receives the interference
but (almost) none of the wanted signal. The canceller filters the reference and subtracts it from the primary.
With uncorrelated noise in both inputs, the converged (Wiener) canceller leaves

    output noise = S_nn [ R_prin + R_refn / (1 + R_refn) ]

where S_nn is the interference power in the primary, R_prin the ratio of uncorrelated to correlated noise
in the primary and R_refn the same ratio in the reference. The noise reduction is therefore

    NR = (1 + R_prin) / (R_prin + R_refn / (1 + R_refn)).

Image sensors carry such references:

* optical-black (masked) columns: they see the row offset of their row but no light -> row banding
  (``train_row_weight`` / ``row_reference_canceller``). The reference is one number per row, so adapting
  on scene pixels fails (the scene's row means swamp the update); the weight is trained on a dark frame or
  adapted only while the optical-black pixels are read (``row_reference_online``).
* a reference output channel read at the same instants as the pixels: it sees the switching of the shared
  amplifier -> readout telegraph noise (``channel_reference_canceller``). The reference changes from pixel
  to pixel and is independent of the scene, so the classic online canceller works.
"""
import numpy as np


def noise_reduction_theory(R_prin, R_refn):
    """Noise-power reduction factor of the converged two-input canceller (linear, not dB)."""
    return (1.0 + R_prin) / (R_prin + R_refn / (1.0 + R_refn))


def train_row_weight(dark, dark_ob, mu2=0.5, passes=3):
    """LMS on a dark frame: d = dark pixel, x = mean of that row's optical-black pixels. Returns w."""
    H, W = dark.shape
    xr = dark_ob.mean(axis=1)
    w = 0.0
    for _ in range(passes):
        for i in range(H):
            x = float(xr[i])
            row = dark[i]
            for j in range(W):
                w += mu2 * (row[j] - w * x) * x
    return w


def row_reference_canceller(y, ob, w):
    """Subtract w times the optical-black row mean from every pixel of the row."""
    return y - w * ob.mean(axis=1, keepdims=True)


def row_reference_online(y, ob, mu2=0.5, mode="ob_gated"):
    """Online variants, for comparison.

    mode = "scene"   : adapt on every scene pixel (d = pixel, x = optical-black row mean). Fails: the
                       scene's row means act as huge noise in the update.
    mode = "ob_gated": adapt only on the optical-black pixels, each predicted from the mean of the other
                       optical-black pixels of its row (leave one out), then correct the scene pixels.
    Returns (output, final weight).
    """
    H, W = y.shape
    K = ob.shape[1]
    out = np.empty_like(y)
    w = 0.0
    for i in range(H):
        xr = float(ob[i].mean())
        if mode == "ob_gated":
            s = float(ob[i].sum())
            for k in range(K):
                xk = (s - ob[i, k]) / (K - 1)
                w += mu2 * (ob[i, k] - w * xk) * xk
            out[i] = y[i] - w * xr
        else:
            row = y[i]
            o = out[i]
            for j in range(W):
                e = row[j] - w * xr
                o[j] = e
                w += mu2 * e * xr
    return out, w


def channel_reference_canceller(y, ref, L=1, alpha=1e-3, train=None, online_alpha=1e-4):
    """Canceller with a concurrent reference channel, in raster order.

    x(n) = [ref(n), ref(n-1), ..., ref(n-L+1)],  output e(n) = y(n) - w.x(n).

    With ``train = (dark, dark_ref)`` the weights are adapted on a dark frame (no scene, so the only
    uncorrelated input is read noise and the weights settle fast and accurately) and then frozen for the
    scene: this is the default. Without it the weights adapt online on the scene. Online, the scene acts as
    a strong uncorrelated "signal" in the LMS gradient (its power is many times the interference power), so
    the step must be tiny (``online_alpha``) and the row mean of the primary is removed from the error that
    drives the update. alpha is the normalised step mu2 * L * var(ref).
    Returns (output, final weights).
    """
    def taps(r):
        p = np.concatenate([np.zeros(L - 1), r.ravel()])
        return np.lib.stride_tricks.sliding_window_view(p, L)[:, ::-1]

    def run(d_img, r_img, w, a, adapt, demean):
        X = taps(r_img)
        d = d_img.ravel()
        dm = (d_img - d_img.mean(axis=1, keepdims=True)).ravel() if demean else d
        mu2 = a / (L * float(np.var(r_img)))
        out = np.empty(d.size)
        for t in range(d.size):
            x = X[t]
            yv = w @ x
            out[t] = d[t] - yv
            if adapt:
                w += (mu2 * (dm[t] - yv)) * x
        return out.reshape(d_img.shape), w

    w = np.zeros(L)
    if train is not None:
        _, w = run(train[0], train[1], w, alpha, adapt=True, demean=False)
        out, _ = run(y, ref, w, alpha, adapt=False, demean=False)
        return out, w
    return run(y, ref, w, online_alpha, adapt=True, demean=True)
