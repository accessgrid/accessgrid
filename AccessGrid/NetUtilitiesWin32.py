#-----------------------------------------------------------------------------
# Name:        NetUtilitiesWin32.py
# Purpose:     Utility routines for network manipulation, win32 specific.
#
# Author:      Robert Olson
#
# Created:     9/11/2003
# RCS-ID:      $Id: NetUtilitiesWin32.py,v 1.1 2003-09-11 21:37:27 olson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

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

if __name__ == "__main__":

    print GetHTTPProxyAddresses()
