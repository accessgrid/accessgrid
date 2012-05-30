#!/bin/sh

sed  -i '1 s/#!\/usr\/bin\/python2\.4/#!\/usr\/bin\/env\ python/' debian/tmp/usr/bin/wsdl2dispatch debian/tmp/usr/bin/wsdl2py


