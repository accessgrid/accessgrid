#-----------------------------------------------------------------------------
# Name:        Icon.py
# Purpose:     This encapsulates an icon for the Access Grid Toolkit.
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Icon.py,v 1.3 2003-03-29 23:37:39 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class Icon:
    """
    An icon is an icon, and we create this python class to enable a wider range
    of raw image types in the icons. Each Icon has three parts:
        type : the file type of the encoded data
        name : the suggested name of the icon when decoded
        data : the base64 encoded image data
    """
    def __init__(self, name):
        """
        Icon constructor, you only have to specify a filename name/url to the
        icon we'll try to figure out the type from there and we encoded it
        internally.
        """
        self.name = name
        # Dynamically determine type from mime types?
        self.type = ""
        # base 64 encode the data
        self.data = ""

    def SetType(self, type):
        """
        SetType sets the type of the icon. Types are mimetypes.
        """
        self.type = type
        
    def GetType(self):
        """
        GetType gets the type of the icon. Types are mimetypes.
        """
        return self.type
    
    def SetName(self, name):
        """
        SetName sets the suggested name of the icon after it is decoded.
        """
        self.name = name
        
    def GetName(self):
        """
        GetName gets the suggested name of the icon.
        """
        return self.name
    
    def SetData(self, data):
        """
        SetData sets the base64 encoded data attribute.
        """
        self.data = data
    
    def GetData(self):
        """
        GetData gets the base64 encoded data attribute.
        """
        return self.data

    def GetRawData(self):
        """
        GetRawData returns the base64 decoded data.
        """
