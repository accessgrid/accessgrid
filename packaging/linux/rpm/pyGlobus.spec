%define	name		pyGlobus
%define	version		cvs
%define	release		11
%define	prefix		/usr
%define buildroot	/var/tmp/%{name}-%{version}

Summary:  The Grid Packaging Toolkit
Name:     %{name}
Version:  %{version}
Release:  %{release}
Copyright: GTPL
Group:    Utilities/System
URL:      http://www-itg.lbl.gov/gtg/projects/pyGlobus/
Vendor:		Argonne National Laboratory
Source:		%{name}-%{version}.tar.gz
BuildRoot:	%{buildroot}
Requires:	globus-accessgrid
BuildRequires:	globus-accessgrid


%description
pyGlobus is the python wrapper for Globus.

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%build
#. /etc/profile.d/gpt.sh
#. /etc/profile.d/globus.sh
python2.3 ./setup.py build --run-swig --with-modules=io,security,util --flavor="gcc32pthr"

%install
#. /etc/profile.d/gpt.sh
#. /etc/profile.d/globus.sh
python2.3 ./setup.py install --with-modules=io,security,util --flavor="gcc32pthr" --prefix="%{buildroot}%{prefix}" --no-compile

%files
%defattr(-,root,root)
/usr/lib

%post
cat <<EOF > /tmp/pyGlobus-Postinstall.py
#!/usr/bin/python2.3
import pyGlobus
import os
import os.path
import glob
import sys

def modimport(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.py")):
        try:
            __import__(module.__name__ + "." + os.path.basename(module_file[:-3]))
        except:
            pass

sys.stdout.write("Compiling Access Grid Python modules.... ")
modimport(pyGlobus)
sys.stdout.write("Done\n")
EOF
chmod +x /tmp/pyGlobus-Postinstall.py
/tmp/pyGlobus-Postinstall.py
rm -f /tmp/pyGlobus-Postinstall.py

%preun
cat <<EOF > /tmp/pyGlobus-Preuninstall.py
#!/usr/bin/python2.3
import pyGlobus
import os
import os.path
import glob

def delcompiled(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.pyc")):
        try:
            os.remove(module_file)
        except os.error:
            pass

delcompiled(pyGlobus)
EOF
chmod +x /tmp/pyGlobus-Preuninstall.py
/tmp/pyGlobus-Preuninstall.py
rm -f /tmp/pyGlobus-Preuninstall.py

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog

* Sat Mar 15 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added compiling module agfter install

* Tue Jan 28 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

