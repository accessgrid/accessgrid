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
#

#
# Define RPMS
# To update this script to install newer versions of packages
# change the variables defined here
#

export FPCONST="fpconst"
export FPCONST_VER="0.6.0-1"
export LOGGING="logging"
export LOGGING_VER="0.4.7-2"
export OPTIK="Optik"
export OPTIK_VER="1.4.1-1"
export PYGLOBUS="pyGlobus"
export PYGLOBUS_VER="cvs-11"
export PYOPENSSL="pyOpenSSL_AG"
export PYOPENSSL_VER="0.5.1-4"
export SOAPPY="SOAPpy"
export SOAPPY_VER="0.11.3_cvs_2004_04_01-1"

export AG="
AccessGrid 
AccessGrid-VenueClient
AccessGrid-VenueServer
AccessGrid-BridgeServer"
export AG_VER="2.2-1"
 

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
  export arch="$3"
  export package_rpm="$package-$package_ver.$arch.rpm"

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
Install $FPCONST $FPCONST_VER noarch
Install $LOGGING $LOGGING_VER noarch
Install $OPTIK $OPTIK_VER noarch
Install $SOAPPY $SOAPPY_VER noarch
Install $PYGLOBUS $PYGLOBUS_VER i386
Install $PYOPENSSL $PYOPENSSL_VER i386

#
# Install AG RPMS
#
echo "***********************************************"
echo "Installing Access Grid packages "
echo "***********************************************"
for package in $AG ; do
    Install $package $AG_VER i386
done

echo ""
echo "Installation finished."
echo ""
