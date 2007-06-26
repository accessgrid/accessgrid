
# Add /path/to/libgtkembed.so to ld search path
#
arch=`uname -m`
if [ "${arch}" = "x86_64" ]; then
  LIBDIR="/usr/lib64"
else
  LIBDIR="/usr/lib"
fi

LDSOCONF="/etc/ld.so.conf"
echo "Adding libgtkembedmoz path to ${LDSOCONF}"

d=`find ${LIBDIR}/ -type d -name "seamonkey*"`
echo "Candidate paths: $d"
for i in $d; do
  location=`find $i -type f -name "libgtkembedmoz.*"`
done
echo "Using $location"

if [ -z $location ]; then
  /sbin/ldconfig
  exit 1
fi

dir2add=`dirname $location`

inld=`grep ${dir2add} ${LDSOCONF}`
if [ $? -ne 0 ];then
  echo "Adding ${dir2add} to ${LDSOCONF}"
  echo "$dir2add" >>${LDSOCONF}
else
  echo "$dir2add already exists in ${LDSOCONF}"
fi

/sbin/ldconfig

