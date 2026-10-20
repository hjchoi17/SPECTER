"""SPECTER RF trace extraction.

Reads an interleaved 8-bit I/Q capture, applies an STFT, and plots the
normalized magnitude of the zero-frequency bin over time (Eq. 1 in the paper).
This script only extracts and visualizes the trace. It does not perform frame
synchronization, threshold selection, or bit decisions.
"""

import argparse
import sys

import numpy as np
import matplotlib
from scipy import signal

TRIM = 20  # frames dropped at each end


def get_sig(filename, dtype):
    iq = np.fromfile(filename, dtype=dtype)
    if iq.size % 2:
        print("warning: odd number of samples, dropping the last byte", file=sys.stderr)
        iq = iq[:-1]
    iq = iq.astype(np.float64)
    return iq[0::2] + 1j * iq[1::2]


def main():
    p = argparse.ArgumentParser(description="SPECTER RF trace extraction")
    p.add_argument("filename", nargs="?", default="output",
                   help="I/Q capture file (default: output)")
    p.add_argument("--fs", type=float, default=2_600_000,
                   help="sample rate in samples/s (default: 2600000)")
    p.add_argument("--nperseg", type=int, default=8192,
                   help="STFT segment length (default: 8192)")
    p.add_argument("--dtype", choices=["int8", "uint8"], default="int8",
                   help="sample format of the capture (default: int8, the format "
                        "written by hackrf_transfer). The previously released "
                        "version of this script read captures as uint8.")
    p.add_argument("--save", metavar="PNG",
                   help="save the plot to a file instead of opening a window")
    args = p.parse_args()

    if args.fs <= 0 or args.nperseg <= 0:
        p.error("--fs and --nperseg must be positive")

    if args.save:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        rf_sig = get_sig(args.filename, args.dtype)
    except OSError as e:
        sys.exit(f"Cannot read {args.filename}: {e}")

    if rf_sig.size < args.nperseg:
        sys.exit("Capture is shorter than one STFT segment.")

    t, Zxx = signal.stft(rf_sig, args.fs, nperseg=args.nperseg)[1:]
    if Zxx.shape[1] <= 2 * TRIM:
        sys.exit(f"Capture too short: {Zxx.shape[1]} STFT frames, "
                 f"need more than {2 * TRIM}.")

    # Magnitude of the zero-frequency bin, first and last frames dropped.
    a = np.abs(Zxx[0, TRIM:-TRIM])
    a_max = np.max(a)
    if not np.isfinite(a_max) or a_max == 0:
        sys.exit("Zero-frequency magnitude is zero everywhere; cannot normalize.")
    r = (a_max - a) / a_max

    plt.plot(t[TRIM:-TRIM], r)
    plt.ylabel("Normalized Magnitude")
    plt.xlabel("Time [sec]")
    if args.save:
        plt.savefig(args.save, dpi=200, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
