#!/bin/sh


LDSOCONF=/etc/ld.so.conf
PATHFOUND=`grep /usr/lib/wxPython-2.6.3.2-gtk2-ansi/lib /etc/ld.so.conf ${LDSOCONF}` >/dev/null
if [ $? -eq 1 ]; then
    echo "/usr/lib/wxPython-2.6.3.2-gtk2-ansi/lib" >>${LDSOCONF}
fi
/sbin/ldconfig

