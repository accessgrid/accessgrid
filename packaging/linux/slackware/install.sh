#!/bin/sh
#
# install.sh
#
# Install packages necessary for AG2.  This script attempts to ensure
# that the necessary packages are installed and up to date. 
#
# Note:  It currently makes no effort to handle failures!
#

# First, check for external prerequisites
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


#################################################################
# Install processing begins here
#################################################################

# Inform user what will be done and prompt to continue
#
echo
echo "This script installs the Slackware packages for the Access Grid software. " 
echo "Continue ? [y/n]"
read response
if [ "$response" != 'y' ] && [ "$response" != "Y" ]
then
   exit 5
fi

# Default ALSA sound devices
#
if [ -x ./snddevices ]; then
  echo
  echo "Treating ALSA devices"
  sh ./snddevices
  echo
fi


#
# Define Slackware packages
# To update this script to install newer versions of packages
# change the variables defined here
#

export GLOBUS="globus-accessgrid"
export GLOBUS_VER="2.4-i486-2"

export AG="AccessGrid"
export AG_VER=VER
 

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
# Check that python2 (typically a link to python2.2 or python2.3) is available
#
echo "Checking python2 link"
PYTHON2=`which python2 2>/dev/null`
if [ ! $? -eq 0 ]; then
  PYTHONEXE=`which pythonPYVER 2>/dev/null`
  if [ ! $? -eq 0 ]; then
    echo "No pythonPYVER available! Please find one and start again"
    exit 2
  else
    echo "Found ${PYTHONEXE} but no python2 link to it" 
    echo  "Create a link to ${PYTHONEXE} now? (Press y to create link) "
    read response
    if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
      echo "Not creating link (at your request), exiting now"
      exit 3
    fi
    PYDIR=`dirname ${PYTHONEXE}`
    ln -s ${PYTHONEXE} ${PYDIR}/python2
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
echo "python2 OK"



#
# Install globus package
#
echo ""
echo "***********************************************"
echo "Installing ${GLOBUS}-${GLOBUS_VER} " 
echo "***********************************************"
Install $GLOBUS $GLOBUS_VER
echo ""

#
# Install AG package
#
echo ""
echo "***********************************************"
echo "Installing Access Grid package "
echo "***********************************************"
Install $AG $AG_VER
echo ""

#
# Install XDG menu stuff
#
echo ""
echo "***********************************************"
echo "Install AG Menus "
echo "***********************************************"
here=`pwd`
APPSMENU_PATCH=${here}/applications-all-users.vfolder-info.diff

if [ ! -r ${APPSMENU_PATCH} ]; then
  echo "No patch file found"
  exit 1
fi

cd /etc/gnome-vfs-2.0/vfolders

patch -p0 -N -t -l -s --dry-run 2>&1 > /dev/null < ${APPSMENU_PATCH}
if [ $? -eq 0 ]; then
  echo "Patching \"Applications\" menu"
  patch -p0 -N -t -l -s  2>&1 > /dev/null < ${APPSMENU_PATCH}
else
  echo "Patch won't apply cleanly."
  echo "Perhaps the \"Applications\" menu was patched by a previous installation? "
fi

echo ""
echo "Installation finished."
echo ""

exit 0

