#!/bin/sh
#
# install.sh
#
# Install packages necessary for AG2.  This script attempts to ensure
# that the necessary packages are installed and up to date. 
#
# Note:  It currently makes no effort to handle failures!
#

# Has wxPythonGTK been installed?
#
WXPYGTK=`ls /var/adm/packages | grep wxPythonGTK`
if [ ! $? -eq 0 ]; then
    echo "Can't find wxPythonGTK package installed"
    echo "Please install wxPythonGTK package, before running this script again"
    exit 1
fi


# Has xawtv been installed? (need v4lctl)
# We could just look for v4lctl
#
XAWTV=`ls /var/adm/packages | grep xawtv`
if [ ! $? -eq 0 ]; then
    echo "Can't find xawtv package installed"
    echo "Please install xawtv package, before running this script again"
    exit 2
fi

# Default ALSA sound devices
#
if [ -x ./snddevices ]; then
  echo
  sh ./snddevices
  echo
fi


#
# Define Slackware packages
# To update this script to install newer versions of packages
# change the variables defined here
#

export GLOBUS="globus-accessgrid"
export GLOBUS_VER="2.4-i486-1"

export AG="AccessGrid"
export AG_VER=VER
 

#################################################################
# Install processing begins here
#################################################################

#
# Install the specified package and version
# 
Install() 
{
  export package="$1"
  export package_ver="$2"
  export package_tgz="$package-$package_ver.tgz"

  upgradepkg --install-new --reinstall $package_tgz

  if [ ! $? -eq 0 ]; then
    echo "Trouble installing ${package_tgz}, exiting now !!!"
    exit 1
  fi
}

#
# Check that python2 (typically a link to python2.3) is available
#
PYTHON2=`which python2 2>/dev/null`
if [ ! $? -eq 0 ]; then
  PYTHON23=`which python2.3 2>/dev/null`
  if [ ! $? -eq 0 ]; then
    echo "No python2.3 available! Please find one and start again"
    exit 2
  else
    echo "Found ${PYTHON23} but no python2 link to it" 
    echo  "Create a link to ${PYTHON23} now? (Press y to create link) "
    read response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
      echo "Not creating link (at your request), exiting now"
      exit 3
    fi
    PYDIR=`dirname ${PYTHON23}`
    ln -s ${PYTHON23} ${PYDIR}/python2
  fi
fi
# Confirm creation of python2 link worked
#
PYTHON2=`which python2`
if [ ! $? -eq 0 ]; then
 echo
 echo
 echo
 echo "STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP! STOP!"
 echo "An attempt to create ${PYDIR}/python2 failed!"
 echo "Parts of this installation will also probably fail."
 echo
 echo "Please ensure your python installation is intact."
 echo "Then run this installation again."
 echo
 echo

 exit 4
fi



# Inform user what will be done and prompt to continue
#
echo
echo "This script installs the Slackware packages for the Access Grid software. " 
echo "Continue?"
read response
if [ "$response" != 'y' ] && [ "$response" != "Y" ]
then
   exit 5
fi

#
# Install Prerequisites
#
echo "***********************************************"
echo "Installing prerequisites" 
echo "***********************************************"
Install $GLOBUS $GLOBUS_VER

#
# Install AG RPMS
#
echo "***********************************************"
echo "Installing Access Grid packages "
echo "***********************************************"
Install $AG $AG_VER

echo ""
echo "Installation finished."
echo ""

