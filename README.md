# SPECTER: USB Power Modulation Transmitter and RF Receiver
Reference implementation for studying a covert channel that encodes bits by toggling the USB port power and, optionally, receives low frequency RF emissions produced by those power transitions. This repository includes a transmitter and an RF receiver.

## Ethical and Safety Notice
- Use only in a controlled lab with devices you own and explicit authorization.
- Do not deploy on systems or networks you do not control.
- The code modulates VBUS power only. The D+ and D- data lines are not used.
- Peripherals remain unmodified in our experiments.

## Repository Contents
 - final_send.py - USB power modulation transmitter CLI. Linux uses sysfs power knobs. Windows uses devcon to enable or disable the device. macOS is present but not supported.
 - RF_receive.py - Minimal RF receiver that reads interleaved unsigned-8-bit IQ from a file, performs an STFT, and visualizes a normalized envelope over time.

## Summary of the Method
- Transmitter encodes bits by toggling the USB port power.
- Receivers
  1. Charging status on a smartphone
  2. Peripheral operating status observed via LEDs or activity indicators
  3. RF reception that measures low frequency emissions near 5 MHz with a software defined radio
 
This repository provides code for (1) transmitter and (3) RF receiver.

## Requirements
- OS: Windows 10 or Ubuntu 22.04 LTS
- Python: 3.9 or newer
- Privileges: administrator on Windows or root on Linux for port power control
- Optional RF hardware
  - Software defined radio (SDR) supported by SoapySDR or UHD
  - Low frequency antenna or a simple wire placed near the USB cable
  
`pip3 install -r requirments.txt`

## Transmitter (final_send.py)
Encodes a bit string by toggling the USB port power per bit.

### Packet and Encoding
- Payload: user supplied bit string
- Encoding
  - Charging and operating status receivers
     - 1 is power on and 0 is power off with device specific dwell
  - RF receiver
     - 1 is the presence of exactly one power toggle at the start of a symbol interval
     - 0 is no toggle during the interval
- Symbol duration: device dependent
   - mouse 1 s
   - other peripherals up to 4 s

 ### Quick Start
 `python3 total_send.py [-i inptut_message]`
 `python3 total_send.py [--input inptut_message]`

### Linux notes
- Edit the placeholder port = 'PORT' to your device path (for example 1-1).
- The script reads /sys/bus/usb/devices/<PORT>/manufacturer and applies different sysfs writes for Samsung vs Apple.
- For each bit it writes to power control files under both /sys/bus/usb/drivers/usb/<PORT>/power/… and /sys/bus/usb/devices/<PORT>/power/…, then sleeps 5 s per bit, which yields about 0.2 bit/s.

### Windows notes
- Install Microsoft DevCon and ensure it is on PATH.
- Set parsed_hwid = 'PID' to your device’s hardware ID string.
- The script does a few devcon enable/disable calls to initialize, then for each bit:
   - bit 1 → devcon enable <HWID> (twice) and sleep 1 s
   - bit 0 → devcon disable <HWID> and sleep 1 s
- There is a code path intended for RF experiments gated by RF == "1". It is currently hard-coded to RF = 0 and compared to a string, so you must edit the file and set RF = "1" to activate the event-based toggling that only flips power during symbols carrying a one.

### macOS
- A placeholder branch exists that renames a kext, but the script marks macOS as not supported for power toggling.

## Android charging receiver (charging_receiver.apk)
### Requirements
- Android 10 or newer recommended
- Enable Install unknown apps for your file manager
- Connect the phone to the target host via USB
- On some devices, you must choose a USB mode such as Transferring images (PTP/MTP) to allow reliable power control

### Quick start
1. Copy charging_receive.apk to the phone and install it.
2. Connect the phone to the target machine with a USB cable.
3. Open the app and press Start capture.
4. Run the transmitter on the host.
5. Press Stop capture.

### Decoding rule
- Transition present within an interval → 1
- No transition within an interval → 0

## RF Receiver (RF_receiove.py)
Parses an interleaved uint8 IQ file, performs STFT, and plots a normalized envelope vs time.

### Expected input
- A raw IQ capture file named output in the working directory. This file is produced with HackRF using the command below.
- Interleaved unsigned 8-bit IQ format [I0, Q0, I1, Q1, …].
- Default sample rate in the script is 2_600_000 sps, which matches the command.

### Record IQ with HackRF
`hackrf_transfer -r output -f 5000000 -s 2600000 -a 1 -x 0`

- -r output writes interleaved uint8 IQ to a file named output
- -f 5000000 tunes near 5 MHz
- -s 2600000 sample rate 2.6 MS/s
- -a 1 enables the on-board amplifier path (bias/amp, board dependent)
- -x 0 sets TX VGA, harmless here and left at 0

### Quick Start
`python3 RF_receive.py`

The script reads output, performs STFT, and plots a normalized envelope over time. You should see amplitude spikes aligned with symbol intervals. If the plot is noisy, increase the symbol duration on the transmitter or repeat the packet.

If you use a different SDR or filename, either rename your file to output or edit the filename variable at the top of RF_receive.py.

## End-to-End Checklist
1. Confirm OS-level privileges for power control.
2. On Linux set PORT, on Windows set parsed_hwid.
3. Choose a symbol duration that matches your device latency
  - mouse about 1 s, other peripherals up to 4 s per symbol
4. If using the RF path, capture IQ near 5 MHz, then run RF_receive.py.
5. Align the transmitter bit schedule with the RF plot to verify correct decoding.

## Known limitations
- Placeholders PORT and PID must be set by the user.
- Linux sleeps 5 s per bit, which caps rate at 0.2 bit/s unless you modify the code.
- RF script expects uint8 IQ and a hard-coded filename. Change filename or adapt to your SDR format as needed.

## FAQ
**Does this use the USB data lines?**

No. Only VBUS power is modulated. D+ and D− remain unused.

**Are peripherals modified?**

No. Peripherals are left unmodified in our experiments.

**Why 5 MHz?**

In our lab, bursts from power transitions were most visible near 5 MHz in spectrum waterfalls. You may need to scout and adjust.
