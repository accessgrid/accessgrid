import sys
import os

out = file(sys.argv[1], "w")

# get lspci output
cmd = "/sbin/lspci -m"
print cmd

# get list of devices from /proc/video/dev
cmd = "ls /proc/video/dev | grep video"
print cmd

# get output of v4l-ctl -c <dev>

for d in deviceList:
    cmd = "v4lctl list -c /dev/%s" % d
    print cmd
    
out.close()
