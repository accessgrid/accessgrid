%define name		AccessGrid-rat
%define version		4.2.22
%define release		1
%define prefix		/usr
%define sysconfdir	/etc
%define buildroot	/var/tmp/%{name}-%{version}

Summary:	UCL rat
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	distributable
Group:		Applications/Multimedia
Source0:	rat-%version.tar.gz
URL:		http://www-mice.cs.ucl.ac.uk/multimedia/software/
BuildRoot:	%{buildroot}

%description
UCL rat is a unicast and multicast audio conferencing tool.

%prep 
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}
%setup -n rat-%{version}

%build
(cd common; ./configure; make)
(cd tcl-8.0/unix; ./configure; make)
(cd tk-8.0/unix; ./configure; make)
(cd rat; ./configure --prefix=%{buildroot}%{prefix} --sysconfdir=%{buildroot}%{sysconfdir}; make)

%install
mkdir -p %{buildroot}%{prefix}/bin
mkdir -p %{buildroot}%{sysconfdir}
(cd rat; make install)

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/bin
/etc
/usr/man

%changelog

* Thu Feb 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Picked up RPM packaging
- Cleaned up this file
