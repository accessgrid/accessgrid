%define name		AccessGrid-rat
%define version		4.2.22
%define release		1
%define prefix		/usr
%define buildroot	/var/tmp/%{name}-%{version}

Summary:	UCL rat
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	distributable
Group:		Applications/Multimedia
Source0:	rat-%{version}.tar.gz
URL:		http://www-mice.cs.ucl.ac.uk/multimedia/software/
Patch0:		rat-4.2.22.bobdif
BuildRoot:	%{buildroot}

%description
UCL rat is a unicast and multicast audio conferencing tool.

%prep 
%setup -n rat-%{version}
%patch0 -p1

%build
(cd common; ./configure; make)
(cd tcl-8.0/unix; ./configure; make)
(cd tk-8.0/unix; ./configure; make)
(cd rat; ./configure --prefix=%{buildroot}%{version}; make)

%install
(cd rat; make install)

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
/usr/bin/rat

%changelog

* Thu Feb 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Picked up RPM packaging
- Cleaned up this file
