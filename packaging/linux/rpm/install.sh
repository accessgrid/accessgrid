#!/bin/sh
#
# install.sh
#
# Install packages necessary for AG2.  This script attempts to ensure
# that the necessary packages are installed and up to date. 
#
# Note:  It currently makes no effort to handle failures!
#

#
# Define RPMS
# To update this script to install newer versions of packages
# change the variables defined here
#

export GLOBUS="globus-accessgrid"
export GLOBUS_VER="2.4-1"

export AG="AccessGrid"
export AG_VER="2.2-4"
 

#################################################################
# Install processing begins here
#################################################################

#
# Install the specified package and version
# 
# - existing packages are not installed
# - downrev packages are freshened
# - non-existent packages are installed
Install() 
{
  export package="$1"
  export package_ver="$2"
  export package_rpm="$package-$package_ver.i386.rpm"

  rpm -q --quiet $package
  if [ $? -eq 0 ] ; then
    if [ "`rpm -q -v $package`" == "$package-$package_ver" ] ; then
      echo "Package already installed:" $package-$package_ver
    else
      echo "Freshening package:" $package
      rpm -Fvh --nodeps $rpm_opts $package_rpm
    fi
  else
    echo "Installing package:" $package
    rpm -Uvh $rpm_opts $package_rpm
  fi
}


# Inform user what will be done and prompt to continue
#
echo "This script installs the necessary RPMS for the Access Grid software. " 
echo "Continue?"
read response
if [ "$response" != 'y' ] && [ "$response" != "Y" ]
then
   exit
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
