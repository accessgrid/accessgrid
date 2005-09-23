#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        GroupMsgDefines.py
# Purpose:     Common definitions for GroupMsgService and GroupMsgClient
# Created:     2005/09/09
# RCS-ID:      $Id: GroupMsgDefines.py,v 1.1 2005-09-23 22:08:17 eolson Exp $
# Copyright:   (c) 2005 
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import struct

class NotConnectedException(Exception):
    """
    This exception is used to indicate a connection has not yet
    been made.
    """
    pass

class GroupDoesNotExistException(Exception):
    """
    This exception is used to indicate the group/channel does
    not exist in the Group Service.
    """

class IncompatibleVersionException(Exception):
    """
    This exception is used to indicate the group/channel protocol
    version is not supported.
    """

class UnspecifiedErrorException(Exception):
    """
    This exception is used to indicate the no information about
    the error was provided.
    """

class ServerUnableToSendException(Exception):
    """
    This exception is used to indicate the server was unable to 
    send a message for an unknown reason.
    """

class ClientNotInGroupException(Exception):
    """
    This exception is used to indicate the client is not in
    a group.  It will likely occur if the client tries to send a
    message before finishing the handshake and joining a group.
    """

class GeneralReceivedErrorException(Exception):
    """
    This exception is used when a specific exception does not
    exist for the error code.
    """

class ERROR:
    '''
    Error codes for messages
    '''
    UNKNOWN                = 0x00
    NO_SUCH_GROUP          = 0x01
    SERVER_UNABLE_TO_SEND  = 0x02
    CLIENT_NOT_IN_GROUP    = 0x03


def PackUByte(value):
    return struct.pack("!c", value)

def UnpackUByte(value):
    return struct.pack("!c", value)

