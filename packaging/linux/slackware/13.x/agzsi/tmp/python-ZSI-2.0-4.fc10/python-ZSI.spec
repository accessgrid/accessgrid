%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           python-ZSI
Version:        2.0
Release:        4%{?dist}
Summary:        Zolera SOAP Infrastructure
Group:          Development/Languages
# to obtain some license information have a look at ZSI/__init__.py file
License:        MIT and LBNL BSD and ZPLv2.0
URL:            http://pywebsvcs.sourceforge.net/
Source0:        http://belnet.dl.sourceforge.net/sourceforge/pywebsvcs/ZSI-%{version}.tar.gz
Patch0:         ZSI_v2_0_0_SVN.patch
Patch1:         python-ZSI-2.0-socket-error.patch
Patch2:         python-ZSI-2.0-no_egg_PyXML.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python-devel python-setuptools
Requires:       PyXML

%description
The Zolara SOAP Infrastructure provides libraries for developing web services
using the python programming language. The libraries implement the various
protocols used when writing web services including SOAP, WSDL, and other
related protocols.

%prep
%setup -q -n ZSI-%{version}
%patch0 -p1 -b .ZSI_v2_0_0_SVN
%patch1 -p1 -b .socket_error
%patch2 -p1 -b .no_egg_PyXML.patch

# remove cvs and svn internal files and
# get rid of executable perm due to rpmlint's
# warnings like: 
# W: python-zsi spurious-executable-perm
#

find . -name .cvsignore -exec rm {} \; ; exit 0
find . -name CVS -type d -exec rm -rf {} \; ; exit 0
find . -name .svn -type d -exec rm -rf {} \; ; exit 0
find doc/examples samples -perm 755 -type f -exec chmod a-x {} \;

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
mkdir $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# some files have shebang and aren't executable
# the simple command below looks for them and if
# they're found, it'll do chmod a+x

find $RPM_BUILD_ROOT%{python_sitelib}/ZSI \
    -type f -perm 644 -name \*.py \
    -exec grep -q \#\!\.\*python {} \; \
    -and -exec chmod a+x {} \;
 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
# we need png's for html's to be more readable
%doc CHANGES README samples doc/examples doc/*.html doc/*.png doc/*.css
%{_bindir}/wsdl2dispatch
%{_bindir}/wsdl2py
%{python_sitelib}/ZSI
%{python_sitelib}/ZSI-*.egg-info


%changelog
* Fri Jan 04 2008 Michał Bentkowski <mr.ecik at gmail.com> - 2.0-3
- Just bumping...

* Sat Dec 29 2007 Michał Bentkowski <mr.ecik at gmail.com> - 2.0-2
- Fix License field (BSD to LBNL BSD)

* Thu Nov 01 2007 Michał Bentkowski <mr.ecik at gmail.com> - 2.0-1
- First release

