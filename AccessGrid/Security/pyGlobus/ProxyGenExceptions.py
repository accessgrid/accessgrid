"""
Exceptions that the proxy generation procedures might raise.
"""

class ProxyRequestError(Exception):
    """
    Baseclass for proxy generation exceptions.
    """
    pass

class PassphraseRequestCancelled(ProxyRequestError):
    """
    The user cancelled this request.
    """
    pass

class InvalidPassphraseException(ProxyRequestError):
    """
    The user entered an invalid passphrase.
    """
    pass

class GridProxyInitError(ProxyRequestError):
    """
    Some other error has occured. The description is in
    exception.args[0].
    """
    pass

class GridProxyInitUnknownSSLError(ProxyRequestError):
    """
    We've received an exception that don't understand.

    Pass along the SSL error queue as args[0], any
    "certificate:" data as args[1].
    """
    pass

