#-----------------------------------------------------------------------------
# Name:        NetUtilities.py
# Purpose:     Utility routines for network manipulation, win32 specific.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilities.py,v 1.1 2004-02-26 16:45:35 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NetUtilities.py,v 1.1 2004-02-26 16:45:35 judson Exp $"
__docformat__ = "restructuredtext en"


import string
import re
import os
import os.path
import sys
import _winreg

__all__ = ["GetHTTPProxyAddresses"]

def GetHTTPProxyAddresses():
    """
    If the system has a proxy server defined for use, return its address.

    The return value is actually a list of tuples (server address, enabled).

    There are at least two places to look for these values.

    WinHttp defines  a proxy at

  HKEY_LOCAL_MACHINE\
    SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\Connections\
      WinHttpSettings :

    Unfortunately it stores its value as a binary string; it's meant to be
    accessed via the WinHttpGetDefaultProxyConfiguration call or by the
    proxycfg.exe program. For now, we'll just use the IE setting:

    IE defines a proxy at

    HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings

    The key ProxyServer has the name of the proxy, and ProxyEnable is nonzero
    if it is enabled for use.

    """

    proxies = []
    ieProxy = GetIEProxyAddress()

    if ieProxy is not None:
        proxies.append(ieProxy)

    return proxies

def GetIEProxyAddress():
    """
    Retrieve Internet Explorer's idea of a proxy server setting from
    HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings
    """

    k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")

    try:
        (val, type) = _winreg.QueryValueEx(k, "ProxyServer")

        proxyStr = str(val)

        if proxyStr.find(":") >= 0:
            #
            # We have hostname and port
            #
            proxy = proxyStr.split(":", 2)
        else:
            #
            # Just a hostname.
            #
            proxy = (proxyStr, None)

    except WindowsError:
        proxy = None

    #
    # Check to see if this proxy is enabled.
    #

    enabled = 0

    if proxy is None:
        return None

    try:
        (val, type) = _winreg.QueryValueEx(k, "ProxyEnable")

        enabled = val
    except WindowsError:
        pass

    return (proxy, enabled)

def EnumerateInterfaces():
    """
    Enumerate the interfaces present on a windows box.

    Run ipconfig /all

    """

    adapter_re = re.compile("^Ethernet adapter (.*):$")
    ip_re = re.compile("^\s*IP Address.*:\s+(\d+\.\d+\.\d+\.\d+)")
    dns_re = re.compile("^\s*DNS Servers.*:\s+(\S+)")

    ipconfig = os.path.join(os.getenv("SystemRoot"), "system32", "ipconfig.exe")
    p = os.popen(r"%s /all" % ipconfig, "r")
    # print "popen returns ", p

    adapters = []
    dns_servers = []

    for l in p:
        l = l.strip()
        m = adapter_re.search(l)
        if m is not None:
            cur_adapter = {'name': m.group(1),
                           'ip': None,
                           'dns': None}
            cur_adapter['name'] = m.group(1)
            adapters.append(cur_adapter)

        m = ip_re.search(l)
        if m is not None:
            # print "got Ip addr '%s'" % (m.group(1))
            cur_adapter['ip'] = m.group(1)

        m = dns_re.search(l)
        if m is not None:
            cur_adapter['dns'] = m.group(1)
            # print "got dns ", m.group(1)
            dns_servers.append(m.group(1))

    p.close()

    return adapters

def GetDefaultRouteIP():
    """
    Retrieve the IP address of the interface that the
    default route points to.
    """

    route = os.path.join(os.getenv("SystemRoot"), "system32", "route.exe")
    p = os.popen(r"%s print" % route, "r")

    for l in p:
        parts = l.split()
        if parts[0] == "0.0.0.0":
            int = parts[3]
            p.close()
            return int

    return None
    

if __name__ == "__main__":

    print EnumerateInterfaces()
    defroute = GetDefaultRouteIP()
    print "Default: ", defroute
    print GetHTTPProxyAddresses()
