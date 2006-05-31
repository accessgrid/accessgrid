here=`pwd`
CMD='sudo make deinstall clean'

for d in `ls -1 ports` ; do
  echo ports/$d
  cd ports/$d && ${CMD}
  cd ${here}
done

