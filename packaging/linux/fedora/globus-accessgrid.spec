%define	name		globus-accessgrid
%define	version		2.4
%define	release		6
%define	prefix		/usr/lib/globus
%define buildroot	/var/tmp/%{name}-%{version}

%define has_ld_so_conf_d %([ -d /etc/ld.so.conf.d ] && echo 1 || echo 0)

Summary:	The Globus Toolkit
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	GTPL
Group:		System Environment/Libraries
URL:		http://www.globus.org/toolkit/
Vendor:		Argonne National Laboratory
BuildRoot:	%{buildroot}
BuildRequires:  gpt

%description
Globus is an open implementation of the grid framework

%prep
rm -rf %{buildroot}
if [ -z "${AGBUILDROOT}" ]; then
    echo "Error: AGBUILDROOT environment variable must be set"
    exit 1
fi

%build
. /etc/profile.d/gpt.sh
export GLOBUS_LOCATION=%{buildroot}%{prefix}

##
# Globus Data Management Client
${GPT_LOCATION}/sbin/gpt-build ${AGBUILDROOT}/gt3.0.2-source-installer/globus-data-management-client-2.4.3-src_bundle.tar.gz gcc32dbgpthr
(cd ${GLOBUS_LOCATION}/setup/globus/ ; ./setup-globus-common ; ./setup-ssl-utils)

##
# Fix der_chop from openssl from using the not right /usr/local/bin/perl and instead use /usr/bin/perl
sed -e 's,/usr/local/bin/perl,/usr/bin/perl,g' < %{buildroot}%{prefix}/bin/der_chop > %{buildroot}%{prefix}/bin/der_chop.sed
mv -f %{buildroot}%{prefix}/bin/der_chop.sed %{buildroot}%{prefix}/bin/der_chop
chmod 0755 %{buildroot}%{prefix}/bin/der_chop
cp -f -p %{buildroot}%{prefix}/bin/der_chop %{buildroot}%{prefix}/bin/gcc32dbgpthr/shared/der_chop

%install
mkdir -p %{buildroot}/etc/profile.d

cat <<EOF > %{buildroot}/etc/profile.d/globus.sh
#!/bin/sh
GLOBUS_LOCATION=%{prefix}
export GLOBUS_LOCATION

. \${GLOBUS_LOCATION}/etc/globus-user-env.sh
EOF

cat <<EOF > %{buildroot}/etc/profile.d/globus.csh
#!/bin/csh
setenv GLOBUS_LOCATION %{prefix}

source \${GLOBUS_LOCATION}/etc/globus-user-env.csh
EOF

chmod 0755 %{buildroot}/etc/profile.d/globus.*

%if %{has_ld_so_conf_d}
  mkdir -p %{buildroot}/etc/ld.so.conf.d
  echo "%{prefix}/lib" > %{buildroot}/etc/ld.so.conf.d/globus.conf
  chmod 0644 %{buildroot}/etc/ld.so.conf.d/globus.conf
%endif

%clean
rm -rf %{buildroot}

%post
%if !%{has_ld_so_conf_d}
  FNAME=`mktemp /etc/ld.so.conf.XXXXXX`
  grep -v "%{prefix}/lib" /etc/ld.so.conf > ${FNAME}
  echo "%{prefix}/lib" >> ${FNAME}
  cat ${FNAME} > /etc/ld.so.conf
  rm -f ${FNAME}
%endif
/sbin/ldconfig

%postun
%if !%{has_ld_so_conf_d}
if [ $1 = 0 ]; then
  FNAME=`mktemp /etc/ld.so.conf.XXXXXX`
  grep -v "%{prefix}/lib" /etc/ld.so.conf > ${FNAME}
  cat ${FNAME} > /etc/ld.so.conf
  rm -f ${FNAME}
fi
%endif
/sbin/ldconfig

%files
%defattr(-,root,root)
/usr/lib/globus
/etc/profile.d/*
%if %{has_ld_so_conf_d}
  /etc/ld.so.conf.d/*
%endif
