%define name		AccessGrid-vic
%define version		2.8ucl1.1.3
%define release		1
%define prefix		/usr
%define buildroot	/var/tmp/%{name}-%{version}
%define snapshot	2003-0212

Summary:	UCL vic
Name:		%{name}
Version:	%{version}
Release:	%{release}
Group:		Applications/Multimedia
Copyright:	distributable
Source0:	vic-%{snapshot}.tar.gz
URL:		http://www-mice.cs.ucl.ac.uk/multimedia/software
BuildRoot:	%{buildroot}

%description
UCL vic is a unicast and multicast videoconferencing phone.

%prep 
%setup -n ag-vic

%build
(cd tcl-8.0/unix; ./configure; make)
(cd tk-8.0/unix; ./configure; make)
(cd common; ./configure; make)
(cd vic; ./configure --prefix=%{buildroot}%{prefix}; make)

%install
mkdir -p %{buildroot}%{prefix}/bin
(cd vic; make install)

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}

%files
/usr/bin/vic

%changelog

* Thu Feb 13 2003 Ti Leggett <leggett@mcs.anl.gov>
- Changed the name

* Wed Feb 12 2003 Ti Leggett <leggett@mcs.anl.gov>
- Picked up RPM packaging
- Cleaned up this file
