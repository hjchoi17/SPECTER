"""SPECTER RF trace extraction.

Reads an interleaved 8-bit I/Q capture, applies an STFT, and plots the
normalized magnitude of the zero-frequency bin over time (Eq. 1 in the paper).
This script only extracts and visualizes the trace. It does not perform frame
synchronization, threshold selection, or bit decisions.
"""

import argparse

import numpy as np
import matplotlib
from scipy import signal


def get_sig(filename, dtype):
    iq = np.fromfile(filename, dtype=dtype).astype(np.float64)
    return iq[0::2] + 1j * iq[1::2]


def main():
    p = argparse.ArgumentParser(description="SPECTER RF trace extraction")
    p.add_argument("filename", nargs="?", default="output",
                   help="I/Q capture file (default: output)")
    p.add_argument("--fs", type=float, default=2_600_000,
                   help="sample rate in samples/s (default: 2600000)")
    p.add_argument("--nperseg", type=int, default=8192,
                   help="STFT segment length (default: 8192)")
    p.add_argument("--dtype", choices=["uint8", "int8"], default="uint8",
                   help="sample format used to read the file (default: uint8, "
                        "as used for the figures in the paper; hackrf_transfer "
                        "itself writes signed int8)")
    p.add_argument("--save", metavar="PNG",
                   help="save the plot to a file instead of opening a window")
    args = p.parse_args()

    if args.save:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rf_sig = get_sig(args.filename, args.dtype)
    t, Zxx = signal.stft(rf_sig, args.fs, nperseg=args.nperseg)[1:]

    # Magnitude of the zero-frequency bin; first and last 20 frames are dropped.
    a = np.abs(Zxx[0, 20:-20])
    r = (np.max(a) - a) / np.max(a)

    plt.plot(t[20:-20], r)
    plt.ylabel("Normalized Magnitude")
    plt.xlabel("Time [sec]")
    if args.save:
        plt.savefig(args.save, dpi=200, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
