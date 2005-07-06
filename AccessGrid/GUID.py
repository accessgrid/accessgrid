"""
Pyro Software License (MIT license):


      Pyro is Copyright (c) 2002  by Irmen de Jong.


      Permission is hereby granted, free of charge, to any person obtaining a copy of this
      software and associated documentation files (the "Software"), to deal in the Software
      without restriction, including without limitation the rights to use, copy, modify, merge,
      publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
      to whom the Software is furnished to do so, subject to the following conditions:

      The above copyright notice and this permission notice shall be included in all copies or
      substantial portions of the Software.

      THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
      INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
      PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
      FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
      OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
      DEALINGS IN THE SOFTWARE.
"""

#
# GUID code originally written by the Pyro project.
#   * 2004/07/06 Initial Import
#        Minor changes to move supporting functions into this file.
#

import os, sys, time, random

def supports_multithreading():
        try:
                from threading import Thread, Lock
                return 1
        except:
                return 0

# bogus lock class, for systems that don't have threads.
class BogusLock:
        def acquire(self): pass
        def release(self): pass

def getLockObject():
        if supports_multithreading():
                from threading import Lock
                return Lock()
        else:
                return BogusLock()

#------ Get the hostname (possibly of other machines) (returns None on error)
def getHostname(ip=None):
        try:
                if ip:
                        (hn,alias,ips) = socket.gethostbyaddr(ip)
                        return hn
                else:
                        return socket.gethostname()
        except socket.error:
                return None

#------ Get IP address (return None on error)
def getIPAddress(host=None):
        try:
                return socket.gethostbyname(host or getHostname())
        except socket.error:
                return None

_getGUID_counter=0              # extra safeguard against double numbers
_getGUID_lock=getLockObject()

if os.name=='java':
        def getGUID():
                # Jython uses java's own ID routine used by RMI
                import java.rmi.dgc
                return java.rmi.dgc.VMID().toString().replace(':','-')
else:
        import socket, binascii
        def getGUID():
                # Generate readable GUID string.
                # The GUID is constructed as follows: hexlified string of
                # AAAAAAAA-AAAABBBB-BBBBBBBB-BBCCCCCC  (a 128-bit number in hex)
                # where A=network address, B=timestamp, C=random. 
                # The 128 bit number is returned as a string of 16 8-bits characters.
                # For A: should use the machine's MAC ethernet address, but there is no
                # portable way to get it... use the IP address + 2 bytes process id.

                ip=getIPAddress()
                if ip:
                        networkAddrStr=binascii.hexlify(socket.inet_aton(ip))+"%04x" % os.getpid()
                else:
                        # can't get IP address... use another value, like our Python id() and PID
                        Log.warn('getGUID','Can\'t get IP address')
                        try:
                                ip=os.getpid()
                        except:
                                ip=0
                        ip += id(getGUID)
                        networkAddrStr = "%08lx%04x" % (ip, os.getpid())

                _getGUID_lock.acquire()  # cannot generate multiple GUIDs at once
                global _getGUID_counter
                t1=time.time()*100 +_getGUID_counter
                _getGUID_counter+=1
                _getGUID_lock.release()
                t2=int((t1*time.clock())%sys.maxint) & 0xffffff
                t1=int(t1%sys.maxint)
                timestamp = (long(t1) << 24) | t2
                r2=(random.randint(0,sys.maxint/2)>>4) & 0xffff
                r3=(random.randint(0,sys.maxint/2)>>5) & 0xff
                return networkAddrStr+'%014x%06x' % (timestamp, (r2<<8)|r3 )

GUID = getGUID

if __name__ == "__main__":
  # just print out a for testing
  guid = getGUID()
  print "GUID: " + guid

