# SPECTER

Artifact for "SPECTER: Covert Data Exfiltration from Air-Gapped Systems via USB Power Modulation."

SPECTER sends bits from a host by issuing host-side USB power-management or device-state operations. The payload is not placed in USB data transfers. The result is observed through one of three receiver paths: smartphone charging state, visible peripheral behavior, or near-field RF activity near the USB cable.

These operations change the runtime power-management or operating-system device state. They do not by themselves guarantee that VBUS is physically disconnected. What can be observed depends on the host controller, hub, driver, and connected device.

## Ethical notice

Use this code only on devices you own, in an isolated lab. Do not run it on systems you are not authorized to control.

## Contents

| File | Description |
|---|---|
| `final_send.py` | Transmitter for Linux (sysfs) and Windows (DevCon) |
| `charging_receive.apk` | Android charging-state receiver |
| `RF_receive.py` | RF trace extraction and plotting from an I/Q capture |
| `requirements.txt` | Python dependencies for `RF_receive.py` |

The peripheral-state receiver needs no code. The observer watches the device LED or behavior directly.

## Tested environment

- Transmitter hosts: Ubuntu 22.04.4 (desktop), Windows 10 (laptop)
- Charging-state receivers: Galaxy S22 (Android 14) with the app, iPhone 13 Pro (iOS 17.4.1) by watching the charging indicator
- Peripherals: USB mouse, keyboard, webcam, wireless-headset dongle, USB hub
- RF: HackRF One with an LF-R 400 loop antenna placed in direct contact with the USB cable

Python 3.9 or newer.

```
pip3 install -r requirements.txt
```

## Transmitter (`final_send.py`)

Root is required on Linux and administrator privileges on Windows. The target device must be given explicitly on the command line.

### Linux

```
sudo python3 final_send.py -i 101011 --port 1-1
```

`--port` is the device name under `/sys/bus/usb/devices/`. The script reads the device manufacturer and uses one of two branches.

- `Apple Inc.` writes the active or inactive values under `/sys/bus/usb/devices/<port>/power/`.
- `SAMSUNG` writes the same values through both `/sys/bus/usb/drivers/usb/<port>/power/` and `/sys/bus/usb/devices/<port>/power/`. The two paths may point to the same device.

Other manufacturers are rejected because they were not tested.

| | `control` | `autosuspend_delay_ms` | `level` | `autosuspend` |
|---|---|---|---|---|
| bit 1 | on | 2000 | on | 2 |
| bit 0 | auto | 0 | auto | 0 |

`level` and `autosuspend` are legacy attributes and may be missing on newer kernels. They are skipped if absent. The script exits with an error if writing `control` or `autosuspend_delay_ms` fails. The default waiting period is 5 s per bit (`--interval` to change it, see below).

On the Galaxy S22 the charging-state response appeared only after selecting the "Transferring images" USB mode on the phone.

### Windows

Install [DevCon](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/devcon) and put it on PATH. Find the device with

```
devcon findall "*USB*"
devcon hwids "*USB*"
```

then run

```
python final_send.py -i 101011 --hwid "<HWID>"
```

If you pass a device instance ID instead of a hardware ID, prefix it with `@`.

Bit 1 enables the device and bit 0 disables it. Enable is issued twice because a single call did not always restore the device state in our setup. The default waiting period is 1 s per bit.

The script exits with an error if a DevCon command fails.

### Waiting period and symbol timing

`--interval` sets a software waiting period that starts after the control operations for a bit have finished. The time between successive symbols is this waiting period plus command execution and scheduling delay, so the actual symbol period is longer than `--interval` and varies between hosts and devices. Some peripherals also recover too slowly to be distinguishable at short waiting periods. Choose the waiting period for the receiver you use, and check the resulting timing on the receiver side.

```
python final_send.py -i 101011 --hwid "<HWID>" --interval 4
```

For the RF receiver add `--rf`. This switches to event-based encoding, where bit 1 is one state change at the start of the symbol and bit 0 is no change.

```
python final_send.py -i 101011 --hwid "<HWID>" --rf
```

### Packet format

The transmitter sends the bit string exactly as given. Framing is done beforehand. For charging-state and peripheral-state reception the paper uses

```
preamble 101011 | header (payload length) | payload | CRC | trailer 1
```

and the RF experiments use the shorter preamble `101`.

## Android charging-state receiver (`charging_receive.apk`)

Tested on a Galaxy S22 running Android 14. Allow installation from unknown sources to install the APK.

1. Install the app and connect the phone to the transmitting host.
2. Enter the number of bits to receive.
3. Start reception so that it lines up with the first transmitted symbol. On Windows the transmitter runs a device initialization sequence before sending the bit string, so launching both programs at the same moment does not align the symbols.

For each bit, the app takes 6 battery-status samples 1 s apart, so one bit window lasts about 6 s or slightly more with processing time. A window is decoded as 1 if every sample in it is charging or full, and as 0 otherwise. The decoded bits are shown on screen. No root access or system modification is needed.

The app does not detect the preamble or synchronize to the transmitter by itself. Alignment depends on starting reception at the first symbol, and the transmitter's symbol period has to match the app's bit window. Set `--interval` accordingly and allow for the command execution time described above.

## RF receiver (`RF_receive.py`)

Capture I/Q near 5 MHz with HackRF.

```
hackrf_transfer -r output -f 5000000 -s 2600000 -a 1
```

Then plot the trace.

```
python3 RF_receive.py output --dtype int8
python3 RF_receive.py output --dtype int8 --save trace.png
```

The script applies an STFT (8192-sample segments at 2.6 MS/s), takes the magnitude of the zero-frequency bin, drops the first and last 20 frames, and plots `(A_max - A_k) / A_max`. Bits are read from the presence or absence of bursts in each symbol interval.

The script only extracts and plots the trace. It does not synchronize frames, pick a threshold, or output bits.

`hackrf_transfer` writes signed 8-bit I/Q, which is the default (`--dtype int8`). The previously released version of this script read captures as unsigned 8-bit samples. `--dtype uint8` reproduces that behavior.

The script stops with an error if the capture is too short for the STFT or if the trace cannot be normalized.

5 MHz is where switching-related bursts were easiest to see in our setup. It may differ with other hardware, and RF results were obtained only with the antenna touching the cable.

## License

MIT
