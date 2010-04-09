#!/bin/sh


# Setup udev for good permissions on /dev/raw1394
config() {
    NEW="$1"
    OLD="$(dirname $NEW)/$(basename $NEW .new)"
    # If there's no config file by that name, mv it over:
    if [ ! -r $OLD ]; then
        mv $NEW $OLD
    elif [ "$(cat $OLD | md5sum)" = "$(cat $NEW | md5sum)" ]; then
        # toss the redundant copy
        rm $NEW
    fi
    # Otherwise, we leave the .new copy for the admin to consider...
    [ -f $NEW ] && {
        echo
        echo "Please do something about /$NEW"
        echo "It may confict with your existing configuration!"
        echo
    }
}
config lib/udev/rules.d/86-firewire-camera.rules.new


# Configure the kernel parameters now
#
/sbin/sysctl -e -p /etc/sysctl.d/60-aghdvic.conf


# Add sysctl processing to rc.local
#
EXTRAFOUND=`grep "### EXTRA SYSCTL PROCESSING ###" /etc/rc.d/rc.local`
if [ $? -eq 1 ]; then
  cat <<EOF >>/etc/rc.d/rc.local

### EXTRA SYSCTL PROCESSING ###
if [ -x /sbin/sysctl ]; then
  for file in /etc/sysctl.d/*.conf ; do
    if [ -r \$file ]; then
      /sbin/sysctl -e -p \$file
    fi
  done
fi

EOF
fi

