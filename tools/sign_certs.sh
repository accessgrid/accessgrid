#!/bin/sh
#
# Certificate signing script
#
#

# Our cert requests are stored here automatically
certRequestRepoDir=${SUDO_USER}@shakey.mcs.anl.gov:/home/FuturesLab
baseDir=/disks/space0/agdev-ca
lockfile=$baseDir/signcerts

# Function for dealing with a lockfile

function my_lockfile()
{
    TEMPFILE="$1.$$"
    LOCKFILE="$1.lock"
    echo $$ >> $TEMPFILE 2>/dev/null || {
	echo "You don't have permission to access `dirname $TEMPFILE`"
	return 1
    }
    ln $TEMPFILE $LOCKFILE 2>/dev/null && {
	rm -f $TEMPFILE
	return 0
    }
    STALE_PID=`< $LOCKFILE`
    test "$STALE_PID" -gt "0" > /dev/null || {
	return 1
    }
    kill -0 $STALE_PID 2>/dev/null && {
	rm -f $TEMPFILE
	return 1
    }
    rm $LOCKFILE  2>/dev/null && {
	echo "Removed stale lock file of process $STALE_PID"
    }
    ln $TEMPFILE $LOCKFILE 2>/dev/null && {
	rm -f $TEMPFILE
	return 0
    }
    rm -f $TEMPFILE
    return 1
}

# Email denial function
function send_deny()
{
    ADDR="$1"
    REASON="$2"

    MSG="Your certificate request to the AG Developers CA has been denied. \
         Please resubmit your request correcting the error described below. \
         The reason for denying the request is:"

    echo $MSG $REASON | mail -s "AG Dev Certificate Denied" $ADDR
}

# Email success function
function send_approve()
{
    ADDR="$1"

    MSG="Your certificate request to the AG Developers CA has been approved \
         and your certificate is ready. You can retrieve this certificate \
         automatically by running the Venues Client and picking \
         View Pending requests from the Preferences->Manage Certificates Menu."

    echo $MSG | mail -s "AG Dev Certificate Approved" $ADDR
}

# Try to lock the lockfile so we can continue
until my_lockfile $lockfile; do
        echo "Waiting for lock"
        sleep 1
done

# Copy the cert repo locally
scp -q -C -r $certRequestRepoDir/agdev-ca .

# Set the umask to open group write
umask 113

# Go through the repo, looking for requests that need to be signed
for DIR in `ls $baseDir/agdev-ca` ;
  do

     currDir=${baseDir}/agdev-ca/${DIR}

     # If there is a request and no cert, check for a denial message
     if [ -f ${currDir}/certreq.pem ] && [ ! -f ${currDir}/cert.pem ]; then

	 # If there is no denial message, make a cert
	 if [ ! -f ${currDir}/deny.txt ]; then

	     req="/usr/bin/openssl req -text -noout -in ${currDir}/certreq.pem"

             #  Sign the cert in ${DIR}/certreq.pem
	     # reqdump="`$req 2>&1`"
	     
	     # pull out the dn
	     dn="`$req 2>&1 | grep Subject | awk -F: '{ print $2 }'`"

	     # pull out the email addres
	     eaddr="`grep EMAIL ${currDir}/metainfo.txt | awk '{ print $2 }'`"

	     echo "Email: " $eaddr
	     echo "Distinguished Name: "
	     echo "   " $dn
	     echo ""
	     echo -n "Sign this certificate? "
	     read -e ans

	     CARGS="-force -in ${currDir}/certreq.pem -out ${currDir}/cert.pem"

	     if [ "$ans" != "" ] ; then
		 if [ "`expr $ans : '[Yy]'`" == "1" ] ; then
		     grid-ca-sign $CARGS
                     # Mail the result
		     send_approve $eaddr
		 fi
		 if [ "`expr $ans : '[Nn]'`" == "1" ] ; then
		     echo -n "Please give a reason: "
		     read -e reason
		     echo $reason > ${currDir}/deny.txt
                     # Mail the result
		     send_deny $eaddr "$reason"
		 fi
	     fi
	 fi
     fi
done

# Copy stuff back

scp -q -C -r ./agdev-ca $certRequestRepoDir

rm -f $lockfile.lock
