%define	name		pyOpenSSL
%define	version		0.5.1
%define	release		1
%define	prefix		/usr
%define sharedir	%{prefix}/share
%define docdir		%{sharedir}/doc/%{name}-%{version}
%define buildroot	/var/tmp/%{name}-%{version}

Summary:	The Python OpenSSL Module
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	GLPL
Group:		Utilities/System
URL:		http://www-itg.lbl.gov/gtg/projects/pyGlobus/
Vendor:		Argonne National Laboratory
Source:		%{name}-%{version}.tar.gz
BuildRoot:	%{buildroot}
Requires:	python2 >= 2.2 openssl >= 0.9.6
BuildRequires:	python2 >= 2.2 openssl-devel >= 0.9.6 tetex-latex


%description
pyOpenSSL is the python wrapper for OpenSSL.

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%build
python2.2 ./setup.py build
cd doc
make all

%install
python2.2 ./setup.py install --prefix="%{buildroot}%{prefix}" --no-compile
mkdir -p %{buildroot}%{docdir}
#cp -dR INSTALL ChangeLog COPYING README TODO doc/pyOpenSSL.txt doc/pyOpenSSL.dvi pyOpenSSL.ps doc/html %{buildroot}%{share}
cp -dR INSTALL ChangeLog COPYING README TODO doc/pyOpenSSL.txt doc/pyOpenSSL.dvi doc/html/ examples/ %{buildroot}%{docdir}

%files
%defattr(-,root,root)
/usr/lib
%doc %{docdir}/*

%post
cat <<EOF > /tmp/%{name}-Postinstall.py
#!/usr/bin/python2.2
import OpenSSL
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

sys.stdout.write("Compiling OpenSSL Python modules.... ")
modimport(OpenSSL)
sys.stdout.write("Done\n")
EOF
chmod +x /tmp/%{name}-Postinstall.py
/tmp/%{name}-Postinstall.py
rm -f /tmp/%{name}-Postinstall.py

%preun
cat <<EOF > /tmp/%{name}-Preuninstall.py
#!/usr/bin/python2.2
import OpenSSL
import os
import os.path
import glob

def delcompiled(module):
    for module_file in glob.glob(os.path.join(module.__path__[0], "*.pyc")):
        try:
            os.remove(module_file)
        except os.error:
            pass

delcompiled(OpenSSL)
EOF
chmod +x /tmp/%{name}-Preuninstall.py
/tmp/%{name}-Preuninstall.py
rm -f /tmp/%{name}-Preuninstall.py

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog

* Tue Apr 02 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

