import os
import sys
import time
import getopt
import subprocess
import platform

def usage():
    print("-------------------------------------------------usage-------------------------------------------------------------------------")
    print("python3 final_send.py [-i inptut_message]")
    print("python3 final_send.py [--input inptut_message]")
    print("-------------------------------------------------------------------------------------------------------------------------------")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:", ["help", "input="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    msg = None
    port = None
    OS = platform.system()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif o in ("-i", "--input"):
            msg = a
        else:
            usage()
            sys.exit(2)

    if msg == None:
        usage()
        sys.exit(2)

    # ubuntu
    if OS == "Linux":

        # Input your port
        port = 'PORT'

        device_query = '/sys/bus/usb/devices/' + port + '/manufacturer'
        device = subprocess.check_output(["cat", device_query]).decode('utf-8').rstrip()

        for i in msg:
            if i == "1":
                query = 'echo "on" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/level'
                query2 = 'echo "2000" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/autosuspend_delay_ms'
                query3 = 'echo "2" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/autosuspend'
                query4 = 'echo "on" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/control'
                query5 = 'echo "on" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/level'
                query6 = 'echo "2000" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/autosuspend_delay_ms'
                query7 = 'echo "2" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/autosuspend'
                query8 = 'echo "on" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/control'

            elif i == "0":
                query = 'echo "auto" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/level'
                query2 = 'echo "0" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/autosuspend_delay_ms'
                query3 = 'echo "0" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/autosuspend'
                query4 = 'echo "auto" | sudo tee -a /sys/bus/usb/drivers/usb/' + port + '/power/control'
                query5 = 'echo "auto" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/level'
                query6 = 'echo "0" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/autosuspend_delay_ms'
                query7 = 'echo "0" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/autosuspend'
                query8 = 'echo "auto" | sudo tee -a /sys/bus/usb/devices/' + port + '/power/control'

            else:
                print("msg must be 1 or 0!!!")
                exit(2)

            if device == "SAMSUNG":    
                os.system(query)
                os.system(query2)
                os.system(query3)
                os.system(query4)
                os.system(query5)
                os.system(query6)
                os.system(query7)
                os.system(query8)
                os.system('cat /sys/bus/usb/devices/' + port + '/power/runtime_status')

                time.sleep(5)

            elif device == "Apple Inc.":
                os.system(query5)
                os.system(query6)
                os.system(query7)
                os.system(query8)
                os.system('cat /sys/bus/usb/devices/' + port + '/power/runtime_status')

                time.sleep(5)


    # Windows
    elif OS == "Windows":
        RF = 0
        state = 1

        # Input your PID
        parsed_hwid = 'PID'

        subprocess.run(['devcon', 'enable', parsed_hwid])
        subprocess.run(['devcon', 'enable', parsed_hwid])
        subprocess.run(['devcon', 'disable', parsed_hwid])
        subprocess.run(['devcon', 'enable', parsed_hwid])
        subprocess.run(['devcon', 'enable', parsed_hwid])

        if RF != "1":
            for i in msg:
                if i == "0":
                    subprocess.run(['devcon', 'disable', parsed_hwid])

                    time.sleep(1)
                
                elif i == "1":
                    subprocess.run(['devcon', 'enable', parsed_hwid])
                    subprocess.run(['devcon', 'enable', parsed_hwid])

                    time.sleep(1)

        elif RF == "1":
            for i in msg:
                if i == "0":
                    print("0")

                    time.sleep(1)
                
                elif i == "1":
                    print("1")
                    if state == 1:
                        subprocess.run(['devcon', 'disable', parsed_hwid])
                        state = 0

                    elif state == 0:
                        subprocess.run(['devcon', 'enable', parsed_hwid])
                        subprocess.run(['devcon', 'enable', parsed_hwid])
                        state = 1

                    time.sleep(1)


    # MacOS (Not supported yet)
    elif OS == "Darwin":
        for i in msg:
            if i == "1":
                try:
                    os.system('mv /System/Library/Extensions/IOUSBMassStorageClass.kext.bup /System/Library/Extensions/IOUSBMassStorageClass.kext')

                    time.sleep(5)

                except:
                    time.sleep(5)
                    pass

            elif i == "0":
                try:
                    os.system('mv /System/Library/Extensions/IOUSBMassStorageClass.kext /System/Library/Extensions/IOUSBMassStorageClass.kext.bup')
                except:
                    time.sleep(5)
                    pass

    else:
        print("Not supported OS")


if __name__ == "__main__":
    main()
    