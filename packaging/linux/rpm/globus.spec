%define	name		globus-accessgrid
%define	version		2.4
%define	release		3
%define	prefix		/usr/lib/globus
%define buildroot	/var/tmp/%{name}-%{version}

Summary:	The Globus Toolkit
Name:		%{name}
Version:	%{version}
Release:	%{release}
Copyright:	GTPL
Group:		System Environment/Libraries
URL:		http://www.globus.org
Vendor:		Argonne National Laboratory
BuildRoot:	%{buildroot}
Obsoletes:	globus-data-management-gcc32pthr
BuildRequires:  gpt
#Source0:	globus-data-management-client-2.4.3-src_bundle.tar.gz

%description
Globus is an open implementation of the grid framework

%prep
#[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}
/bin/true

%build
. /etc/profile.d/gpt.sh
export GLOBUS_LOCATION=%{buildroot}%{prefix}

##
# Globus Data Management Client
${GPT_LOCATION}/sbin/gpt-build ${AGBUILDROOT}/gt3.0.2-source-installer/globus-data-management-client-2.4.3-src_bundle.tar.gz gcc32pthr
${GPT_LOCATION}/sbin/gpt-verify
(cd ${GLOBUS_LOCATION}/setup/globus/ ; ./setup-globus-common )

##
# Fix der_chop from openssl from using the not right /usr/local/bin/perl and instead use /usr/bin/perl
sed -e 's,/usr/local/bin/perl,/usr/bin/perl,g' < %{buildroot}%{prefix}/bin/der_chop > %{buildroot}%{prefix}/bin/der_chop.sed
mv -f %{buildroot}%{prefix}/bin/der_chop.sed %{buildroot}%{prefix}/bin/der_chop
chmod 0755 %{buildroot}%{prefix}/bin/der_chop
cp -f -p %{buildroot}%{prefix}/bin/der_chop %{buildroot}%{prefix}/bin/gcc32pthr/shared/der_chop

%files
%defattr(-,root,root)
/usr/lib/globus

%post
GLOBUS_LOCATION=%{prefix}
/sbin/ldconfig $GLOBUS_LOCATION/lib

cat <<EOF > /etc/profile.d/globus.sh
#!/bin/sh
GLOBUS_LOCATION=%{prefix}
export GLOBUS_LOCATION

. \${GLOBUS_LOCATION}/etc/globus-user-env.sh
EOF

cat <<EOF > /etc/profile.d/globus.csh
#!/bin/csh
setenv GLOBUS_LOCATION %{prefix}

source \${GLOBUS_LOCATION}/etc/globus-user-env.csh
EOF

chmod 0755 /etc/profile.d/globus.*

%postun
/sbin/ldconfig

if [ "$1" = "0" ] ; then # last uninstall
    if [ -f /etc/profile.d/globus.sh ]; then
        rm -f /etc/profile.d/globus.sh
    fi

    if [ -f /etc/profile.d/globus.csh ]; then
        rm -f /etc/profile.d/globus.csh
    fi
fi

%clean
[ -n "%{buildroot}" -a "%{buildroot}" != / ] && rm -rf %{buildroot}
