import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def get_sig(filename):
    iq = np.fromfile(filename, dtype=np.uint8)

    I = iq[0::2]
    Q = iq[1::2]
    rf_sig = I + 1j * Q

    return rf_sig


if __name__=="__main__":
    filename = "output"
    filename = "result"
    rf_sig = get_sig(filename)

    print(rf_sig)

    fs = 2600000

    f, t, Zxx = signal.stft(rf_sig, fs, nperseg=8192)

    covert_sig = np.abs(Zxx[0,20:-20])

    normalized_sig = (np.max(covert_sig) - covert_sig)/np.max(covert_sig)

    plt.plot(t[20:-20],normalized_sig)
    plt.ylabel('Normalized Frequency')
    plt.xlabel('Time [sec]')
    plt.show()
