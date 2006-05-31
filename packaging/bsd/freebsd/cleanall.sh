here=`pwd`
CMD='sudo make'
ALLDIRS=0

while [ $# -gt 0 ]; do
  case "$1" in
    -d)
      CMD="${CMD} deinstall"
      ;;
    -c)
      CMD="${CMD} clean"
      ;;
    -a)
      ALLDIRS=1
      ;;
    *)
      echo "Unknown option ($1). Exiting!"
      exit 1
      ;;
  esac
  shift
done
if [ "${CMD}" = "sudo make" ]; then
   CMD='sudo make clean'
fi
#echo "Running command: ${CMD}"

if [ ${ALLDIRS} -eq 1 ]; then
  cd ${here} && ${CMD}
fi

for d in `ls -1 ports` ; do
  if [ "$d" = "CVS" ]; then continue; fi
  echo ports/$d
  cd ports/$d && ${CMD}
  cd ${here}
done

