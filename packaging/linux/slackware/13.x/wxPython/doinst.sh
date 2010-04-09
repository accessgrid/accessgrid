#!/bin/sh
LDSOCONF=/etc/ld.so.conf
PATHFOUND=`grep "^include[ ]*/etc/ld.so.conf.d/\*.conf" ${LDSOCONF}` >/dev/null
if [ $? -eq 1 ]; then
  echo "include /etc/ld.so.conf.d/*.conf" >>${LDSOCONF}
fi
/sbin/ldconfig

