#-----------------------------------------------------------------------------
# Name:        UrllibTransport.py
# Purpose:     Transport class for doing xmlrpc through a proxy server
# Created:     2006/03/08
# RCS-ID:      $Id: UrllibTransport.py,v 1.1 2006-03-08 20:04:16 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------


import xmlrpclib
#
# The following code is from:
# http://starship.python.net/crew/jjkunce/python/xmlrpc_urllib_transport.py
#
class UrllibTransport(xmlrpclib.Transport):
	'''Handles an HTTP transaction to an XML-RPC server via urllib
	(urllib includes proxy-server support)
	jjk  07/02/99'''

        def __init__(self, proxy):
            self.proxy = proxy

	def request(self, host, handler, request_body, verbose = None):
		'''issue XML-RPC request
		jjk  07/02/99'''
		import urllib
		self.verbose = verbose
                urlopener = urllib.URLopener(proxies = {"http": self.proxy})
		urlopener.addheaders = [('User-agent', self.user_agent)]
		# probably should use appropriate 'join' methods instead of 'http://'+host+handler
		f = urlopener.open('http://'+host+handler, request_body)
		return(self.parse_response(f))


