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
  export rpm_opts="$3"
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
echo "This script installs the necessary RPMS for the Access Grid software, " 
echo "with the exception of python and wxPython.  "
echo "When prompted whether you want to continue, respond with 'y'"
echo "When prompted whether you want to save and quit, respond with 'q'"
echo ""
echo "After the installation, you must log out and back in before using"
echo "the software."
echo "Continue?"
read response
if [ "$response" != 'y' ] && [ "$response" != "Y" ]
then
   exit
fi

#
# Install Phase 1 RPMS
#
echo "***********************************************"
echo "Installing prerequisites" 
echo "***********************************************"
Install $FPCONST $FPCONST_VER
Install $LOGGING $LOGGING_VER 
Install $OPTIK $OPTIK_VER
Install $SOAPPY $SOAPPY_VER
Install $PYGLOBUS $PYGLOBUS_VER
Install $PYOPENSSL $PYOPENSSL_VER 

#
# Install AG RPMS
#
echo "***********************************************"
echo "Installing Access Grid packages "
echo "***********************************************"
for package in $AG ; do
    Install $package $AG_VER 
done

echo ""
echo "Installation finished."
echo ""
echo "Important: "
echo "- You should log out and back in before using the software, "
echo "  to allow proper initialization of the execution environment"
echo "- The AG software should be run by normal users, _not_ root."
