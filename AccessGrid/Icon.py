#-----------------------------------------------------------------------------
# Name:        Icon.py
# Purpose:     This encapsulates an icon for the Access Grid Toolkit.
#
# Author:      Ivan R. Judson
#
# Created:     2002/11/12
# RCS-ID:      $Id: Icon.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class Icon:
    __doc__ = """
    An icon is an icon, and we create this python class to enable a wider range
    of raw image types in the icons. Each Icon has three parts:
        type : the file type of the encoded data
        name : the suggested name of the icon when decoded
        data : the base64 encoded image data
    """
        
    type = ""
    name = ""
    data = ""
    
    def __init__(self, name):
        __doc__ = """
        Icon constructor, you only have to specify a filename name/url to the
        icon we'll try to figure out the type from there and we encoded it
        internally.
        """
        self.name = name
        # Dynamically determine type from mime types?
        # base 64 encode the data

    def SetType(self, type):
        __doc__ = """
        SetType sets the type of the icon. Types are mimetypes.
        """
        self.type = type
        
    def GetType(self):
        __doc__ = """
        GetType gets the type of the icon. Types are mimetypes.
        """
        return self.type
    
    def SetName(self, name):
        __doc__ = """
        SetName sets the suggested name of the icon after it is decoded.
        """
        self.name = name
        
    def GetName(self):
        __doc__ = """
        GetName gets the suggested name of the icon.
        """
        return self.name
    
    def SetData(self, data):
        __doc__ = """
        SetData sets the base64 encoded data attribute.
        """
        data = data
    
    def GetData(self):
        __doc__ = """
        GetData gets the base64 encoded data attribute.
        """
        return data