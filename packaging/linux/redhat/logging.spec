%define	name		logging
%define	version		0.4.7
%define	release		2
%define	prefix		/usr
%define sharedir	%{prefix}/share
%define docdir		%{sharedir}/doc/%{name}-%{version}
%define buildroot	/var/tmp/%{name}-%{version}

Summary:	The Python logging module
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	distributable
Group:		Utilities/System
URL:		http://www.red-dove.com/python_logging.html 
Packager:	Argonne National Laboratory
Source:		%{name}-%{version}.tar.gz
BuildRoot:	%{buildroot}
Requires:	/usr/bin/python2.2
BuildRequires:	/usr/bin/python2.2


%description
logging is the python logging module. It handles logging to system dependent logfiles.

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%build
python2.2 ./setup.py build

%install
python2.2 ./setup.py install --prefix="%{buildroot}%{prefix}" --no-compile
mkdir -p %{buildroot}%{docdir}
cp default.css liblogging.tex python_logging.html PKG-INFO README.txt %{buildroot}%{docdir}

%files
%defattr(-,root,root)
/usr/lib
%doc %{docdir}/*

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog

* Thu Apr 03 2003 Ti Leggett <leggett@mcs.anl.gov>
- Added copying of documentation

* Tue Jan 28 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created
