%define	name		SharedBrowser
%define	version		1.0
%define	release		1
%define	prefix		/usr
%define sharedir	%{prefix}/share/AccessGrid/applications/%{name}
%define buildroot	/var/tmp/%{name}-%{version}

Summary:	Access Grid Shared Browser Application
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	AGTPL
Group:		Utilities/System
URL:		http://www.mcs.anl.gov/fl/research/accessgrid
Vendor:		Argonne National Laboratory
Source:		%{name}-%{version}.tar.gz
BuildRoot:	%{buildroot}
Requires:	/usr/bin/python2.2
Requires:	AccessGrid

%description
SharedBrowser is a Access Grid 2.0 shared browser application.

%prep
%setup
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%install
mkdir -p %{buildroot}%{sharedir}
cp %{name}.py %{buildroot}%{sharedir}
cp %{name}.app %{buildroot}%{sharedir}

%files
%defattr(-,root,root)
%{sharedir}/*

%post
/usr/bin/MailcapSetup.py --system --mime-type "application/x-ag-shared-browser" --executable "%{sharedir}/SharedBrowser.py %s" --description "This is the shared browser application" --nametemplate "%s.sharedbrowser"

%postun
/usr/bin/MailcapSetup.py --system --uninstall --mime-type "application/x-ag-shared-browser"

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%changelog

* Fri May 16 2003 Ti Leggett <leggett@mcs.anl.gov>
- This file was created

