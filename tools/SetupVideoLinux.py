import sys
import os

out = file(sys.argv[1], "w")


# Initialize the device list
deviceList = dict()

if os.path.exists('/proc/video/dev'):
    # Get list of devices
    cmd = "ls /proc/video/dev | grep video"
    fh = os.popen(cmd,'r')
    for line in fh.readlines():
        device = os.path.join('/dev',line.strip())
        deviceList[device] = None
    fh.close()

    # Determine ports for devices
    portString = ""
    for d in deviceList.keys():
        cmd = "v4lctl list -c %s" % d
        fh = os.popen(cmd)
        for line in fh.readlines():
            if line.startswith('input'):
                portString = line.split('|')[-1]
                deviceList[d] = portString.strip()
                break
                
deviceList['x11'] = 'x11'

# Write the devices to the specified file
for device,portString in deviceList.items():
    out.write("device: %s\n"% device)
    out.write("portnames:  %s\n"% portString)

out.close()
