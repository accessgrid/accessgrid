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
export WXWINDOWS="wxGTK"
export WXWINDOWS_VER="2.4.0-1"
export LOGGING="logging"
export LOGGING_VER="0.4.7-2"
export PYOPENSSL="pyOpenSSL_AG"
export PYOPENSSL_VER="0.5.1-3"
export GPT="gpt"
export GPT_VER="1.0-2"
export GLOBUS="globus-accessgrid"
export GLOBUS_VER="2.0-2"
export PYGLOBUS="pyGlobus"
export PYGLOBUS_VER="cvs-10"

export AGRAT="AccessGrid-rat"
export AGRAT_VER="4.2.22-2"
export AGVIC="AccessGrid-vic"
export AGVIC_VER="2.8ucl1.1.3-3"

export AG="
AccessGrid 
AccessGrid-VenueClient
AccessGrid-VenueServer
AccessGrid-BridgeServer"
export AG_VER="2.1.2-9"
 

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
      rpm -Fvh --nodeps $package_rpm
    fi
  else
    echo "Installing package:" $package
    rpm -Uvh $package_rpm
  fi
}

#
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
# Before installing, check whether globus is already installed
#
if [ "`rpm -q -v $GLOBUS`" == "$GLOBUS-$GLOBUS_VER" ] ; then
  export GLOBUS_PREINSTALLED=1
fi
  


#
# Install Phase 1 RPMS
#
echo "***********************************************"
echo "Installing prerequisites (phase 1) " 
echo "***********************************************"
Install $WXWINDOWS $WXWINDOWS_VER
Install $LOGGING $LOGGING_VER 
Install $PYOPENSSL $PYOPENSSL_VER 
Install $GPT $GPT_VER 
Install $GLOBUS $GLOBUS_VER 


#
# Run Globus post-install scripts
#
if [ "$GLOBUS_PREINSTALLED" ] ; then
  echo "Globus was already installed; skipping configuration steps"
else
  . /etc/profile.d/gpt.sh
  . /etc/profile.d/globus.sh
  ${GPT_LOCATION}/sbin/gpt_verify
  ${GPT_LOCATION}/sbin/gpt-postinstall
  /usr/lib/globus/setup/globus/setup-gsi
  /usr/lib/globus/setup/globus_simple_ca_45cc9e80_setup/setup-gsi -default
fi

#
# Install Phase 2 RPMS
#
echo "***********************************************"
echo "Installing prerequisites (phase 2) "
echo "***********************************************"
Install $PYGLOBUS $PYGLOBUS_VER 

#
# Install AG media tools RPMS
#
echo "***********************************************"
echo "Installing media tools " 
echo "***********************************************"
Install $AGRAT $AGRAT_VER 
Install $AGVIC $AGVIC_VER


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
