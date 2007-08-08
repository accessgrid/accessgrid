--- wxPython/contrib/mozilla25/wx/mozilla.py.wxPython28	2005-05-07 04:41:53.000000000 +1000
+++ wxPython/contrib/mozilla25/wx/mozilla.py	2007-07-20 12:17:49.000000000 +1000
@@ -1,18 +1,18 @@
-# This file was created automatically by SWIG.
+# This file was created automatically by SWIG 1.3.29.
 # Don't modify this file, modify the SWIG interface instead.
 
 import _mozilla
-
+import new
+new_instancemethod = new.instancemethod
 def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
+    if (name == "thisown"): return self.this.own(value)
     if (name == "this"):
-        if isinstance(value, class_type):
-            self.__dict__[name] = value.this
-            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
-            del value.thisown
+        if type(value).__name__ == 'PySwigObject':
+            self.__dict__[name] = value
             return
     method = class_type.__swig_setmethods__.get(name,None)
     if method: return method(self,value)
-    if (not static) or hasattr(self,name) or (name == "thisown"):
+    if (not static) or hasattr(self,name):
         self.__dict__[name] = value
     else:
         raise AttributeError("You cannot add attributes to %s" % self)
@@ -21,10 +21,16 @@ def _swig_setattr(self,class_type,name,v
     return _swig_setattr_nondynamic(self,class_type,name,value,0)
 
 def _swig_getattr(self,class_type,name):
+    if (name == "thisown"): return self.this.own()
     method = class_type.__swig_getmethods__.get(name,None)
     if method: return method(self)
     raise AttributeError,name
 
+def _swig_repr(self):
+    try: strthis = "proxy of " + self.this.__repr__()
+    except: strthis = ""
+    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)
+
 import types
 try:
     _object = types.ObjectType
@@ -37,7 +43,8 @@ del types
 
 def _swig_setattr_nondynamic_method(set):
     def set_attr(self,name,value):
-        if hasattr(self,name) or (name in ("this", "thisown")):
+        if (name == "thisown"): return self.this.own(value)
+        if hasattr(self,name) or (name == "this"):
             set(self,name,value)
         else:
             raise AttributeError("You cannot add attributes to %s" % self)
@@ -51,17 +58,14 @@ wx = _core 
 __docfilter__ = wx.__DocFilter(globals()) 
 class MozillaBrowser(_core.Window):
     """Proxy of C++ MozillaBrowser class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaBrowser instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
-    def __init__(self, *args, **kwargs):
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
+    def __init__(self, *args, **kwargs): 
         """
         __init__(self, Window parent, int id, Point pos=DefaultPosition, Size size=DefaultSize, 
             long style=0, String name=PanelNameStr) -> MozillaBrowser
         """
-        newobj = _mozilla.new_MozillaBrowser(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
+        _mozilla.MozillaBrowser_swiginit(self,_mozilla.new_MozillaBrowser(*args, **kwargs))
     def Create(*args, **kwargs):
         """
         Create(self, Window parent, int id, Point pos=DefaultPosition, Size size=DefaultSize, 
@@ -196,13 +200,7 @@ class MozillaBrowser(_core.Window):
         """SetZoom(self, float level) -> bool"""
         return _mozilla.MozillaBrowser_SetZoom(*args, **kwargs)
 
-
-class MozillaBrowserPtr(MozillaBrowser):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaBrowser
-_mozilla.MozillaBrowser_swigregister(MozillaBrowserPtr)
+_mozilla.MozillaBrowser_swigregister(MozillaBrowser)
 cvar = _mozilla.cvar
 MOZ_MAJOR_VERSION = cvar.MOZ_MAJOR_VERSION
 MOZ_MINOR_VERSION = cvar.MOZ_MINOR_VERSION
@@ -210,28 +208,19 @@ MOZ_RELEASE_NUMBER = cvar.MOZ_RELEASE_NU
 
 class MozillaWindow(_windows.Frame):
     """Proxy of C++ MozillaWindow class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaWindow instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
-    def __init__(self, *args, **kwargs):
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
+    def __init__(self, *args, **kwargs): 
         """__init__(self, bool showMenu=True, bool showToolbar=True, bool showStatusbar=True) -> MozillaWindow"""
-        newobj = _mozilla.new_MozillaWindow(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
+        _mozilla.MozillaWindow_swiginit(self,_mozilla.new_MozillaWindow(*args, **kwargs))
     Mozilla = property(_mozilla.MozillaWindow_Mozilla_get, _mozilla.MozillaWindow_Mozilla_set)
-
-class MozillaWindowPtr(MozillaWindow):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaWindow
-_mozilla.MozillaWindow_swigregister(MozillaWindowPtr)
+_mozilla.MozillaWindow_swigregister(MozillaWindow)
 
 class MozillaSettings(object):
     """Proxy of C++ MozillaSettings class"""
-    def __init__(self): raise RuntimeError, "No constructor defined"
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaSettings instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    def __init__(self): raise AttributeError, "No constructor defined"
+    __repr__ = _swig_repr
     def SetProfilePath(*args, **kwargs):
         """SetProfilePath(String path) -> bool"""
         return _mozilla.MozillaSettings_SetProfilePath(*args, **kwargs)
@@ -287,57 +276,51 @@ class MozillaSettings(object):
         return _mozilla.MozillaSettings_SavePrefs(*args, **kwargs)
 
     SavePrefs = staticmethod(SavePrefs)
-
-class MozillaSettingsPtr(MozillaSettings):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaSettings
-_mozilla.MozillaSettings_swigregister(MozillaSettingsPtr)
+_mozilla.MozillaSettings_swigregister(MozillaSettings)
 
 def MozillaSettings_SetProfilePath(*args, **kwargs):
-    """MozillaSettings_SetProfilePath(String path) -> bool"""
-    return _mozilla.MozillaSettings_SetProfilePath(*args, **kwargs)
+  """MozillaSettings_SetProfilePath(String path) -> bool"""
+  return _mozilla.MozillaSettings_SetProfilePath(*args, **kwargs)
 
-def MozillaSettings_GetProfilePath(*args, **kwargs):
-    """MozillaSettings_GetProfilePath() -> String"""
-    return _mozilla.MozillaSettings_GetProfilePath(*args, **kwargs)
+def MozillaSettings_GetProfilePath(*args):
+  """MozillaSettings_GetProfilePath() -> String"""
+  return _mozilla.MozillaSettings_GetProfilePath(*args)
 
 def MozillaSettings_SetMozillaPath(*args, **kwargs):
-    """MozillaSettings_SetMozillaPath(String path)"""
-    return _mozilla.MozillaSettings_SetMozillaPath(*args, **kwargs)
+  """MozillaSettings_SetMozillaPath(String path)"""
+  return _mozilla.MozillaSettings_SetMozillaPath(*args, **kwargs)
 
-def MozillaSettings_GetMozillaPath(*args, **kwargs):
-    """MozillaSettings_GetMozillaPath() -> String"""
-    return _mozilla.MozillaSettings_GetMozillaPath(*args, **kwargs)
+def MozillaSettings_GetMozillaPath(*args):
+  """MozillaSettings_GetMozillaPath() -> String"""
+  return _mozilla.MozillaSettings_GetMozillaPath(*args)
 
 def MozillaSettings_SetBoolPref(*args, **kwargs):
-    """MozillaSettings_SetBoolPref(String name, bool value)"""
-    return _mozilla.MozillaSettings_SetBoolPref(*args, **kwargs)
+  """MozillaSettings_SetBoolPref(String name, bool value)"""
+  return _mozilla.MozillaSettings_SetBoolPref(*args, **kwargs)
 
 def MozillaSettings_GetBoolPref(*args, **kwargs):
-    """MozillaSettings_GetBoolPref(String name) -> bool"""
-    return _mozilla.MozillaSettings_GetBoolPref(*args, **kwargs)
+  """MozillaSettings_GetBoolPref(String name) -> bool"""
+  return _mozilla.MozillaSettings_GetBoolPref(*args, **kwargs)
 
 def MozillaSettings_SetStrPref(*args, **kwargs):
-    """MozillaSettings_SetStrPref(String name, String value)"""
-    return _mozilla.MozillaSettings_SetStrPref(*args, **kwargs)
+  """MozillaSettings_SetStrPref(String name, String value)"""
+  return _mozilla.MozillaSettings_SetStrPref(*args, **kwargs)
 
 def MozillaSettings_GetStrPref(*args, **kwargs):
-    """MozillaSettings_GetStrPref(String name) -> String"""
-    return _mozilla.MozillaSettings_GetStrPref(*args, **kwargs)
+  """MozillaSettings_GetStrPref(String name) -> String"""
+  return _mozilla.MozillaSettings_GetStrPref(*args, **kwargs)
 
 def MozillaSettings_SetIntPref(*args, **kwargs):
-    """MozillaSettings_SetIntPref(String name, int value)"""
-    return _mozilla.MozillaSettings_SetIntPref(*args, **kwargs)
+  """MozillaSettings_SetIntPref(String name, int value)"""
+  return _mozilla.MozillaSettings_SetIntPref(*args, **kwargs)
 
 def MozillaSettings_GetIntPref(*args, **kwargs):
-    """MozillaSettings_GetIntPref(String name) -> int"""
-    return _mozilla.MozillaSettings_GetIntPref(*args, **kwargs)
+  """MozillaSettings_GetIntPref(String name) -> int"""
+  return _mozilla.MozillaSettings_GetIntPref(*args, **kwargs)
 
-def MozillaSettings_SavePrefs(*args, **kwargs):
-    """MozillaSettings_SavePrefs()"""
-    return _mozilla.MozillaSettings_SavePrefs(*args, **kwargs)
+def MozillaSettings_SavePrefs(*args):
+  """MozillaSettings_SavePrefs()"""
+  return _mozilla.MozillaSettings_SavePrefs(*args)
 
 MOZILLA_STATE_START = _mozilla.MOZILLA_STATE_START
 MOZILLA_STATE_NEGOTIATING = _mozilla.MOZILLA_STATE_NEGOTIATING
@@ -361,8 +344,8 @@ MOZILLA_CONTEXT_BACKGROUND_IMAGE = _mozi
 MOZILLA_CONTEXT_IMAGE = _mozilla.MOZILLA_CONTEXT_IMAGE
 class MozillaBeforeLoadEvent(_core.CommandEvent):
     """Proxy of C++ MozillaBeforeLoadEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaBeforeLoadEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetURL(*args, **kwargs):
         """GetURL(self) -> String"""
         return _mozilla.MozillaBeforeLoadEvent_GetURL(*args, **kwargs)
@@ -379,24 +362,15 @@ class MozillaBeforeLoadEvent(_core.Comma
         """IsCancelled(self) -> bool"""
         return _mozilla.MozillaBeforeLoadEvent_IsCancelled(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaBeforeLoadEvent"""
-        newobj = _mozilla.new_MozillaBeforeLoadEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaBeforeLoadEventPtr(MozillaBeforeLoadEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaBeforeLoadEvent
-_mozilla.MozillaBeforeLoadEvent_swigregister(MozillaBeforeLoadEventPtr)
+        _mozilla.MozillaBeforeLoadEvent_swiginit(self,_mozilla.new_MozillaBeforeLoadEvent(*args, **kwargs))
+_mozilla.MozillaBeforeLoadEvent_swigregister(MozillaBeforeLoadEvent)
 
 class MozillaLinkChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaLinkChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaLinkChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetNewURL(*args, **kwargs):
         """GetNewURL(self) -> String"""
         return _mozilla.MozillaLinkChangedEvent_GetNewURL(*args, **kwargs)
@@ -421,24 +395,15 @@ class MozillaLinkChangedEvent(_core.Comm
         """SetCanGoForward(self, bool goforward)"""
         return _mozilla.MozillaLinkChangedEvent_SetCanGoForward(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaLinkChangedEvent"""
-        newobj = _mozilla.new_MozillaLinkChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaLinkChangedEventPtr(MozillaLinkChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaLinkChangedEvent
-_mozilla.MozillaLinkChangedEvent_swigregister(MozillaLinkChangedEventPtr)
+        _mozilla.MozillaLinkChangedEvent_swiginit(self,_mozilla.new_MozillaLinkChangedEvent(*args, **kwargs))
+_mozilla.MozillaLinkChangedEvent_swigregister(MozillaLinkChangedEvent)
 
 class MozillaStateChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaStateChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaStateChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetState(*args, **kwargs):
         """GetState(self) -> int"""
         return _mozilla.MozillaStateChangedEvent_GetState(*args, **kwargs)
@@ -455,24 +420,15 @@ class MozillaStateChangedEvent(_core.Com
         """SetURL(self, String url)"""
         return _mozilla.MozillaStateChangedEvent_SetURL(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaStateChangedEvent"""
-        newobj = _mozilla.new_MozillaStateChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaStateChangedEventPtr(MozillaStateChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaStateChangedEvent
-_mozilla.MozillaStateChangedEvent_swigregister(MozillaStateChangedEventPtr)
+        _mozilla.MozillaStateChangedEvent_swiginit(self,_mozilla.new_MozillaStateChangedEvent(*args, **kwargs))
+_mozilla.MozillaStateChangedEvent_swigregister(MozillaStateChangedEvent)
 
 class MozillaSecurityChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaSecurityChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaSecurityChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetSecurity(*args, **kwargs):
         """GetSecurity(self) -> int"""
         return _mozilla.MozillaSecurityChangedEvent_GetSecurity(*args, **kwargs)
@@ -481,42 +437,24 @@ class MozillaSecurityChangedEvent(_core.
         """SetSecurity(self, int security)"""
         return _mozilla.MozillaSecurityChangedEvent_SetSecurity(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaSecurityChangedEvent"""
-        newobj = _mozilla.new_MozillaSecurityChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaSecurityChangedEventPtr(MozillaSecurityChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaSecurityChangedEvent
-_mozilla.MozillaSecurityChangedEvent_swigregister(MozillaSecurityChangedEventPtr)
+        _mozilla.MozillaSecurityChangedEvent_swiginit(self,_mozilla.new_MozillaSecurityChangedEvent(*args, **kwargs))
+_mozilla.MozillaSecurityChangedEvent_swigregister(MozillaSecurityChangedEvent)
 
 class MozillaLoadCompleteEvent(_core.CommandEvent):
     """Proxy of C++ MozillaLoadCompleteEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaLoadCompleteEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
-    def __init__(self, *args, **kwargs):
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaLoadCompleteEvent"""
-        newobj = _mozilla.new_MozillaLoadCompleteEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaLoadCompleteEventPtr(MozillaLoadCompleteEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaLoadCompleteEvent
-_mozilla.MozillaLoadCompleteEvent_swigregister(MozillaLoadCompleteEventPtr)
+        _mozilla.MozillaLoadCompleteEvent_swiginit(self,_mozilla.new_MozillaLoadCompleteEvent(*args, **kwargs))
+_mozilla.MozillaLoadCompleteEvent_swigregister(MozillaLoadCompleteEvent)
 
 class MozillaStatusChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaStatusChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaStatusChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetStatusText(*args, **kwargs):
         """GetStatusText(self) -> String"""
         return _mozilla.MozillaStatusChangedEvent_GetStatusText(*args, **kwargs)
@@ -533,24 +471,15 @@ class MozillaStatusChangedEvent(_core.Co
         """SetBusy(self, bool isbusy)"""
         return _mozilla.MozillaStatusChangedEvent_SetBusy(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaStatusChangedEvent"""
-        newobj = _mozilla.new_MozillaStatusChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaStatusChangedEventPtr(MozillaStatusChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaStatusChangedEvent
-_mozilla.MozillaStatusChangedEvent_swigregister(MozillaStatusChangedEventPtr)
+        _mozilla.MozillaStatusChangedEvent_swiginit(self,_mozilla.new_MozillaStatusChangedEvent(*args, **kwargs))
+_mozilla.MozillaStatusChangedEvent_swigregister(MozillaStatusChangedEvent)
 
 class MozillaTitleChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaTitleChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaTitleChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetTitle(*args, **kwargs):
         """GetTitle(self) -> String"""
         return _mozilla.MozillaTitleChangedEvent_GetTitle(*args, **kwargs)
@@ -559,24 +488,15 @@ class MozillaTitleChangedEvent(_core.Com
         """SetTitle(self, String title)"""
         return _mozilla.MozillaTitleChangedEvent_SetTitle(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaTitleChangedEvent"""
-        newobj = _mozilla.new_MozillaTitleChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaTitleChangedEventPtr(MozillaTitleChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaTitleChangedEvent
-_mozilla.MozillaTitleChangedEvent_swigregister(MozillaTitleChangedEventPtr)
+        _mozilla.MozillaTitleChangedEvent_swiginit(self,_mozilla.new_MozillaTitleChangedEvent(*args, **kwargs))
+_mozilla.MozillaTitleChangedEvent_swigregister(MozillaTitleChangedEvent)
 
 class MozillaProgressEvent(_core.CommandEvent):
     """Proxy of C++ MozillaProgressEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaProgressEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetSelfCurrentProgress(*args, **kwargs):
         """GetSelfCurrentProgress(self) -> int"""
         return _mozilla.MozillaProgressEvent_GetSelfCurrentProgress(*args, **kwargs)
@@ -609,24 +529,15 @@ class MozillaProgressEvent(_core.Command
         """SetTotalMaxProgress(self, int progress)"""
         return _mozilla.MozillaProgressEvent_SetTotalMaxProgress(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaProgressEvent"""
-        newobj = _mozilla.new_MozillaProgressEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaProgressEventPtr(MozillaProgressEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaProgressEvent
-_mozilla.MozillaProgressEvent_swigregister(MozillaProgressEventPtr)
+        _mozilla.MozillaProgressEvent_swiginit(self,_mozilla.new_MozillaProgressEvent(*args, **kwargs))
+_mozilla.MozillaProgressEvent_swigregister(MozillaProgressEvent)
 
 class MozillaRightClickEvent(_core.MouseEvent):
     """Proxy of C++ MozillaRightClickEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaRightClickEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def IsBusy(*args, **kwargs):
         """IsBusy(self) -> bool"""
         return _mozilla.MozillaRightClickEvent_IsBusy(*args, **kwargs)
@@ -675,19 +586,10 @@ class MozillaRightClickEvent(_core.Mouse
         """SetContext(self, int context)"""
         return _mozilla.MozillaRightClickEvent_SetContext(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaRightClickEvent"""
-        newobj = _mozilla.new_MozillaRightClickEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaRightClickEventPtr(MozillaRightClickEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaRightClickEvent
-_mozilla.MozillaRightClickEvent_swigregister(MozillaRightClickEventPtr)
+        _mozilla.MozillaRightClickEvent_swiginit(self,_mozilla.new_MozillaRightClickEvent(*args, **kwargs))
+_mozilla.MozillaRightClickEvent_swigregister(MozillaRightClickEvent)
 
 wxEVT_MOZILLA_BEFORE_LOAD = _mozilla.wxEVT_MOZILLA_BEFORE_LOAD
 wxEVT_MOZILLA_URL_CHANGED = _mozilla.wxEVT_MOZILLA_URL_CHANGED
@@ -711,3 +613,4 @@ EVT_MOZILLA_PROGRESS = wx.PyEventBinder(
 EVT_MOZILLA_RIGHT_CLICK = wx.PyEventBinder(wxEVT_MOZILLA_RIGHT_CLICK, 1)
 
 
+
--- wxPython/contrib/mozilla25/gtk/mozilla.py.wxPython28	2005-05-07 04:41:53.000000000 +1000
+++ wxPython/contrib/mozilla25/gtk/mozilla.py	2007-07-20 12:17:49.000000000 +1000
@@ -1,18 +1,18 @@
-# This file was created automatically by SWIG.
+# This file was created automatically by SWIG 1.3.29.
 # Don't modify this file, modify the SWIG interface instead.
 
 import _mozilla
-
+import new
+new_instancemethod = new.instancemethod
 def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
+    if (name == "thisown"): return self.this.own(value)
     if (name == "this"):
-        if isinstance(value, class_type):
-            self.__dict__[name] = value.this
-            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
-            del value.thisown
+        if type(value).__name__ == 'PySwigObject':
+            self.__dict__[name] = value
             return
     method = class_type.__swig_setmethods__.get(name,None)
     if method: return method(self,value)
-    if (not static) or hasattr(self,name) or (name == "thisown"):
+    if (not static) or hasattr(self,name):
         self.__dict__[name] = value
     else:
         raise AttributeError("You cannot add attributes to %s" % self)
@@ -21,10 +21,16 @@ def _swig_setattr(self,class_type,name,v
     return _swig_setattr_nondynamic(self,class_type,name,value,0)
 
 def _swig_getattr(self,class_type,name):
+    if (name == "thisown"): return self.this.own()
     method = class_type.__swig_getmethods__.get(name,None)
     if method: return method(self)
     raise AttributeError,name
 
+def _swig_repr(self):
+    try: strthis = "proxy of " + self.this.__repr__()
+    except: strthis = ""
+    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)
+
 import types
 try:
     _object = types.ObjectType
@@ -37,7 +43,8 @@ del types
 
 def _swig_setattr_nondynamic_method(set):
     def set_attr(self,name,value):
-        if hasattr(self,name) or (name in ("this", "thisown")):
+        if (name == "thisown"): return self.this.own(value)
+        if hasattr(self,name) or (name == "this"):
             set(self,name,value)
         else:
             raise AttributeError("You cannot add attributes to %s" % self)
@@ -51,17 +58,14 @@ wx = _core 
 __docfilter__ = wx.__DocFilter(globals()) 
 class MozillaBrowser(_core.Window):
     """Proxy of C++ MozillaBrowser class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaBrowser instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
-    def __init__(self, *args, **kwargs):
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
+    def __init__(self, *args, **kwargs): 
         """
         __init__(self, Window parent, int id, Point pos=DefaultPosition, Size size=DefaultSize, 
             long style=0, String name=PanelNameStr) -> MozillaBrowser
         """
-        newobj = _mozilla.new_MozillaBrowser(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
+        _mozilla.MozillaBrowser_swiginit(self,_mozilla.new_MozillaBrowser(*args, **kwargs))
     def Create(*args, **kwargs):
         """
         Create(self, Window parent, int id, Point pos=DefaultPosition, Size size=DefaultSize, 
@@ -196,13 +200,7 @@ class MozillaBrowser(_core.Window):
         """SetZoom(self, float level) -> bool"""
         return _mozilla.MozillaBrowser_SetZoom(*args, **kwargs)
 
-
-class MozillaBrowserPtr(MozillaBrowser):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaBrowser
-_mozilla.MozillaBrowser_swigregister(MozillaBrowserPtr)
+_mozilla.MozillaBrowser_swigregister(MozillaBrowser)
 cvar = _mozilla.cvar
 MOZ_MAJOR_VERSION = cvar.MOZ_MAJOR_VERSION
 MOZ_MINOR_VERSION = cvar.MOZ_MINOR_VERSION
@@ -210,28 +208,19 @@ MOZ_RELEASE_NUMBER = cvar.MOZ_RELEASE_NU
 
 class MozillaWindow(_windows.Frame):
     """Proxy of C++ MozillaWindow class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaWindow instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
-    def __init__(self, *args, **kwargs):
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
+    def __init__(self, *args, **kwargs): 
         """__init__(self, bool showMenu=True, bool showToolbar=True, bool showStatusbar=True) -> MozillaWindow"""
-        newobj = _mozilla.new_MozillaWindow(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
+        _mozilla.MozillaWindow_swiginit(self,_mozilla.new_MozillaWindow(*args, **kwargs))
     Mozilla = property(_mozilla.MozillaWindow_Mozilla_get, _mozilla.MozillaWindow_Mozilla_set)
-
-class MozillaWindowPtr(MozillaWindow):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaWindow
-_mozilla.MozillaWindow_swigregister(MozillaWindowPtr)
+_mozilla.MozillaWindow_swigregister(MozillaWindow)
 
 class MozillaSettings(object):
     """Proxy of C++ MozillaSettings class"""
-    def __init__(self): raise RuntimeError, "No constructor defined"
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaSettings instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    def __init__(self): raise AttributeError, "No constructor defined"
+    __repr__ = _swig_repr
     def SetProfilePath(*args, **kwargs):
         """SetProfilePath(String path) -> bool"""
         return _mozilla.MozillaSettings_SetProfilePath(*args, **kwargs)
@@ -287,57 +276,51 @@ class MozillaSettings(object):
         return _mozilla.MozillaSettings_SavePrefs(*args, **kwargs)
 
     SavePrefs = staticmethod(SavePrefs)
-
-class MozillaSettingsPtr(MozillaSettings):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaSettings
-_mozilla.MozillaSettings_swigregister(MozillaSettingsPtr)
+_mozilla.MozillaSettings_swigregister(MozillaSettings)
 
 def MozillaSettings_SetProfilePath(*args, **kwargs):
-    """MozillaSettings_SetProfilePath(String path) -> bool"""
-    return _mozilla.MozillaSettings_SetProfilePath(*args, **kwargs)
+  """MozillaSettings_SetProfilePath(String path) -> bool"""
+  return _mozilla.MozillaSettings_SetProfilePath(*args, **kwargs)
 
-def MozillaSettings_GetProfilePath(*args, **kwargs):
-    """MozillaSettings_GetProfilePath() -> String"""
-    return _mozilla.MozillaSettings_GetProfilePath(*args, **kwargs)
+def MozillaSettings_GetProfilePath(*args):
+  """MozillaSettings_GetProfilePath() -> String"""
+  return _mozilla.MozillaSettings_GetProfilePath(*args)
 
 def MozillaSettings_SetMozillaPath(*args, **kwargs):
-    """MozillaSettings_SetMozillaPath(String path)"""
-    return _mozilla.MozillaSettings_SetMozillaPath(*args, **kwargs)
+  """MozillaSettings_SetMozillaPath(String path)"""
+  return _mozilla.MozillaSettings_SetMozillaPath(*args, **kwargs)
 
-def MozillaSettings_GetMozillaPath(*args, **kwargs):
-    """MozillaSettings_GetMozillaPath() -> String"""
-    return _mozilla.MozillaSettings_GetMozillaPath(*args, **kwargs)
+def MozillaSettings_GetMozillaPath(*args):
+  """MozillaSettings_GetMozillaPath() -> String"""
+  return _mozilla.MozillaSettings_GetMozillaPath(*args)
 
 def MozillaSettings_SetBoolPref(*args, **kwargs):
-    """MozillaSettings_SetBoolPref(String name, bool value)"""
-    return _mozilla.MozillaSettings_SetBoolPref(*args, **kwargs)
+  """MozillaSettings_SetBoolPref(String name, bool value)"""
+  return _mozilla.MozillaSettings_SetBoolPref(*args, **kwargs)
 
 def MozillaSettings_GetBoolPref(*args, **kwargs):
-    """MozillaSettings_GetBoolPref(String name) -> bool"""
-    return _mozilla.MozillaSettings_GetBoolPref(*args, **kwargs)
+  """MozillaSettings_GetBoolPref(String name) -> bool"""
+  return _mozilla.MozillaSettings_GetBoolPref(*args, **kwargs)
 
 def MozillaSettings_SetStrPref(*args, **kwargs):
-    """MozillaSettings_SetStrPref(String name, String value)"""
-    return _mozilla.MozillaSettings_SetStrPref(*args, **kwargs)
+  """MozillaSettings_SetStrPref(String name, String value)"""
+  return _mozilla.MozillaSettings_SetStrPref(*args, **kwargs)
 
 def MozillaSettings_GetStrPref(*args, **kwargs):
-    """MozillaSettings_GetStrPref(String name) -> String"""
-    return _mozilla.MozillaSettings_GetStrPref(*args, **kwargs)
+  """MozillaSettings_GetStrPref(String name) -> String"""
+  return _mozilla.MozillaSettings_GetStrPref(*args, **kwargs)
 
 def MozillaSettings_SetIntPref(*args, **kwargs):
-    """MozillaSettings_SetIntPref(String name, int value)"""
-    return _mozilla.MozillaSettings_SetIntPref(*args, **kwargs)
+  """MozillaSettings_SetIntPref(String name, int value)"""
+  return _mozilla.MozillaSettings_SetIntPref(*args, **kwargs)
 
 def MozillaSettings_GetIntPref(*args, **kwargs):
-    """MozillaSettings_GetIntPref(String name) -> int"""
-    return _mozilla.MozillaSettings_GetIntPref(*args, **kwargs)
+  """MozillaSettings_GetIntPref(String name) -> int"""
+  return _mozilla.MozillaSettings_GetIntPref(*args, **kwargs)
 
-def MozillaSettings_SavePrefs(*args, **kwargs):
-    """MozillaSettings_SavePrefs()"""
-    return _mozilla.MozillaSettings_SavePrefs(*args, **kwargs)
+def MozillaSettings_SavePrefs(*args):
+  """MozillaSettings_SavePrefs()"""
+  return _mozilla.MozillaSettings_SavePrefs(*args)
 
 MOZILLA_STATE_START = _mozilla.MOZILLA_STATE_START
 MOZILLA_STATE_NEGOTIATING = _mozilla.MOZILLA_STATE_NEGOTIATING
@@ -361,8 +344,8 @@ MOZILLA_CONTEXT_BACKGROUND_IMAGE = _mozi
 MOZILLA_CONTEXT_IMAGE = _mozilla.MOZILLA_CONTEXT_IMAGE
 class MozillaBeforeLoadEvent(_core.CommandEvent):
     """Proxy of C++ MozillaBeforeLoadEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaBeforeLoadEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetURL(*args, **kwargs):
         """GetURL(self) -> String"""
         return _mozilla.MozillaBeforeLoadEvent_GetURL(*args, **kwargs)
@@ -379,24 +362,15 @@ class MozillaBeforeLoadEvent(_core.Comma
         """IsCancelled(self) -> bool"""
         return _mozilla.MozillaBeforeLoadEvent_IsCancelled(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaBeforeLoadEvent"""
-        newobj = _mozilla.new_MozillaBeforeLoadEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaBeforeLoadEventPtr(MozillaBeforeLoadEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaBeforeLoadEvent
-_mozilla.MozillaBeforeLoadEvent_swigregister(MozillaBeforeLoadEventPtr)
+        _mozilla.MozillaBeforeLoadEvent_swiginit(self,_mozilla.new_MozillaBeforeLoadEvent(*args, **kwargs))
+_mozilla.MozillaBeforeLoadEvent_swigregister(MozillaBeforeLoadEvent)
 
 class MozillaLinkChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaLinkChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaLinkChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetNewURL(*args, **kwargs):
         """GetNewURL(self) -> String"""
         return _mozilla.MozillaLinkChangedEvent_GetNewURL(*args, **kwargs)
@@ -421,24 +395,15 @@ class MozillaLinkChangedEvent(_core.Comm
         """SetCanGoForward(self, bool goforward)"""
         return _mozilla.MozillaLinkChangedEvent_SetCanGoForward(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaLinkChangedEvent"""
-        newobj = _mozilla.new_MozillaLinkChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaLinkChangedEventPtr(MozillaLinkChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaLinkChangedEvent
-_mozilla.MozillaLinkChangedEvent_swigregister(MozillaLinkChangedEventPtr)
+        _mozilla.MozillaLinkChangedEvent_swiginit(self,_mozilla.new_MozillaLinkChangedEvent(*args, **kwargs))
+_mozilla.MozillaLinkChangedEvent_swigregister(MozillaLinkChangedEvent)
 
 class MozillaStateChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaStateChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaStateChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetState(*args, **kwargs):
         """GetState(self) -> int"""
         return _mozilla.MozillaStateChangedEvent_GetState(*args, **kwargs)
@@ -455,24 +420,15 @@ class MozillaStateChangedEvent(_core.Com
         """SetURL(self, String url)"""
         return _mozilla.MozillaStateChangedEvent_SetURL(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaStateChangedEvent"""
-        newobj = _mozilla.new_MozillaStateChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaStateChangedEventPtr(MozillaStateChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaStateChangedEvent
-_mozilla.MozillaStateChangedEvent_swigregister(MozillaStateChangedEventPtr)
+        _mozilla.MozillaStateChangedEvent_swiginit(self,_mozilla.new_MozillaStateChangedEvent(*args, **kwargs))
+_mozilla.MozillaStateChangedEvent_swigregister(MozillaStateChangedEvent)
 
 class MozillaSecurityChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaSecurityChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaSecurityChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetSecurity(*args, **kwargs):
         """GetSecurity(self) -> int"""
         return _mozilla.MozillaSecurityChangedEvent_GetSecurity(*args, **kwargs)
@@ -481,42 +437,24 @@ class MozillaSecurityChangedEvent(_core.
         """SetSecurity(self, int security)"""
         return _mozilla.MozillaSecurityChangedEvent_SetSecurity(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaSecurityChangedEvent"""
-        newobj = _mozilla.new_MozillaSecurityChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaSecurityChangedEventPtr(MozillaSecurityChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaSecurityChangedEvent
-_mozilla.MozillaSecurityChangedEvent_swigregister(MozillaSecurityChangedEventPtr)
+        _mozilla.MozillaSecurityChangedEvent_swiginit(self,_mozilla.new_MozillaSecurityChangedEvent(*args, **kwargs))
+_mozilla.MozillaSecurityChangedEvent_swigregister(MozillaSecurityChangedEvent)
 
 class MozillaLoadCompleteEvent(_core.CommandEvent):
     """Proxy of C++ MozillaLoadCompleteEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaLoadCompleteEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
-    def __init__(self, *args, **kwargs):
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaLoadCompleteEvent"""
-        newobj = _mozilla.new_MozillaLoadCompleteEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaLoadCompleteEventPtr(MozillaLoadCompleteEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaLoadCompleteEvent
-_mozilla.MozillaLoadCompleteEvent_swigregister(MozillaLoadCompleteEventPtr)
+        _mozilla.MozillaLoadCompleteEvent_swiginit(self,_mozilla.new_MozillaLoadCompleteEvent(*args, **kwargs))
+_mozilla.MozillaLoadCompleteEvent_swigregister(MozillaLoadCompleteEvent)
 
 class MozillaStatusChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaStatusChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaStatusChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetStatusText(*args, **kwargs):
         """GetStatusText(self) -> String"""
         return _mozilla.MozillaStatusChangedEvent_GetStatusText(*args, **kwargs)
@@ -533,24 +471,15 @@ class MozillaStatusChangedEvent(_core.Co
         """SetBusy(self, bool isbusy)"""
         return _mozilla.MozillaStatusChangedEvent_SetBusy(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaStatusChangedEvent"""
-        newobj = _mozilla.new_MozillaStatusChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaStatusChangedEventPtr(MozillaStatusChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaStatusChangedEvent
-_mozilla.MozillaStatusChangedEvent_swigregister(MozillaStatusChangedEventPtr)
+        _mozilla.MozillaStatusChangedEvent_swiginit(self,_mozilla.new_MozillaStatusChangedEvent(*args, **kwargs))
+_mozilla.MozillaStatusChangedEvent_swigregister(MozillaStatusChangedEvent)
 
 class MozillaTitleChangedEvent(_core.CommandEvent):
     """Proxy of C++ MozillaTitleChangedEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaTitleChangedEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetTitle(*args, **kwargs):
         """GetTitle(self) -> String"""
         return _mozilla.MozillaTitleChangedEvent_GetTitle(*args, **kwargs)
@@ -559,24 +488,15 @@ class MozillaTitleChangedEvent(_core.Com
         """SetTitle(self, String title)"""
         return _mozilla.MozillaTitleChangedEvent_SetTitle(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaTitleChangedEvent"""
-        newobj = _mozilla.new_MozillaTitleChangedEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaTitleChangedEventPtr(MozillaTitleChangedEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaTitleChangedEvent
-_mozilla.MozillaTitleChangedEvent_swigregister(MozillaTitleChangedEventPtr)
+        _mozilla.MozillaTitleChangedEvent_swiginit(self,_mozilla.new_MozillaTitleChangedEvent(*args, **kwargs))
+_mozilla.MozillaTitleChangedEvent_swigregister(MozillaTitleChangedEvent)
 
 class MozillaProgressEvent(_core.CommandEvent):
     """Proxy of C++ MozillaProgressEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaProgressEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def GetSelfCurrentProgress(*args, **kwargs):
         """GetSelfCurrentProgress(self) -> int"""
         return _mozilla.MozillaProgressEvent_GetSelfCurrentProgress(*args, **kwargs)
@@ -609,24 +529,15 @@ class MozillaProgressEvent(_core.Command
         """SetTotalMaxProgress(self, int progress)"""
         return _mozilla.MozillaProgressEvent_SetTotalMaxProgress(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaProgressEvent"""
-        newobj = _mozilla.new_MozillaProgressEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaProgressEventPtr(MozillaProgressEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaProgressEvent
-_mozilla.MozillaProgressEvent_swigregister(MozillaProgressEventPtr)
+        _mozilla.MozillaProgressEvent_swiginit(self,_mozilla.new_MozillaProgressEvent(*args, **kwargs))
+_mozilla.MozillaProgressEvent_swigregister(MozillaProgressEvent)
 
 class MozillaRightClickEvent(_core.MouseEvent):
     """Proxy of C++ MozillaRightClickEvent class"""
-    def __repr__(self):
-        return "<%s.%s; proxy of C++ wxMozillaRightClickEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
+    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
+    __repr__ = _swig_repr
     def IsBusy(*args, **kwargs):
         """IsBusy(self) -> bool"""
         return _mozilla.MozillaRightClickEvent_IsBusy(*args, **kwargs)
@@ -675,19 +586,10 @@ class MozillaRightClickEvent(_core.Mouse
         """SetContext(self, int context)"""
         return _mozilla.MozillaRightClickEvent_SetContext(*args, **kwargs)
 
-    def __init__(self, *args, **kwargs):
+    def __init__(self, *args, **kwargs): 
         """__init__(self, Window win=None) -> MozillaRightClickEvent"""
-        newobj = _mozilla.new_MozillaRightClickEvent(*args, **kwargs)
-        self.this = newobj.this
-        self.thisown = 1
-        del newobj.thisown
-
-class MozillaRightClickEventPtr(MozillaRightClickEvent):
-    def __init__(self, this):
-        self.this = this
-        if not hasattr(self,"thisown"): self.thisown = 0
-        self.__class__ = MozillaRightClickEvent
-_mozilla.MozillaRightClickEvent_swigregister(MozillaRightClickEventPtr)
+        _mozilla.MozillaRightClickEvent_swiginit(self,_mozilla.new_MozillaRightClickEvent(*args, **kwargs))
+_mozilla.MozillaRightClickEvent_swigregister(MozillaRightClickEvent)
 
 wxEVT_MOZILLA_BEFORE_LOAD = _mozilla.wxEVT_MOZILLA_BEFORE_LOAD
 wxEVT_MOZILLA_URL_CHANGED = _mozilla.wxEVT_MOZILLA_URL_CHANGED
@@ -711,3 +613,4 @@ EVT_MOZILLA_PROGRESS = wx.PyEventBinder(
 EVT_MOZILLA_RIGHT_CLICK = wx.PyEventBinder(wxEVT_MOZILLA_RIGHT_CLICK, 1)
 
 
+
--- wxPython/contrib/mozilla25/gtk/mozilla_wrap.cpp.wxPython28	2007-06-22 11:05:40.000000000 +1000
+++ wxPython/contrib/mozilla25/gtk/mozilla_wrap.cpp	2007-07-20 12:17:50.000000000 +1000
@@ -1,6 +1,6 @@
 /* ----------------------------------------------------------------------------
  * This file was automatically generated by SWIG (http://www.swig.org).
- * Version 1.3.27
+ * Version 1.3.29
  * 
  * This file is not intended to be easily readable and contains a number of 
  * coding conventions designed to improve portability and efficiency. Do not make
@@ -9,6 +9,7 @@
  * ----------------------------------------------------------------------------- */
 
 #define SWIGPYTHON
+#define SWIG_PYTHON_DIRECTOR_NO_VTABLE
 
 #ifdef __cplusplus
 template<class T> class SwigValueWrapper {
@@ -26,20 +27,22 @@ private:
 };
 #endif
 
-/***********************************************************************
- *
+/* -----------------------------------------------------------------------------
  *  This section contains generic SWIG labels for method/variable
  *  declarations/attributes, and other compiler dependent labels.
- *
- ************************************************************************/
+ * ----------------------------------------------------------------------------- */
 
 /* template workaround for compilers that cannot correctly implement the C++ standard */
 #ifndef SWIGTEMPLATEDISAMBIGUATOR
-#  if defined(__SUNPRO_CC) && (__SUNPRO_CC <= 0x560)
-#    define SWIGTEMPLATEDISAMBIGUATOR template
-#  else
-#    define SWIGTEMPLATEDISAMBIGUATOR 
-#  endif
+# if defined(__SUNPRO_CC)
+#   if (__SUNPRO_CC <= 0x560)
+#     define SWIGTEMPLATEDISAMBIGUATOR template
+#   else
+#     define SWIGTEMPLATEDISAMBIGUATOR 
+#   endif
+# else
+#   define SWIGTEMPLATEDISAMBIGUATOR 
+# endif
 #endif
 
 /* inline attribute */
@@ -53,13 +56,27 @@ private:
 
 /* attribute recognised by some compilers to avoid 'unused' warnings */
 #ifndef SWIGUNUSED
-# if defined(__GNUC__) || defined(__ICC)
-#   define SWIGUNUSED __attribute__ ((unused)) 
+# if defined(__GNUC__)
+#   if !(defined(__cplusplus)) || (__GNUC__ > 3 || (__GNUC__ == 3 && __GNUC_MINOR__ >= 4))
+#     define SWIGUNUSED __attribute__ ((__unused__)) 
+#   else
+#     define SWIGUNUSED
+#   endif
+# elif defined(__ICC)
+#   define SWIGUNUSED __attribute__ ((__unused__)) 
 # else
 #   define SWIGUNUSED 
 # endif
 #endif
 
+#ifndef SWIGUNUSEDPARM
+# ifdef __cplusplus
+#   define SWIGUNUSEDPARM(p)
+# else
+#   define SWIGUNUSEDPARM(p) p SWIGUNUSED 
+# endif
+#endif
+
 /* internal SWIG method */
 #ifndef SWIGINTERN
 # define SWIGINTERN static SWIGUNUSED
@@ -70,7 +87,13 @@ private:
 # define SWIGINTERNINLINE SWIGINTERN SWIGINLINE
 #endif
 
-/* exporting methods for Windows DLLs */
+/* exporting methods */
+#if (__GNUC__ >= 4) || (__GNUC__ == 3 && __GNUC_MINOR__ >= 4)
+#  ifndef GCC_HASCLASSVISIBILITY
+#    define GCC_HASCLASSVISIBILITY
+#  endif
+#endif
+
 #ifndef SWIGEXPORT
 # if defined(_WIN32) || defined(__WIN32__) || defined(__CYGWIN__)
 #   if defined(STATIC_LINKED)
@@ -79,7 +102,11 @@ private:
 #     define SWIGEXPORT __declspec(dllexport)
 #   endif
 # else
-#   define SWIGEXPORT
+#   if defined(__GNUC__) && defined(GCC_HASCLASSVISIBILITY)
+#     define SWIGEXPORT __attribute__ ((visibility("default")))
+#   else
+#     define SWIGEXPORT
+#   endif
 # endif
 #endif
 
@@ -92,17 +119,21 @@ private:
 # endif 
 #endif
 
+/* Deal with Microsoft's attempt at deprecating C standard runtime functions */
+#if !defined(SWIG_NO_CRT_SECURE_NO_DEPRECATE) && defined(_MSC_VER)
+# define _CRT_SECURE_NO_DEPRECATE
+#endif
 
 
+/* Python.h has to appear first */
 #include <Python.h>
 
-/***********************************************************************
+/* -----------------------------------------------------------------------------
  * swigrun.swg
  *
- *     This file contains generic CAPI SWIG runtime support for pointer
- *     type checking.
- *
- ************************************************************************/
+ * This file contains generic CAPI SWIG runtime support for pointer
+ * type checking.
+ * ----------------------------------------------------------------------------- */
 
 /* This should only be incremented when either the layout of swig_type_info changes,
    or for whatever reason, the runtime changes incompatibly */
@@ -134,6 +165,147 @@ private:
 # define SWIGRUNTIMEINLINE SWIGRUNTIME SWIGINLINE
 #endif
 
+/*  Generic buffer size */
+#ifndef SWIG_BUFFER_SIZE
+# define SWIG_BUFFER_SIZE 1024
+#endif
+
+/* Flags for pointer conversions */
+#define SWIG_POINTER_DISOWN        0x1
+
+/* Flags for new pointer objects */
+#define SWIG_POINTER_OWN           0x1
+
+
+/* 
+   Flags/methods for returning states.
+   
+   The swig conversion methods, as ConvertPtr, return and integer 
+   that tells if the conversion was successful or not. And if not,
+   an error code can be returned (see swigerrors.swg for the codes).
+   
+   Use the following macros/flags to set or process the returning
+   states.
+   
+   In old swig versions, you usually write code as:
+
+     if (SWIG_ConvertPtr(obj,vptr,ty.flags) != -1) {
+       // success code
+     } else {
+       //fail code
+     }
+
+   Now you can be more explicit as:
+
+    int res = SWIG_ConvertPtr(obj,vptr,ty.flags);
+    if (SWIG_IsOK(res)) {
+      // success code
+    } else {
+      // fail code
+    }
+
+   that seems to be the same, but now you can also do
+
+    Type *ptr;
+    int res = SWIG_ConvertPtr(obj,(void **)(&ptr),ty.flags);
+    if (SWIG_IsOK(res)) {
+      // success code
+      if (SWIG_IsNewObj(res) {
+        ...
+	delete *ptr;
+      } else {
+        ...
+      }
+    } else {
+      // fail code
+    }
+    
+   I.e., now SWIG_ConvertPtr can return new objects and you can
+   identify the case and take care of the deallocation. Of course that
+   requires also to SWIG_ConvertPtr to return new result values, as
+
+      int SWIG_ConvertPtr(obj, ptr,...) {         
+        if (<obj is ok>) {			       
+          if (<need new object>) {		       
+            *ptr = <ptr to new allocated object>; 
+            return SWIG_NEWOBJ;		       
+          } else {				       
+            *ptr = <ptr to old object>;	       
+            return SWIG_OLDOBJ;		       
+          } 				       
+        } else {				       
+          return SWIG_BADOBJ;		       
+        }					       
+      }
+
+   Of course, returning the plain '0(success)/-1(fail)' still works, but you can be
+   more explicit by returning SWIG_BADOBJ, SWIG_ERROR or any of the
+   swig errors code.
+
+   Finally, if the SWIG_CASTRANK_MODE is enabled, the result code
+   allows to return the 'cast rank', for example, if you have this
+
+       int food(double)
+       int fooi(int);
+
+   and you call
+ 
+      food(1)   // cast rank '1'  (1 -> 1.0)
+      fooi(1)   // cast rank '0'
+
+   just use the SWIG_AddCast()/SWIG_CheckState()
+
+
+ */
+#define SWIG_OK                    (0) 
+#define SWIG_ERROR                 (-1)
+#define SWIG_IsOK(r)               (r >= 0)
+#define SWIG_ArgError(r)           ((r != SWIG_ERROR) ? r : SWIG_TypeError)  
+
+/* The CastRankLimit says how many bits are used for the cast rank */
+#define SWIG_CASTRANKLIMIT         (1 << 8)
+/* The NewMask denotes the object was created (using new/malloc) */
+#define SWIG_NEWOBJMASK            (SWIG_CASTRANKLIMIT  << 1)
+/* The TmpMask is for in/out typemaps that use temporal objects */
+#define SWIG_TMPOBJMASK            (SWIG_NEWOBJMASK << 1)
+/* Simple returning values */
+#define SWIG_BADOBJ                (SWIG_ERROR)
+#define SWIG_OLDOBJ                (SWIG_OK)
+#define SWIG_NEWOBJ                (SWIG_OK | SWIG_NEWOBJMASK)
+#define SWIG_TMPOBJ                (SWIG_OK | SWIG_TMPOBJMASK)
+/* Check, add and del mask methods */
+#define SWIG_AddNewMask(r)         (SWIG_IsOK(r) ? (r | SWIG_NEWOBJMASK) : r)
+#define SWIG_DelNewMask(r)         (SWIG_IsOK(r) ? (r & ~SWIG_NEWOBJMASK) : r)
+#define SWIG_IsNewObj(r)           (SWIG_IsOK(r) && (r & SWIG_NEWOBJMASK))
+#define SWIG_AddTmpMask(r)         (SWIG_IsOK(r) ? (r | SWIG_TMPOBJMASK) : r)
+#define SWIG_DelTmpMask(r)         (SWIG_IsOK(r) ? (r & ~SWIG_TMPOBJMASK) : r)
+#define SWIG_IsTmpObj(r)           (SWIG_IsOK(r) && (r & SWIG_TMPOBJMASK))
+
+
+/* Cast-Rank Mode */
+#if defined(SWIG_CASTRANK_MODE)
+#  ifndef SWIG_TypeRank
+#    define SWIG_TypeRank             unsigned long
+#  endif
+#  ifndef SWIG_MAXCASTRANK            /* Default cast allowed */
+#    define SWIG_MAXCASTRANK          (2)
+#  endif
+#  define SWIG_CASTRANKMASK          ((SWIG_CASTRANKLIMIT) -1)
+#  define SWIG_CastRank(r)           (r & SWIG_CASTRANKMASK)
+SWIGINTERNINLINE int SWIG_AddCast(int r) { 
+  return SWIG_IsOK(r) ? ((SWIG_CastRank(r) < SWIG_MAXCASTRANK) ? (r + 1) : SWIG_ERROR) : r;
+}
+SWIGINTERNINLINE int SWIG_CheckState(int r) { 
+  return SWIG_IsOK(r) ? SWIG_CastRank(r) + 1 : 0; 
+}
+#else /* no cast-rank mode */
+#  define SWIG_AddCast
+#  define SWIG_CheckState(r) (SWIG_IsOK(r) ? 1 : 0)
+#endif
+
+
+
+
 #include <string.h>
 
 #ifdef __cplusplus
@@ -150,6 +322,7 @@ typedef struct swig_type_info {
   swig_dycast_func        dcast;		/* dynamic cast function down a hierarchy */
   struct swig_cast_info  *cast;			/* linked list of types that can cast into this type */
   void                   *clientdata;		/* language specific type data */
+  int                    owndata;		/* flag if the structure owns the clientdata */
 } swig_type_info;
 
 /* Structure to store a type and conversion function used for casting */
@@ -172,7 +345,6 @@ typedef struct swig_module_info {
   void                    *clientdata;		/* Language specific module data */
 } swig_module_info;
 
-
 /* 
   Compare two type names skipping the space characters, therefore
   "char*" == "char *" and "Class<int>" == "Class<int >", etc.
@@ -186,7 +358,7 @@ SWIG_TypeNameComp(const char *f1, const 
   for (;(f1 != l1) && (f2 != l2); ++f1, ++f2) {
     while ((*f1 == ' ') && (f1 != l1)) ++f1;
     while ((*f2 == ' ') && (f2 != l2)) ++f2;
-    if (*f1 != *f2) return (int)(*f1 - *f2);
+    if (*f1 != *f2) return (*f1 > *f2) ? 1 : -1;
   }
   return (l1 - f1) - (l2 - f2);
 }
@@ -306,6 +478,7 @@ SWIG_TypePrettyName(const swig_type_info
      type, separated by vertical-bar characters.  We choose
      to print the last name, as it is often (?) the most
      specific. */
+  if (!type) return NULL;
   if (type->str != NULL) {
     const char *last_name = type->str;
     const char *s;
@@ -336,7 +509,12 @@ SWIG_TypeClientData(swig_type_info *ti, 
     cast = cast->next;
   }
 }
-
+SWIGRUNTIME void
+SWIG_TypeNewClientData(swig_type_info *ti, void *clientdata) {
+  SWIG_TypeClientData(ti, clientdata);
+  ti->owndata = 1;
+}
+  
 /*
   Search for a swig_type_info structure only by mangled name
   Search is a O(log #types)
@@ -416,7 +594,6 @@ SWIG_TypeQueryModule(swig_module_info *s
   return 0;
 }
 
-
 /* 
    Pack binary data into a string
 */
@@ -442,7 +619,7 @@ SWIG_UnpackData(const char *c, void *ptr
   register const unsigned char *eu = u + sz;
   for (; u != eu; ++u) {
     register char d = *(c++);
-    register unsigned char uu = 0;
+    register unsigned char uu;
     if ((d >= '0') && (d <= '9'))
       uu = ((d - '0') << 4);
     else if ((d >= 'a') && (d <= 'f'))
@@ -520,251 +697,890 @@ SWIG_UnpackDataName(const char *c, void 
 }
 #endif
 
-/* -----------------------------------------------------------------------------
- * SWIG API. Portion that goes into the runtime
- * ----------------------------------------------------------------------------- */
+/*  Errors in SWIG */
+#define  SWIG_UnknownError    	   -1 
+#define  SWIG_IOError        	   -2 
+#define  SWIG_RuntimeError   	   -3 
+#define  SWIG_IndexError     	   -4 
+#define  SWIG_TypeError      	   -5 
+#define  SWIG_DivisionByZero 	   -6 
+#define  SWIG_OverflowError  	   -7 
+#define  SWIG_SyntaxError    	   -8 
+#define  SWIG_ValueError     	   -9 
+#define  SWIG_SystemError    	   -10
+#define  SWIG_AttributeError 	   -11
+#define  SWIG_MemoryError    	   -12 
+#define  SWIG_NullReferenceError   -13
 
-#ifdef __cplusplus
-extern "C" {
+
+
+/* Python.h has to appear first */
+#include <Python.h>
+
+/* Add PyOS_snprintf for old Pythons */
+#if PY_VERSION_HEX < 0x02020000
+# if defined(_MSC_VER) || defined(__BORLANDC__) || defined(_WATCOM)
+#  define PyOS_snprintf _snprintf
+# else
+#  define PyOS_snprintf snprintf
+# endif
+#endif
+
+/* A crude PyString_FromFormat implementation for old Pythons */
+#if PY_VERSION_HEX < 0x02020000
+
+#ifndef SWIG_PYBUFFER_SIZE
+# define SWIG_PYBUFFER_SIZE 1024
+#endif
+
+static PyObject *
+PyString_FromFormat(const char *fmt, ...) {
+  va_list ap;
+  char buf[SWIG_PYBUFFER_SIZE * 2];
+  int res;
+  va_start(ap, fmt);
+  res = vsnprintf(buf, sizeof(buf), fmt, ap);
+  va_end(ap);
+  return (res < 0 || res >= (int)sizeof(buf)) ? 0 : PyString_FromString(buf);
+}
+#endif
+
+/* Add PyObject_Del for old Pythons */
+#if PY_VERSION_HEX < 0x01060000
+# define PyObject_Del(op) PyMem_DEL((op))
+#endif
+#ifndef PyObject_DEL
+# define PyObject_DEL PyObject_Del
+#endif
+
+/* A crude PyExc_StopIteration exception for old Pythons */
+#if PY_VERSION_HEX < 0x02020000
+# ifndef PyExc_StopIteration
+#  define PyExc_StopIteration PyExc_RuntimeError
+# endif
+# ifndef PyObject_GenericGetAttr
+#  define PyObject_GenericGetAttr 0
+# endif
+#endif
+/* Py_NotImplemented is defined in 2.1 and up. */
+#if PY_VERSION_HEX < 0x02010000
+# ifndef Py_NotImplemented
+#  define Py_NotImplemented PyExc_RuntimeError
+# endif
+#endif
+
+
+/* A crude PyString_AsStringAndSize implementation for old Pythons */
+#if PY_VERSION_HEX < 0x02010000
+# ifndef PyString_AsStringAndSize
+#  define PyString_AsStringAndSize(obj, s, len) {*s = PyString_AsString(obj); *len = *s ? strlen(*s) : 0;}
+# endif
+#endif
+
+/* PySequence_Size for old Pythons */
+#if PY_VERSION_HEX < 0x02000000
+# ifndef PySequence_Size
+#  define PySequence_Size PySequence_Length
+# endif
+#endif
+
+
+/* PyBool_FromLong for old Pythons */
+#if PY_VERSION_HEX < 0x02030000
+static
+PyObject *PyBool_FromLong(long ok)
+{
+  PyObject *result = ok ? Py_True : Py_False;
+  Py_INCREF(result);
+  return result;
+}
 #endif
 
+
 /* -----------------------------------------------------------------------------
- * for internal method declarations
+ * error manipulation
  * ----------------------------------------------------------------------------- */
 
-#ifndef SWIGINTERN
-#  define SWIGINTERN static SWIGUNUSED
-#endif
+SWIGRUNTIME PyObject*
+SWIG_Python_ErrorType(int code) {
+  PyObject* type = 0;
+  switch(code) {
+  case SWIG_MemoryError:
+    type = PyExc_MemoryError;
+    break;
+  case SWIG_IOError:
+    type = PyExc_IOError;
+    break;
+  case SWIG_RuntimeError:
+    type = PyExc_RuntimeError;
+    break;
+  case SWIG_IndexError:
+    type = PyExc_IndexError;
+    break;
+  case SWIG_TypeError:
+    type = PyExc_TypeError;
+    break;
+  case SWIG_DivisionByZero:
+    type = PyExc_ZeroDivisionError;
+    break;
+  case SWIG_OverflowError:
+    type = PyExc_OverflowError;
+    break;
+  case SWIG_SyntaxError:
+    type = PyExc_SyntaxError;
+    break;
+  case SWIG_ValueError:
+    type = PyExc_ValueError;
+    break;
+  case SWIG_SystemError:
+    type = PyExc_SystemError;
+    break;
+  case SWIG_AttributeError:
+    type = PyExc_AttributeError;
+    break;
+  default:
+    type = PyExc_RuntimeError;
+  }
+  return type;
+}
 
-#ifndef SWIGINTERNINLINE
-#  define SWIGINTERNINLINE SWIGINTERN SWIGINLINE
+
+SWIGRUNTIME void
+SWIG_Python_AddErrorMsg(const char* mesg)
+{
+  PyObject *type = 0;
+  PyObject *value = 0;
+  PyObject *traceback = 0;
+
+  if (PyErr_Occurred()) PyErr_Fetch(&type, &value, &traceback);
+  if (value) {
+    PyObject *old_str = PyObject_Str(value);
+    PyErr_Clear();
+    Py_XINCREF(type);
+    PyErr_Format(type, "%s %s", PyString_AsString(old_str), mesg);
+    Py_DECREF(old_str);
+    Py_DECREF(value);
+  } else {
+    PyErr_Format(PyExc_RuntimeError, mesg);
+  }
+}
+
+
+
+#if defined(SWIG_PYTHON_NO_THREADS)
+#  if defined(SWIG_PYTHON_THREADS)
+#    undef SWIG_PYTHON_THREADS
+#  endif
+#endif
+#if defined(SWIG_PYTHON_THREADS) /* Threading support is enabled */
+#  if !defined(SWIG_PYTHON_USE_GIL) && !defined(SWIG_PYTHON_NO_USE_GIL)
+#    if (PY_VERSION_HEX >= 0x02030000) /* For 2.3 or later, use the PyGILState calls */
+#      define SWIG_PYTHON_USE_GIL
+#    endif
+#  endif
+#  if defined(SWIG_PYTHON_USE_GIL) /* Use PyGILState threads calls */
+#    ifndef SWIG_PYTHON_INITIALIZE_THREADS
+#     define SWIG_PYTHON_INITIALIZE_THREADS  PyEval_InitThreads() 
+#    endif
+#    ifdef __cplusplus /* C++ code */
+       class SWIG_Python_Thread_Block {
+         bool status;
+         PyGILState_STATE state;
+       public:
+         void end() { if (status) { PyGILState_Release(state); status = false;} }
+         SWIG_Python_Thread_Block() : status(true), state(PyGILState_Ensure()) {}
+         ~SWIG_Python_Thread_Block() { end(); }
+       };
+       class SWIG_Python_Thread_Allow {
+         bool status;
+         PyThreadState *save;
+       public:
+         void end() { if (status) { PyEval_RestoreThread(save); status = false; }}
+         SWIG_Python_Thread_Allow() : status(true), save(PyEval_SaveThread()) {}
+         ~SWIG_Python_Thread_Allow() { end(); }
+       };
+#      define SWIG_PYTHON_THREAD_BEGIN_BLOCK   SWIG_Python_Thread_Block _swig_thread_block
+#      define SWIG_PYTHON_THREAD_END_BLOCK     _swig_thread_block.end()
+#      define SWIG_PYTHON_THREAD_BEGIN_ALLOW   SWIG_Python_Thread_Allow _swig_thread_allow
+#      define SWIG_PYTHON_THREAD_END_ALLOW     _swig_thread_allow.end()
+#    else /* C code */
+#      define SWIG_PYTHON_THREAD_BEGIN_BLOCK   PyGILState_STATE _swig_thread_block = PyGILState_Ensure()
+#      define SWIG_PYTHON_THREAD_END_BLOCK     PyGILState_Release(_swig_thread_block)
+#      define SWIG_PYTHON_THREAD_BEGIN_ALLOW   PyThreadState *_swig_thread_allow = PyEval_SaveThread()
+#      define SWIG_PYTHON_THREAD_END_ALLOW     PyEval_RestoreThread(_swig_thread_allow)
+#    endif
+#  else /* Old thread way, not implemented, user must provide it */
+#    if !defined(SWIG_PYTHON_INITIALIZE_THREADS)
+#      define SWIG_PYTHON_INITIALIZE_THREADS
+#    endif
+#    if !defined(SWIG_PYTHON_THREAD_BEGIN_BLOCK)
+#      define SWIG_PYTHON_THREAD_BEGIN_BLOCK
+#    endif
+#    if !defined(SWIG_PYTHON_THREAD_END_BLOCK)
+#      define SWIG_PYTHON_THREAD_END_BLOCK
+#    endif
+#    if !defined(SWIG_PYTHON_THREAD_BEGIN_ALLOW)
+#      define SWIG_PYTHON_THREAD_BEGIN_ALLOW
+#    endif
+#    if !defined(SWIG_PYTHON_THREAD_END_ALLOW)
+#      define SWIG_PYTHON_THREAD_END_ALLOW
+#    endif
+#  endif
+#else /* No thread support */
+#  define SWIG_PYTHON_INITIALIZE_THREADS
+#  define SWIG_PYTHON_THREAD_BEGIN_BLOCK
+#  define SWIG_PYTHON_THREAD_END_BLOCK
+#  define SWIG_PYTHON_THREAD_BEGIN_ALLOW
+#  define SWIG_PYTHON_THREAD_END_ALLOW
 #endif
 
-/*
-  Exception handling in wrappers
-*/
-#define SWIG_fail                goto fail
-#define SWIG_arg_fail(arg)       SWIG_Python_ArgFail(arg)
-#define SWIG_append_errmsg(msg)   SWIG_Python_AddErrMesg(msg,0)
-#define SWIG_preppend_errmsg(msg) SWIG_Python_AddErrMesg(msg,1)
-#define SWIG_type_error(type,obj) SWIG_Python_TypeError(type,obj)
-#define SWIG_null_ref(type)       SWIG_Python_NullRef(type)
+/* -----------------------------------------------------------------------------
+ * Python API portion that goes into the runtime
+ * ----------------------------------------------------------------------------- */
 
-/*
-  Contract support
-*/
-#define SWIG_contract_assert(expr, msg) \
- if (!(expr)) { PyErr_SetString(PyExc_RuntimeError, (char *) msg ); goto fail; } else
+#ifdef __cplusplus
+extern "C" {
+#if 0
+} /* cc-mode */
+#endif
+#endif
 
 /* -----------------------------------------------------------------------------
  * Constant declarations
  * ----------------------------------------------------------------------------- */
 
 /* Constant Types */
-#define SWIG_PY_INT     1
-#define SWIG_PY_FLOAT   2
-#define SWIG_PY_STRING  3
 #define SWIG_PY_POINTER 4
 #define SWIG_PY_BINARY  5
 
 /* Constant information structure */
 typedef struct swig_const_info {
-    int type;
-    char *name;
-    long lvalue;
-    double dvalue;
-    void   *pvalue;
-    swig_type_info **ptype;
+  int type;
+  char *name;
+  long lvalue;
+  double dvalue;
+  void   *pvalue;
+  swig_type_info **ptype;
 } swig_const_info;
 
-
-/* -----------------------------------------------------------------------------
- * Alloc. memory flags
- * ----------------------------------------------------------------------------- */
-#define SWIG_OLDOBJ  1
-#define SWIG_NEWOBJ  SWIG_OLDOBJ + 1
-#define SWIG_PYSTR   SWIG_NEWOBJ + 1
-
 #ifdef __cplusplus
+#if 0
+{ /* cc-mode */
+#endif
 }
 #endif
 
 
-/***********************************************************************
+/* -----------------------------------------------------------------------------
+ * See the LICENSE file for information on copyright, usage and redistribution
+ * of SWIG, and the README file for authors - http://www.swig.org/release.html.
+ *
  * pyrun.swg
  *
- *     This file contains the runtime support for Python modules
- *     and includes code for managing global variables and pointer
- *     type checking.
+ * This file contains the runtime support for Python modules
+ * and includes code for managing global variables and pointer
+ * type checking.
  *
- * Author : David Beazley (beazley@cs.uchicago.edu)
- ************************************************************************/
+ * ----------------------------------------------------------------------------- */
 
 /* Common SWIG API */
-#define SWIG_ConvertPtr(obj, pp, type, flags)    SWIG_Python_ConvertPtr(obj, pp, type, flags)
-#define SWIG_NewPointerObj(p, type, flags)       SWIG_Python_NewPointerObj(p, type, flags)
-#define SWIG_MustGetPtr(p, type, argnum, flags)  SWIG_Python_MustGetPtr(p, type, argnum, flags)
- 
 
-/* Python-specific SWIG API */
-#define SWIG_ConvertPacked(obj, ptr, sz, ty, flags)   SWIG_Python_ConvertPacked(obj, ptr, sz, ty, flags)
-#define SWIG_NewPackedObj(ptr, sz, type)              SWIG_Python_NewPackedObj(ptr, sz, type)
+#if PY_VERSION_HEX < 0x02050000
+typedef int Py_ssize_t;
+#endif
+
+/* for raw pointers */
+#define SWIG_Python_ConvertPtr(obj, pptr, type, flags)  SWIG_Python_ConvertPtrAndOwn(obj, pptr, type, flags, 0)
+#define SWIG_ConvertPtr(obj, pptr, type, flags)         SWIG_Python_ConvertPtr(obj, pptr, type, flags)
+#define SWIG_ConvertPtrAndOwn(obj,pptr,type,flags,own)  SWIG_Python_ConvertPtrAndOwn(obj, pptr, type, flags, own)
+#define SWIG_NewPointerObj(ptr, type, flags)            SWIG_Python_NewPointerObj(ptr, type, flags)
+#define SWIG_CheckImplicit(ty)                          SWIG_Python_CheckImplicit(ty) 
+#define SWIG_AcquirePtr(ptr, src)                       SWIG_Python_AcquirePtr(ptr, src)
+#define swig_owntype                                    int
+
+/* for raw packed data */
+#define SWIG_ConvertPacked(obj, ptr, sz, ty)            SWIG_Python_ConvertPacked(obj, ptr, sz, ty)
+#define SWIG_NewPackedObj(ptr, sz, type)                SWIG_Python_NewPackedObj(ptr, sz, type)
+
+/* for class or struct pointers */
+#define SWIG_ConvertInstance(obj, pptr, type, flags)    SWIG_ConvertPtr(obj, pptr, type, flags)
+#define SWIG_NewInstanceObj(ptr, type, flags)           SWIG_NewPointerObj(ptr, type, flags)
+
+/* for C or C++ function pointers */
+#define SWIG_ConvertFunctionPtr(obj, pptr, type)        SWIG_Python_ConvertFunctionPtr(obj, pptr, type)
+#define SWIG_NewFunctionPtrObj(ptr, type)               SWIG_Python_NewPointerObj(ptr, type, 0)
+
+/* for C++ member pointers, ie, member methods */
+#define SWIG_ConvertMember(obj, ptr, sz, ty)            SWIG_Python_ConvertPacked(obj, ptr, sz, ty)
+#define SWIG_NewMemberObj(ptr, sz, type)                SWIG_Python_NewPackedObj(ptr, sz, type)
+
 
 /* Runtime API */
-#define SWIG_GetModule(clientdata) SWIG_Python_GetModule()
-#define SWIG_SetModule(clientdata, pointer) SWIG_Python_SetModule(pointer)
 
-/* -----------------------------------------------------------------------------
- * Pointer declarations
- * ----------------------------------------------------------------------------- */
-/*
-  Use SWIG_NO_COBJECT_TYPES to force the use of strings to represent
-  C/C++ pointers in the python side. Very useful for debugging, but
-  not always safe.
-*/
-#if !defined(SWIG_NO_COBJECT_TYPES) && !defined(SWIG_COBJECT_TYPES)
-#  define SWIG_COBJECT_TYPES
-#endif
+#define SWIG_GetModule(clientdata)                      SWIG_Python_GetModule()
+#define SWIG_SetModule(clientdata, pointer)             SWIG_Python_SetModule(pointer)
+#define SWIG_NewClientData(obj)                         PySwigClientData_New(obj)
 
-/* Flags for pointer conversion */
-#define SWIG_POINTER_EXCEPTION     0x1
-#define SWIG_POINTER_DISOWN        0x2
+#define SWIG_SetErrorObj                                SWIG_Python_SetErrorObj                            
+#define SWIG_SetErrorMsg                        	SWIG_Python_SetErrorMsg				   
+#define SWIG_ErrorType(code)                    	SWIG_Python_ErrorType(code)                        
+#define SWIG_Error(code, msg)            		SWIG_Python_SetErrorMsg(SWIG_ErrorType(code), msg) 
+#define SWIG_fail                        		goto fail					   
 
 
-/* Add PyOS_snprintf for old Pythons */
-#if PY_VERSION_HEX < 0x02020000
-#define PyOS_snprintf snprintf
-#endif
+/* Runtime API implementation */
 
-#ifdef __cplusplus
-extern "C" {
-#endif
+/* Error manipulation */
 
-/* -----------------------------------------------------------------------------
- * Create a new pointer string 
- * ----------------------------------------------------------------------------- */
-#ifndef SWIG_BUFFER_SIZE
-#define SWIG_BUFFER_SIZE 1024
-#endif
+SWIGINTERN void 
+SWIG_Python_SetErrorObj(PyObject *errtype, PyObject *obj) {
+  SWIG_PYTHON_THREAD_BEGIN_BLOCK; 
+  PyErr_SetObject(errtype, obj);
+  Py_DECREF(obj);
+  SWIG_PYTHON_THREAD_END_BLOCK;
+}
 
-/* A crude PyString_FromFormat implementation for old Pythons */
-#if PY_VERSION_HEX < 0x02020000
-static PyObject *
-PyString_FromFormat(const char *fmt, ...) {
-  va_list ap;
-  char buf[SWIG_BUFFER_SIZE * 2];
-  int res;
-  va_start(ap, fmt);
-  res = vsnprintf(buf, sizeof(buf), fmt, ap);
-  va_end(ap);
-  return (res < 0 || res >= sizeof(buf)) ? 0 : PyString_FromString(buf);
+SWIGINTERN void 
+SWIG_Python_SetErrorMsg(PyObject *errtype, const char *msg) {
+  SWIG_PYTHON_THREAD_BEGIN_BLOCK;
+  PyErr_SetString(errtype, (char *) msg);
+  SWIG_PYTHON_THREAD_END_BLOCK;
 }
-#endif
 
-#if PY_VERSION_HEX < 0x01060000
-#define PyObject_Del(op) PyMem_DEL((op))
-#endif
+#define SWIG_Python_Raise(obj, type, desc)  SWIG_Python_SetErrorObj(SWIG_Python_ExceptionType(desc), obj)
 
-#if defined(SWIG_COBJECT_TYPES)
-#if !defined(SWIG_COBJECT_PYTHON)
-/* -----------------------------------------------------------------------------
- * Implements a simple Swig Object type, and use it instead of PyCObject
- * ----------------------------------------------------------------------------- */
+/* Set a constant value */
 
-typedef struct {
-  PyObject_HEAD
-  void *ptr;
-  const char *desc;
-} PySwigObject;
+SWIGINTERN void
+SWIG_Python_SetConstant(PyObject *d, const char *name, PyObject *obj) {   
+  PyDict_SetItemString(d, (char*) name, obj);
+  Py_DECREF(obj);                            
+}
 
-/* Declarations for objects of type PySwigObject */
+/* Append a value to the result obj */
 
-SWIGRUNTIME int
-PySwigObject_print(PySwigObject *v, FILE *fp, int flags)
-{
-  char result[SWIG_BUFFER_SIZE];
-  flags = flags;
-  if (SWIG_PackVoidPtr(result, v->ptr, v->desc, sizeof(result))) {
-    fputs("<Swig Object at ", fp); fputs(result, fp); fputs(">", fp);
-    return 0; 
+SWIGINTERN PyObject*
+SWIG_Python_AppendOutput(PyObject* result, PyObject* obj) {
+#if !defined(SWIG_PYTHON_OUTPUT_TUPLE)
+  if (!result) {
+    result = obj;
+  } else if (result == Py_None) {
+    Py_DECREF(result);
+    result = obj;
   } else {
-    return 1; 
+    if (!PyList_Check(result)) {
+      PyObject *o2 = result;
+      result = PyList_New(1);
+      PyList_SetItem(result, 0, o2);
+    }
+    PyList_Append(result,obj);
+    Py_DECREF(obj);
   }
-}
-  
-SWIGRUNTIME PyObject *
-PySwigObject_repr(PySwigObject *v)
-{
-  char result[SWIG_BUFFER_SIZE];
-  return SWIG_PackVoidPtr(result, v->ptr, v->desc, sizeof(result)) ?
-    PyString_FromFormat("<Swig Object at %s>", result) : 0;
-}
-
-SWIGRUNTIME PyObject *
-PySwigObject_str(PySwigObject *v)
-{
-  char result[SWIG_BUFFER_SIZE];
-  return SWIG_PackVoidPtr(result, v->ptr, v->desc, sizeof(result)) ?
-    PyString_FromString(result) : 0;
+  return result;
+#else
+  PyObject*   o2;
+  PyObject*   o3;
+  if (!result) {
+    result = obj;
+  } else if (result == Py_None) {
+    Py_DECREF(result);
+    result = obj;
+  } else {
+    if (!PyTuple_Check(result)) {
+      o2 = result;
+      result = PyTuple_New(1);
+      PyTuple_SET_ITEM(result, 0, o2);
+    }
+    o3 = PyTuple_New(1);
+    PyTuple_SET_ITEM(o3, 0, obj);
+    o2 = result;
+    result = PySequence_Concat(o2, o3);
+    Py_DECREF(o2);
+    Py_DECREF(o3);
+  }
+  return result;
+#endif
 }
 
-SWIGRUNTIME PyObject *
-PySwigObject_long(PySwigObject *v)
-{
-  return PyLong_FromVoidPtr(v->ptr);
-}
+/* Unpack the argument tuple */
 
-SWIGRUNTIME PyObject *
-PySwigObject_format(const char* fmt, PySwigObject *v)
+SWIGINTERN int
+SWIG_Python_UnpackTuple(PyObject *args, const char *name, int min, int max, PyObject **objs)
 {
-  PyObject *res = NULL;
-  PyObject *args = PyTuple_New(1);
-  if (args && (PyTuple_SetItem(args, 0, PySwigObject_long(v)) == 0)) {
-    PyObject *ofmt = PyString_FromString(fmt);
-    if (ofmt) {
-      res = PyString_Format(ofmt,args);
-      Py_DECREF(ofmt);
+  if (!args) {
+    if (!min && !max) {
+      return 1;
+    } else {
+      PyErr_Format(PyExc_TypeError, "%s expected %s%d arguments, got none", 
+		   name, (min == max ? "" : "at least "), min);
+      return 0;
     }
-    Py_DECREF(args);
   }  
-  return res;
+  if (!PyTuple_Check(args)) {
+    PyErr_SetString(PyExc_SystemError, "UnpackTuple() argument list is not a tuple");
+    return 0;
+  } else {
+    register int l = PyTuple_GET_SIZE(args);
+    if (l < min) {
+      PyErr_Format(PyExc_TypeError, "%s expected %s%d arguments, got %d", 
+		   name, (min == max ? "" : "at least "), min, l);
+      return 0;
+    } else if (l > max) {
+      PyErr_Format(PyExc_TypeError, "%s expected %s%d arguments, got %d", 
+		   name, (min == max ? "" : "at most "), max, l);
+      return 0;
+    } else {
+      register int i;
+      for (i = 0; i < l; ++i) {
+	objs[i] = PyTuple_GET_ITEM(args, i);
+      }
+      for (; l < max; ++l) {
+	objs[l] = 0;
+      }
+      return i + 1;
+    }    
+  }
 }
 
-SWIGRUNTIME PyObject *
-PySwigObject_oct(PySwigObject *v)
-{
-  return PySwigObject_format("%o",v);
-}
+/* A functor is a function object with one single object argument */
+#if PY_VERSION_HEX >= 0x02020000
+#define SWIG_Python_CallFunctor(functor, obj)	        PyObject_CallFunctionObjArgs(functor, obj, NULL);
+#else
+#define SWIG_Python_CallFunctor(functor, obj)	        PyObject_CallFunction(functor, "O", obj);
+#endif
 
-SWIGRUNTIME PyObject *
-PySwigObject_hex(PySwigObject *v)
-{
-  return PySwigObject_format("%x",v);
+/*
+  Helper for static pointer initialization for both C and C++ code, for example
+  static PyObject *SWIG_STATIC_POINTER(MyVar) = NewSomething(...);
+*/
+#ifdef __cplusplus
+#define SWIG_STATIC_POINTER(var)  var
+#else
+#define SWIG_STATIC_POINTER(var)  var = 0; if (!var) var
+#endif
+
+/* -----------------------------------------------------------------------------
+ * Pointer declarations
+ * ----------------------------------------------------------------------------- */
+
+/* Flags for new pointer objects */
+#define SWIG_POINTER_NOSHADOW       (SWIG_POINTER_OWN      << 1)
+#define SWIG_POINTER_NEW            (SWIG_POINTER_NOSHADOW | SWIG_POINTER_OWN)
+
+#define SWIG_POINTER_IMPLICIT_CONV  (SWIG_POINTER_DISOWN   << 1)
+
+#ifdef __cplusplus
+extern "C" {
+#if 0
+} /* cc-mode */
+#endif
+#endif
+
+/*  How to access Py_None */
+#if defined(_WIN32) || defined(__WIN32__) || defined(__CYGWIN__)
+#  ifndef SWIG_PYTHON_NO_BUILD_NONE
+#    ifndef SWIG_PYTHON_BUILD_NONE
+#      define SWIG_PYTHON_BUILD_NONE
+#    endif
+#  endif
+#endif
+
+#ifdef SWIG_PYTHON_BUILD_NONE
+#  ifdef Py_None
+#   undef Py_None
+#   define Py_None SWIG_Py_None()
+#  endif
+SWIGRUNTIMEINLINE PyObject * 
+_SWIG_Py_None(void)
+{
+  PyObject *none = Py_BuildValue("");
+  Py_DECREF(none);
+  return none;
+}
+SWIGRUNTIME PyObject * 
+SWIG_Py_None(void)
+{
+  static PyObject *SWIG_STATIC_POINTER(none) = _SWIG_Py_None();
+  return none;
+}
+#endif
+
+/* The python void return value */
+
+SWIGRUNTIMEINLINE PyObject * 
+SWIG_Py_Void(void)
+{
+  PyObject *none = Py_None;
+  Py_INCREF(none);
+  return none;
+}
+
+/* PySwigClientData */
+
+typedef struct {
+  PyObject *klass;
+  PyObject *newraw;
+  PyObject *newargs;
+  PyObject *destroy;
+  int delargs;
+  int implicitconv;
+} PySwigClientData;
+
+SWIGRUNTIMEINLINE int 
+SWIG_Python_CheckImplicit(swig_type_info *ty)
+{
+  PySwigClientData *data = (PySwigClientData *)ty->clientdata;
+  return data ? data->implicitconv : 0;
+}
+
+SWIGRUNTIMEINLINE PyObject *
+SWIG_Python_ExceptionType(swig_type_info *desc) {
+  PySwigClientData *data = desc ? (PySwigClientData *) desc->clientdata : 0;
+  PyObject *klass = data ? data->klass : 0;
+  return (klass ? klass : PyExc_RuntimeError);
+}
+
+
+SWIGRUNTIME PySwigClientData * 
+PySwigClientData_New(PyObject* obj)
+{
+  if (!obj) {
+    return 0;
+  } else {
+    PySwigClientData *data = (PySwigClientData *)malloc(sizeof(PySwigClientData));
+    /* the klass element */
+    data->klass = obj;
+    Py_INCREF(data->klass);
+    /* the newraw method and newargs arguments used to create a new raw instance */
+    if (PyClass_Check(obj)) {
+      data->newraw = 0;
+      data->newargs = obj;
+      Py_INCREF(obj);
+    } else {
+#if (PY_VERSION_HEX < 0x02020000)
+      data->newraw = 0;
+#else
+      data->newraw = PyObject_GetAttrString(data->klass, (char *)"__new__");
+#endif
+      if (data->newraw) {
+	Py_INCREF(data->newraw);
+	data->newargs = PyTuple_New(1);
+	PyTuple_SetItem(data->newargs, 0, obj);
+      } else {
+	data->newargs = obj;
+      }
+      Py_INCREF(data->newargs);
+    }
+    /* the destroy method, aka as the C++ delete method */
+    data->destroy = PyObject_GetAttrString(data->klass, (char *)"__swig_destroy__");
+    if (PyErr_Occurred()) {
+      PyErr_Clear();
+      data->destroy = 0;
+    }
+    if (data->destroy) {
+      int flags;
+      Py_INCREF(data->destroy);
+      flags = PyCFunction_GET_FLAGS(data->destroy);
+#ifdef METH_O
+      data->delargs = !(flags & (METH_O));
+#else
+      data->delargs = 0;
+#endif
+    } else {
+      data->delargs = 0;
+    }
+    data->implicitconv = 0;
+    return data;
+  }
+}
+
+SWIGRUNTIME void 
+PySwigClientData_Del(PySwigClientData* data)
+{
+  Py_XDECREF(data->newraw);
+  Py_XDECREF(data->newargs);
+  Py_XDECREF(data->destroy);
+}
+
+/* =============== PySwigObject =====================*/
+
+typedef struct {
+  PyObject_HEAD
+  void *ptr;
+  swig_type_info *ty;
+  int own;
+  PyObject *next;
+} PySwigObject;
+
+SWIGRUNTIME PyObject *
+PySwigObject_long(PySwigObject *v)
+{
+  return PyLong_FromVoidPtr(v->ptr);
+}
+
+SWIGRUNTIME PyObject *
+PySwigObject_format(const char* fmt, PySwigObject *v)
+{
+  PyObject *res = NULL;
+  PyObject *args = PyTuple_New(1);
+  if (args) {
+    if (PyTuple_SetItem(args, 0, PySwigObject_long(v)) == 0) {
+      PyObject *ofmt = PyString_FromString(fmt);
+      if (ofmt) {
+	res = PyString_Format(ofmt,args);
+	Py_DECREF(ofmt);
+      }
+      Py_DECREF(args);
+    }
+  }
+  return res;
+}
+
+SWIGRUNTIME PyObject *
+PySwigObject_oct(PySwigObject *v)
+{
+  return PySwigObject_format("%o",v);
+}
+
+SWIGRUNTIME PyObject *
+PySwigObject_hex(PySwigObject *v)
+{
+  return PySwigObject_format("%x",v);
+}
+
+SWIGRUNTIME PyObject *
+#ifdef METH_NOARGS
+PySwigObject_repr(PySwigObject *v)
+#else
+PySwigObject_repr(PySwigObject *v, PyObject *args)
+#endif
+{
+  const char *name = SWIG_TypePrettyName(v->ty);
+  PyObject *hex = PySwigObject_hex(v);    
+  PyObject *repr = PyString_FromFormat("<Swig Object of type '%s' at 0x%s>", name, PyString_AsString(hex));
+  Py_DECREF(hex);
+  if (v->next) {
+#ifdef METH_NOARGS
+    PyObject *nrep = PySwigObject_repr((PySwigObject *)v->next);
+#else
+    PyObject *nrep = PySwigObject_repr((PySwigObject *)v->next, args);
+#endif
+    PyString_ConcatAndDel(&repr,nrep);
+  }
+  return repr;  
 }
 
 SWIGRUNTIME int
-PySwigObject_compare(PySwigObject *v, PySwigObject *w)
+PySwigObject_print(PySwigObject *v, FILE *fp, int SWIGUNUSEDPARM(flags))
 {
-  int c = strcmp(v->desc, w->desc);
-  if (c) {
-    return (c > 0) ? 1 : -1;
+#ifdef METH_NOARGS
+  PyObject *repr = PySwigObject_repr(v);
+#else
+  PyObject *repr = PySwigObject_repr(v, NULL);
+#endif
+  if (repr) {
+    fputs(PyString_AsString(repr), fp);
+    Py_DECREF(repr);
+    return 0; 
   } else {
-    void *i = v->ptr;
-    void *j = w->ptr;
-    return (i < j) ? -1 : ((i > j) ? 1 : 0);
+    return 1; 
   }
 }
 
-SWIGRUNTIME void
-PySwigObject_dealloc(PySwigObject *self)
+SWIGRUNTIME PyObject *
+PySwigObject_str(PySwigObject *v)
+{
+  char result[SWIG_BUFFER_SIZE];
+  return SWIG_PackVoidPtr(result, v->ptr, v->ty->name, sizeof(result)) ?
+    PyString_FromString(result) : 0;
+}
+
+SWIGRUNTIME int
+PySwigObject_compare(PySwigObject *v, PySwigObject *w)
 {
-  PyObject_Del(self);
+  void *i = v->ptr;
+  void *j = w->ptr;
+  return (i < j) ? -1 : ((i > j) ? 1 : 0);
 }
 
+SWIGRUNTIME PyTypeObject* _PySwigObject_type(void);
+
 SWIGRUNTIME PyTypeObject*
 PySwigObject_type(void) {
-  static char pyswigobject_type__doc__[] = 
-    "Swig object carries a C/C++ instance pointer";
+  static PyTypeObject *SWIG_STATIC_POINTER(type) = _PySwigObject_type();
+  return type;
+}
+
+SWIGRUNTIMEINLINE int
+PySwigObject_Check(PyObject *op) {
+  return ((op)->ob_type == PySwigObject_type())
+    || (strcmp((op)->ob_type->tp_name,"PySwigObject") == 0);
+}
+
+SWIGRUNTIME PyObject *
+PySwigObject_New(void *ptr, swig_type_info *ty, int own);
+
+SWIGRUNTIME void
+PySwigObject_dealloc(PyObject *v)
+{
+  PySwigObject *sobj = (PySwigObject *) v;
+  PyObject *next = sobj->next;
+  if (sobj->own) {
+    swig_type_info *ty = sobj->ty;
+    PySwigClientData *data = ty ? (PySwigClientData *) ty->clientdata : 0;
+    PyObject *destroy = data ? data->destroy : 0;
+    if (destroy) {
+      /* destroy is always a VARARGS method */
+      PyObject *res;
+      if (data->delargs) {
+	/* we need to create a temporal object to carry the destroy operation */
+	PyObject *tmp = PySwigObject_New(sobj->ptr, ty, 0);
+	res = SWIG_Python_CallFunctor(destroy, tmp);
+	Py_DECREF(tmp);
+      } else {
+	PyCFunction meth = PyCFunction_GET_FUNCTION(destroy);
+	PyObject *mself = PyCFunction_GET_SELF(destroy);
+	res = ((*meth)(mself, v));
+      }
+      Py_XDECREF(res);
+    } else {
+      const char *name = SWIG_TypePrettyName(ty);
+#if !defined(SWIG_PYTHON_SILENT_MEMLEAK)
+      printf("swig/python detected a memory leak of type '%s', no destructor found.\n", name);
+#endif
+    }
+  } 
+  Py_XDECREF(next);
+  PyObject_DEL(v);
+}
+
+SWIGRUNTIME PyObject* 
+PySwigObject_append(PyObject* v, PyObject* next)
+{
+  PySwigObject *sobj = (PySwigObject *) v;
+#ifndef METH_O
+  PyObject *tmp = 0;
+  if (!PyArg_ParseTuple(next,(char *)"O:append", &tmp)) return NULL;
+  next = tmp;
+#endif
+  if (!PySwigObject_Check(next)) {
+    return NULL;
+  }
+  sobj->next = next;
+  Py_INCREF(next);
+  return SWIG_Py_Void();
+}
+
+SWIGRUNTIME PyObject* 
+#ifdef METH_NOARGS
+PySwigObject_next(PyObject* v)
+#else
+PySwigObject_next(PyObject* v, PyObject *SWIGUNUSEDPARM(args))
+#endif
+{
+  PySwigObject *sobj = (PySwigObject *) v;
+  if (sobj->next) {    
+    Py_INCREF(sobj->next);
+    return sobj->next;
+  } else {
+    return SWIG_Py_Void();
+  }
+}
+
+SWIGINTERN PyObject*
+#ifdef METH_NOARGS
+PySwigObject_disown(PyObject *v)
+#else
+PySwigObject_disown(PyObject* v, PyObject *SWIGUNUSEDPARM(args))
+#endif
+{
+  PySwigObject *sobj = (PySwigObject *)v;
+  sobj->own = 0;
+  return SWIG_Py_Void();
+}
+
+SWIGINTERN PyObject*
+#ifdef METH_NOARGS
+PySwigObject_acquire(PyObject *v)
+#else
+PySwigObject_acquire(PyObject* v, PyObject *SWIGUNUSEDPARM(args))
+#endif
+{
+  PySwigObject *sobj = (PySwigObject *)v;
+  sobj->own = SWIG_POINTER_OWN;
+  return SWIG_Py_Void();
+}
+
+SWIGINTERN PyObject*
+PySwigObject_own(PyObject *v, PyObject *args)
+{
+  PyObject *val = 0;
+#if (PY_VERSION_HEX < 0x02020000)
+  if (!PyArg_ParseTuple(args,(char *)"|O:own",&val))
+#else
+  if (!PyArg_UnpackTuple(args, (char *)"own", 0, 1, &val)) 
+#endif
+    {
+      return NULL;
+    } 
+  else
+    {
+      PySwigObject *sobj = (PySwigObject *)v;
+      PyObject *obj = PyBool_FromLong(sobj->own);
+      if (val) {
+#ifdef METH_NOARGS
+	if (PyObject_IsTrue(val)) {
+	  PySwigObject_acquire(v);
+	} else {
+	  PySwigObject_disown(v);
+	}
+#else
+	if (PyObject_IsTrue(val)) {
+	  PySwigObject_acquire(v,args);
+	} else {
+	  PySwigObject_disown(v,args);
+	}
+#endif
+      } 
+      return obj;
+    }
+}
+
+#ifdef METH_O
+static PyMethodDef
+swigobject_methods[] = {
+  {(char *)"disown",  (PyCFunction)PySwigObject_disown,  METH_NOARGS,  (char *)"releases ownership of the pointer"},
+  {(char *)"acquire", (PyCFunction)PySwigObject_acquire, METH_NOARGS,  (char *)"aquires ownership of the pointer"},
+  {(char *)"own",     (PyCFunction)PySwigObject_own,     METH_VARARGS, (char *)"returns/sets ownership of the pointer"},
+  {(char *)"append",  (PyCFunction)PySwigObject_append,  METH_O,       (char *)"appends another 'this' object"},
+  {(char *)"next",    (PyCFunction)PySwigObject_next,    METH_NOARGS,  (char *)"returns the next 'this' object"},
+  {(char *)"__repr__",(PyCFunction)PySwigObject_repr,    METH_NOARGS,  (char *)"returns object representation"},
+  {0, 0, 0, 0}  
+};
+#else
+static PyMethodDef
+swigobject_methods[] = {
+  {(char *)"disown",  (PyCFunction)PySwigObject_disown,  METH_VARARGS,  (char *)"releases ownership of the pointer"},
+  {(char *)"acquire", (PyCFunction)PySwigObject_acquire, METH_VARARGS,  (char *)"aquires ownership of the pointer"},
+  {(char *)"own",     (PyCFunction)PySwigObject_own,     METH_VARARGS,  (char *)"returns/sets ownership of the pointer"},
+  {(char *)"append",  (PyCFunction)PySwigObject_append,  METH_VARARGS,  (char *)"appends another 'this' object"},
+  {(char *)"next",    (PyCFunction)PySwigObject_next,    METH_VARARGS,  (char *)"returns the next 'this' object"},
+  {(char *)"__repr__",(PyCFunction)PySwigObject_repr,   METH_VARARGS,  (char *)"returns object representation"},
+  {0, 0, 0, 0}  
+};
+#endif
+
+#if PY_VERSION_HEX < 0x02020000
+SWIGINTERN PyObject *
+PySwigObject_getattr(PySwigObject *sobj,char *name)
+{
+  return Py_FindMethod(swigobject_methods, (PyObject *)sobj, name);
+}
+#endif
+
+SWIGRUNTIME PyTypeObject*
+_PySwigObject_type(void) {
+  static char swigobject_doc[] = "Swig object carries a C/C++ instance pointer";
   
   static PyNumberMethods PySwigObject_as_number = {
     (binaryfunc)0, /*nb_add*/
@@ -797,88 +1613,88 @@ PySwigObject_type(void) {
 #endif
   };
 
-  static PyTypeObject pyswigobject_type
-#if !defined(__cplusplus)
-  ;  
+  static PyTypeObject pyswigobject_type;  
   static int type_init = 0;
   if (!type_init) {
-    PyTypeObject tmp
-#endif
-    = {
-    PyObject_HEAD_INIT(&PyType_Type)
-    0,					/*ob_size*/
-    (char *)"PySwigObject",		/*tp_name*/
-    sizeof(PySwigObject),		/*tp_basicsize*/
-    0,					/*tp_itemsize*/
-    /* methods */
-    (destructor)PySwigObject_dealloc,	/*tp_dealloc*/
-    (printfunc)PySwigObject_print,	/*tp_print*/
-    (getattrfunc)0,			/*tp_getattr*/
-    (setattrfunc)0,			/*tp_setattr*/
-    (cmpfunc)PySwigObject_compare,	/*tp_compare*/
-    (reprfunc)PySwigObject_repr,	/*tp_repr*/
-    &PySwigObject_as_number,	        /*tp_as_number*/
-    0,					/*tp_as_sequence*/
-    0,					/*tp_as_mapping*/
-    (hashfunc)0,			/*tp_hash*/
-    (ternaryfunc)0,			/*tp_call*/
-    (reprfunc)PySwigObject_str,		/*tp_str*/
-    /* Space for future expansion */
-    0,0,0,0,
-    pyswigobject_type__doc__, 	        /* Documentation string */
-#if PY_VERSION_HEX >= 0x02000000
-    0,                                  /* tp_traverse */
-    0,                                  /* tp_clear */
-#endif
-#if PY_VERSION_HEX >= 0x02010000
-    0,                                  /* tp_richcompare */
-    0,                                  /* tp_weaklistoffset */
+    const PyTypeObject tmp
+      = {
+	PyObject_HEAD_INIT(NULL)
+	0,				    /* ob_size */
+	(char *)"PySwigObject",		    /* tp_name */
+	sizeof(PySwigObject),		    /* tp_basicsize */
+	0,			            /* tp_itemsize */
+	(destructor)PySwigObject_dealloc,   /* tp_dealloc */
+	(printfunc)PySwigObject_print,	    /* tp_print */
+#if PY_VERSION_HEX < 0x02020000
+	(getattrfunc)PySwigObject_getattr,  /* tp_getattr */ 
+#else
+	(getattrfunc)0,			    /* tp_getattr */ 
 #endif
+	(setattrfunc)0,			    /* tp_setattr */ 
+	(cmpfunc)PySwigObject_compare,	    /* tp_compare */ 
+	(reprfunc)PySwigObject_repr,	    /* tp_repr */    
+	&PySwigObject_as_number,	    /* tp_as_number */
+	0,				    /* tp_as_sequence */
+	0,				    /* tp_as_mapping */
+	(hashfunc)0,			    /* tp_hash */
+	(ternaryfunc)0,			    /* tp_call */
+	(reprfunc)PySwigObject_str,	    /* tp_str */
+	PyObject_GenericGetAttr,            /* tp_getattro */
+	0,				    /* tp_setattro */
+	0,		                    /* tp_as_buffer */
+	Py_TPFLAGS_DEFAULT,	            /* tp_flags */
+	swigobject_doc, 	            /* tp_doc */        
+	0,                                  /* tp_traverse */
+	0,                                  /* tp_clear */
+	0,                                  /* tp_richcompare */
+	0,                                  /* tp_weaklistoffset */
 #if PY_VERSION_HEX >= 0x02020000
-    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* tp_iter -> tp_weaklist */
+	0,                                  /* tp_iter */
+	0,                                  /* tp_iternext */
+	swigobject_methods,		    /* tp_methods */ 
+	0,			            /* tp_members */
+	0,				    /* tp_getset */	    	
+	0,			            /* tp_base */	        
+	0,				    /* tp_dict */	    	
+	0,				    /* tp_descr_get */  	
+	0,				    /* tp_descr_set */  	
+	0,				    /* tp_dictoffset */ 	
+	0,				    /* tp_init */	    	
+	0,				    /* tp_alloc */	    	
+	0,			            /* tp_new */	    	
+	0,	                            /* tp_free */	   
+        0,                                  /* tp_is_gc */  
+	0,				    /* tp_bases */   
+	0,				    /* tp_mro */
+	0,				    /* tp_cache */   
+ 	0,				    /* tp_subclasses */
+	0,				    /* tp_weaklist */
 #endif
 #if PY_VERSION_HEX >= 0x02030000
-    0,                                  /* tp_del */
+	0,                                  /* tp_del */
 #endif
 #ifdef COUNT_ALLOCS
-    0,0,0,0                             /* tp_alloc -> tp_next */
+	0,0,0,0                             /* tp_alloc -> tp_next */
 #endif
-    };
-#if !defined(__cplusplus)
+      };
     pyswigobject_type = tmp;
+    pyswigobject_type.ob_type = &PyType_Type;
     type_init = 1;
   }
-#endif
   return &pyswigobject_type;
 }
 
 SWIGRUNTIME PyObject *
-PySwigObject_FromVoidPtrAndDesc(void *ptr, const char *desc)
+PySwigObject_New(void *ptr, swig_type_info *ty, int own)
 {
-  PySwigObject *self = PyObject_NEW(PySwigObject, PySwigObject_type());
-  if (self) {
-    self->ptr = ptr;
-    self->desc = desc;
+  PySwigObject *sobj = PyObject_NEW(PySwigObject, PySwigObject_type());
+  if (sobj) {
+    sobj->ptr  = ptr;
+    sobj->ty   = ty;
+    sobj->own  = own;
+    sobj->next = 0;
   }
-  return (PyObject *)self;
-}
-
-SWIGRUNTIMEINLINE void *
-PySwigObject_AsVoidPtr(PyObject *self)
-{
-  return ((PySwigObject *)self)->ptr;
-}
-
-SWIGRUNTIMEINLINE const char *
-PySwigObject_GetDesc(PyObject *self)
-{
-  return ((PySwigObject *)self)->desc;
-}
-
-SWIGRUNTIMEINLINE int
-PySwigObject_Check(PyObject *op) {
-  return ((op)->ob_type == PySwigObject_type()) 
-    || (strcmp((op)->ob_type->tp_name,"PySwigObject") == 0);
+  return (PyObject *)sobj;
 }
 
 /* -----------------------------------------------------------------------------
@@ -888,21 +1704,20 @@ PySwigObject_Check(PyObject *op) {
 typedef struct {
   PyObject_HEAD
   void *pack;
-  const char *desc;
+  swig_type_info *ty;
   size_t size;
 } PySwigPacked;
 
 SWIGRUNTIME int
-PySwigPacked_print(PySwigPacked *v, FILE *fp, int flags)
+PySwigPacked_print(PySwigPacked *v, FILE *fp, int SWIGUNUSEDPARM(flags))
 {
   char result[SWIG_BUFFER_SIZE];
-  flags = flags;
   fputs("<Swig Packed ", fp); 
   if (SWIG_PackDataName(result, v->pack, v->size, 0, sizeof(result))) {
     fputs("at ", fp); 
     fputs(result, fp); 
   }
-  fputs(v->desc,fp); 
+  fputs(v->ty->name,fp); 
   fputs(">", fp);
   return 0; 
 }
@@ -912,9 +1727,9 @@ PySwigPacked_repr(PySwigPacked *v)
 {
   char result[SWIG_BUFFER_SIZE];
   if (SWIG_PackDataName(result, v->pack, v->size, 0, sizeof(result))) {
-    return PyString_FromFormat("<Swig Packed at %s%s>", result, v->desc);
+    return PyString_FromFormat("<Swig Packed at %s%s>", result, v->ty->name);
   } else {
-    return PyString_FromFormat("<Swig Packed %s>", v->desc);
+    return PyString_FromFormat("<Swig Packed %s>", v->ty->name);
   }  
 }
 
@@ -923,434 +1738,489 @@ PySwigPacked_str(PySwigPacked *v)
 {
   char result[SWIG_BUFFER_SIZE];
   if (SWIG_PackDataName(result, v->pack, v->size, 0, sizeof(result))){
-    return PyString_FromFormat("%s%s", result, v->desc);
+    return PyString_FromFormat("%s%s", result, v->ty->name);
   } else {
-    return PyString_FromString(v->desc);
+    return PyString_FromString(v->ty->name);
   }  
 }
 
 SWIGRUNTIME int
 PySwigPacked_compare(PySwigPacked *v, PySwigPacked *w)
 {
-  int c = strcmp(v->desc, w->desc);
-  if (c) {
-    return (c > 0) ? 1 : -1;
-  } else {
-    size_t i = v->size;
-    size_t j = w->size;
-    int s = (i < j) ? -1 : ((i > j) ? 1 : 0);
-    return s ? s : strncmp((char *)v->pack, (char *)w->pack, 2*v->size);
-  }
+  size_t i = v->size;
+  size_t j = w->size;
+  int s = (i < j) ? -1 : ((i > j) ? 1 : 0);
+  return s ? s : strncmp((char *)v->pack, (char *)w->pack, 2*v->size);
+}
+
+SWIGRUNTIME PyTypeObject* _PySwigPacked_type(void);
+
+SWIGRUNTIME PyTypeObject*
+PySwigPacked_type(void) {
+  static PyTypeObject *SWIG_STATIC_POINTER(type) = _PySwigPacked_type();
+  return type;
+}
+
+SWIGRUNTIMEINLINE int
+PySwigPacked_Check(PyObject *op) {
+  return ((op)->ob_type == _PySwigPacked_type()) 
+    || (strcmp((op)->ob_type->tp_name,"PySwigPacked") == 0);
 }
 
 SWIGRUNTIME void
-PySwigPacked_dealloc(PySwigPacked *self)
+PySwigPacked_dealloc(PyObject *v)
 {
-  free(self->pack);
-  PyObject_Del(self);
+  if (PySwigPacked_Check(v)) {
+    PySwigPacked *sobj = (PySwigPacked *) v;
+    free(sobj->pack);
+  }
+  PyObject_DEL(v);
 }
 
 SWIGRUNTIME PyTypeObject*
-PySwigPacked_type(void) {
-  static char pyswigpacked_type__doc__[] = 
-    "Swig object carries a C/C++ instance pointer";
-  static PyTypeObject pyswigpacked_type
-#if !defined(__cplusplus)
-  ;
+_PySwigPacked_type(void) {
+  static char swigpacked_doc[] = "Swig object carries a C/C++ instance pointer";
+  static PyTypeObject pyswigpacked_type;
   static int type_init = 0;  
   if (!type_init) {
-    PyTypeObject tmp
-#endif
-    = {
-    PyObject_HEAD_INIT(&PyType_Type)
-    0,					/*ob_size*/
-    (char *)"PySwigPacked",		/*tp_name*/
-    sizeof(PySwigPacked),		/*tp_basicsize*/
-    0,					/*tp_itemsize*/
-    /* methods */
-    (destructor)PySwigPacked_dealloc,	/*tp_dealloc*/
-    (printfunc)PySwigPacked_print,	/*tp_print*/
-    (getattrfunc)0,			/*tp_getattr*/
-    (setattrfunc)0,			/*tp_setattr*/
-    (cmpfunc)PySwigPacked_compare,	/*tp_compare*/
-    (reprfunc)PySwigPacked_repr,	/*tp_repr*/
-    0,	                                /*tp_as_number*/
-    0,					/*tp_as_sequence*/
-    0,					/*tp_as_mapping*/
-    (hashfunc)0,			/*tp_hash*/
-    (ternaryfunc)0,			/*tp_call*/
-    (reprfunc)PySwigPacked_str,		/*tp_str*/
-    /* Space for future expansion */
-    0,0,0,0,
-    pyswigpacked_type__doc__, 	        /* Documentation string */
-#if PY_VERSION_HEX >= 0x02000000
-    0,                                  /* tp_traverse */
-    0,                                  /* tp_clear */
-#endif
-#if PY_VERSION_HEX >= 0x02010000
-    0,                                  /* tp_richcompare */
-    0,                                  /* tp_weaklistoffset */
-#endif
-#if PY_VERSION_HEX >= 0x02020000         
-    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* tp_iter -> tp_weaklist */
+    const PyTypeObject tmp
+      = {
+	PyObject_HEAD_INIT(NULL)
+	0,				    /* ob_size */	
+	(char *)"PySwigPacked",		    /* tp_name */	
+	sizeof(PySwigPacked),		    /* tp_basicsize */	
+	0,				    /* tp_itemsize */	
+	(destructor)PySwigPacked_dealloc,   /* tp_dealloc */	
+	(printfunc)PySwigPacked_print,	    /* tp_print */   	
+	(getattrfunc)0,			    /* tp_getattr */ 	
+	(setattrfunc)0,			    /* tp_setattr */ 	
+	(cmpfunc)PySwigPacked_compare,	    /* tp_compare */ 	
+	(reprfunc)PySwigPacked_repr,	    /* tp_repr */    	
+	0,	                            /* tp_as_number */	
+	0,				    /* tp_as_sequence */
+	0,				    /* tp_as_mapping */	
+	(hashfunc)0,			    /* tp_hash */	
+	(ternaryfunc)0,			    /* tp_call */	
+	(reprfunc)PySwigPacked_str,	    /* tp_str */	
+	PyObject_GenericGetAttr,            /* tp_getattro */
+	0,				    /* tp_setattro */
+	0,		                    /* tp_as_buffer */
+	Py_TPFLAGS_DEFAULT,	            /* tp_flags */
+	swigpacked_doc, 	            /* tp_doc */
+	0,                                  /* tp_traverse */
+	0,                                  /* tp_clear */
+	0,                                  /* tp_richcompare */
+	0,                                  /* tp_weaklistoffset */
+#if PY_VERSION_HEX >= 0x02020000
+	0,                                  /* tp_iter */
+	0,                                  /* tp_iternext */
+	0,		                    /* tp_methods */ 
+	0,			            /* tp_members */
+	0,				    /* tp_getset */	    	
+	0,			            /* tp_base */	        
+	0,				    /* tp_dict */	    	
+	0,				    /* tp_descr_get */  	
+	0,				    /* tp_descr_set */  	
+	0,				    /* tp_dictoffset */ 	
+	0,				    /* tp_init */	    	
+	0,				    /* tp_alloc */	    	
+	0,			            /* tp_new */	    	
+	0, 	                            /* tp_free */	   
+        0,                                  /* tp_is_gc */  
+	0,				    /* tp_bases */   
+	0,				    /* tp_mro */
+	0,				    /* tp_cache */   
+ 	0,				    /* tp_subclasses */
+	0,				    /* tp_weaklist */
 #endif
 #if PY_VERSION_HEX >= 0x02030000
-    0,                                  /* tp_del */
+	0,                                  /* tp_del */
 #endif
 #ifdef COUNT_ALLOCS
-    0,0,0,0                             /* tp_alloc -> tp_next */
+	0,0,0,0                             /* tp_alloc -> tp_next */
 #endif
-    };
-#if !defined(__cplusplus)
+      };
     pyswigpacked_type = tmp;
+    pyswigpacked_type.ob_type = &PyType_Type;
     type_init = 1;
   }
-#endif
   return &pyswigpacked_type;
 }
 
 SWIGRUNTIME PyObject *
-PySwigPacked_FromDataAndDesc(void *ptr, size_t size, const char *desc)
+PySwigPacked_New(void *ptr, size_t size, swig_type_info *ty)
 {
-  PySwigPacked *self = PyObject_NEW(PySwigPacked, PySwigPacked_type());
-  if (self == NULL) {
-    return NULL;
-  } else {
+  PySwigPacked *sobj = PyObject_NEW(PySwigPacked, PySwigPacked_type());
+  if (sobj) {
     void *pack = malloc(size);
     if (pack) {
       memcpy(pack, ptr, size);
-      self->pack = pack;
-      self->desc = desc;
-      self->size = size;
-      return (PyObject *) self;
+      sobj->pack = pack;
+      sobj->ty   = ty;
+      sobj->size = size;
+    } else {
+      PyObject_DEL((PyObject *) sobj);
+      sobj = 0;
     }
-    return NULL;
   }
+  return (PyObject *) sobj;
 }
 
-SWIGRUNTIMEINLINE const char *
+SWIGRUNTIME swig_type_info *
 PySwigPacked_UnpackData(PyObject *obj, void *ptr, size_t size)
 {
-  PySwigPacked *self = (PySwigPacked *)obj;
-  if (self->size != size) return 0;
-  memcpy(ptr, self->pack, size);
-  return self->desc;
+  if (PySwigPacked_Check(obj)) {
+    PySwigPacked *sobj = (PySwigPacked *)obj;
+    if (sobj->size != size) return 0;
+    memcpy(ptr, sobj->pack, size);
+    return sobj->ty;
+  } else {
+    return 0;
+  }
 }
 
-SWIGRUNTIMEINLINE const char *
-PySwigPacked_GetDesc(PyObject *self)
+/* -----------------------------------------------------------------------------
+ * pointers/data manipulation
+ * ----------------------------------------------------------------------------- */
+
+SWIGRUNTIMEINLINE PyObject *
+_SWIG_This(void)
 {
-  return ((PySwigPacked *)self)->desc;
+  return PyString_FromString("this");
 }
 
-SWIGRUNTIMEINLINE int
-PySwigPacked_Check(PyObject *op) {
-  return ((op)->ob_type == PySwigPacked_type()) 
-    || (strcmp((op)->ob_type->tp_name,"PySwigPacked") == 0);
+SWIGRUNTIME PyObject *
+SWIG_This(void)
+{
+  static PyObject *SWIG_STATIC_POINTER(swig_this) = _SWIG_This();
+  return swig_this;
 }
 
-#else
-/* -----------------------------------------------------------------------------
- * Use the old Python PyCObject instead of PySwigObject
- * ----------------------------------------------------------------------------- */
-
-#define PySwigObject_GetDesc(obj)	           PyCObject_GetDesc(obj)
-#define PySwigObject_Check(obj)	           PyCObject_Check(obj)
-#define PySwigObject_AsVoidPtr(obj)	   PyCObject_AsVoidPtr(obj)
-#define PySwigObject_FromVoidPtrAndDesc(p, d)  PyCObject_FromVoidPtrAndDesc(p, d, NULL)
-
-#endif
+/* #define SWIG_PYTHON_SLOW_GETSET_THIS */
 
+SWIGRUNTIME PySwigObject *
+SWIG_Python_GetSwigThis(PyObject *pyobj) 
+{
+  if (PySwigObject_Check(pyobj)) {
+    return (PySwigObject *) pyobj;
+  } else {
+    PyObject *obj = 0;
+#if (!defined(SWIG_PYTHON_SLOW_GETSET_THIS) && (PY_VERSION_HEX >= 0x02030000))
+    if (PyInstance_Check(pyobj)) {
+      obj = _PyInstance_Lookup(pyobj, SWIG_This());      
+    } else {
+      PyObject **dictptr = _PyObject_GetDictPtr(pyobj);
+      if (dictptr != NULL) {
+	PyObject *dict = *dictptr;
+	obj = dict ? PyDict_GetItem(dict, SWIG_This()) : 0;
+      } else {
+#ifdef PyWeakref_CheckProxy
+	if (PyWeakref_CheckProxy(pyobj)) {
+	  PyObject *wobj = PyWeakref_GET_OBJECT(pyobj);
+	  return wobj ? SWIG_Python_GetSwigThis(wobj) : 0;
+	}
 #endif
-
-/* -----------------------------------------------------------------------------
- * errors manipulation
- * ----------------------------------------------------------------------------- */
-
-SWIGRUNTIME void
-SWIG_Python_TypeError(const char *type, PyObject *obj)
-{
-  if (type) {
-#if defined(SWIG_COBJECT_TYPES)
-    if (obj && PySwigObject_Check(obj)) {
-      const char *otype = (const char *) PySwigObject_GetDesc(obj);
-      if (otype) {
-	PyErr_Format(PyExc_TypeError, "a '%s' is expected, 'PySwigObject(%s)' is received",
-		     type, otype);
-	return;
-      }
-    } else 
-#endif      
-    {
-      const char *otype = (obj ? obj->ob_type->tp_name : 0); 
-      if (otype) {
-	PyObject *str = PyObject_Str(obj);
-	const char *cstr = str ? PyString_AsString(str) : 0;
-	if (cstr) {
-	  PyErr_Format(PyExc_TypeError, "a '%s' is expected, '%s(%s)' is received",
-		       type, otype, cstr);
+	obj = PyObject_GetAttr(pyobj,SWIG_This());
+	if (obj) {
+	  Py_DECREF(obj);
 	} else {
-	  PyErr_Format(PyExc_TypeError, "a '%s' is expected, '%s' is received",
-		       type, otype);
+	  if (PyErr_Occurred()) PyErr_Clear();
+	  return 0;
 	}
-	Py_XDECREF(str);
-	return;
       }
-    }   
-    PyErr_Format(PyExc_TypeError, "a '%s' is expected", type);
-  } else {
-    PyErr_Format(PyExc_TypeError, "unexpected type is received");
+    }
+#else
+    obj = PyObject_GetAttr(pyobj,SWIG_This());
+    if (obj) {
+      Py_DECREF(obj);
+    } else {
+      if (PyErr_Occurred()) PyErr_Clear();
+      return 0;
+    }
+#endif
+    if (obj && !PySwigObject_Check(obj)) {
+      /* a PyObject is called 'this', try to get the 'real this'
+	 PySwigObject from it */ 
+      return SWIG_Python_GetSwigThis(obj);
+    }
+    return (PySwigObject *)obj;
   }
 }
 
-SWIGRUNTIMEINLINE void
-SWIG_Python_NullRef(const char *type)
-{
-  if (type) {
-    PyErr_Format(PyExc_TypeError, "null reference of type '%s' was received",type);
-  } else {
-    PyErr_Format(PyExc_TypeError, "null reference was received");
-  }
-}
+/* Acquire a pointer value */
 
 SWIGRUNTIME int
-SWIG_Python_AddErrMesg(const char* mesg, int infront)
-{
-  if (PyErr_Occurred()) {
-    PyObject *type = 0;
-    PyObject *value = 0;
-    PyObject *traceback = 0;
-    PyErr_Fetch(&type, &value, &traceback);
-    if (value) {
-      PyObject *old_str = PyObject_Str(value);
-      Py_XINCREF(type);
-      PyErr_Clear();
-      if (infront) {
-	PyErr_Format(type, "%s %s", mesg, PyString_AsString(old_str));
-      } else {
-	PyErr_Format(type, "%s %s", PyString_AsString(old_str), mesg);
-      }
-      Py_DECREF(old_str);
+SWIG_Python_AcquirePtr(PyObject *obj, int own) {
+  if (own) {
+    PySwigObject *sobj = SWIG_Python_GetSwigThis(obj);
+    if (sobj) {
+      int oldown = sobj->own;
+      sobj->own = own;
+      return oldown;
     }
-    return 1;
-  } else {
-    return 0;
   }
+  return 0;
 }
 
+/* Convert a pointer value */
+
 SWIGRUNTIME int
-SWIG_Python_ArgFail(int argnum)
-{
-  if (PyErr_Occurred()) {
-    /* add information about failing argument */
-    char mesg[256];
-    PyOS_snprintf(mesg, sizeof(mesg), "argument number %d:", argnum);
-    return SWIG_Python_AddErrMesg(mesg, 1);
+SWIG_Python_ConvertPtrAndOwn(PyObject *obj, void **ptr, swig_type_info *ty, int flags, int *own) {
+  if (!obj) return SWIG_ERROR;
+  if (obj == Py_None) {
+    if (ptr) *ptr = 0;
+    return SWIG_OK;
   } else {
-    return 0;
+    PySwigObject *sobj = SWIG_Python_GetSwigThis(obj);
+    while (sobj) {
+      void *vptr = sobj->ptr;
+      if (ty) {
+	swig_type_info *to = sobj->ty;
+	if (to == ty) {
+	  /* no type cast needed */
+	  if (ptr) *ptr = vptr;
+	  break;
+	} else {
+	  swig_cast_info *tc = SWIG_TypeCheck(to->name,ty);
+	  if (!tc) {
+	    sobj = (PySwigObject *)sobj->next;
+	  } else {
+	    if (ptr) *ptr = SWIG_TypeCast(tc,vptr);
+	    break;
+	  }
+	}
+      } else {
+	if (ptr) *ptr = vptr;
+	break;
+      }
+    }
+    if (sobj) {
+      if (own) *own = sobj->own;
+      if (flags & SWIG_POINTER_DISOWN) {
+	sobj->own = 0;
+      }
+      return SWIG_OK;
+    } else {
+      int res = SWIG_ERROR;
+      if (flags & SWIG_POINTER_IMPLICIT_CONV) {
+	PySwigClientData *data = ty ? (PySwigClientData *) ty->clientdata : 0;
+	if (data && !data->implicitconv) {
+	  PyObject *klass = data->klass;
+	  if (klass) {
+	    PyObject *impconv;
+	    data->implicitconv = 1; /* avoid recursion and call 'explicit' constructors*/
+	    impconv = SWIG_Python_CallFunctor(klass, obj);
+	    data->implicitconv = 0;
+	    if (PyErr_Occurred()) {
+	      PyErr_Clear();
+	      impconv = 0;
+	    }
+	    if (impconv) {
+	      PySwigObject *iobj = SWIG_Python_GetSwigThis(impconv);
+	      if (iobj) {
+		void *vptr;
+		res = SWIG_Python_ConvertPtrAndOwn((PyObject*)iobj, &vptr, ty, 0, 0);
+		if (SWIG_IsOK(res)) {
+		  if (ptr) {
+		    *ptr = vptr;
+		    /* transfer the ownership to 'ptr' */
+		    iobj->own = 0;
+		    res = SWIG_AddCast(res);
+		    res = SWIG_AddNewMask(res);
+		  } else {
+		    res = SWIG_AddCast(res);		    
+		  }
+		}
+	      }
+	      Py_DECREF(impconv);
+	    }
+	  }
+	}
+      }
+      return res;
+    }
   }
 }
 
+/* Convert a function ptr value */
 
-/* -----------------------------------------------------------------------------
- * pointers/data manipulation
- * ----------------------------------------------------------------------------- */
-
-/* Convert a pointer value */
 SWIGRUNTIME int
-SWIG_Python_ConvertPtr(PyObject *obj, void **ptr, swig_type_info *ty, int flags) {
-  swig_cast_info *tc;
-  const char *c = 0;
-  static PyObject *SWIG_this = 0;
-  int    newref = 0;
-  PyObject  *pyobj = 0;
-  void *vptr;
-  
-  if (!obj) return 0;
-  if (obj == Py_None) {
-    *ptr = 0;
-    return 0;
-  }
-
-#ifdef SWIG_COBJECT_TYPES
-  if (!(PySwigObject_Check(obj))) {
-    if (!SWIG_this)
-      SWIG_this = PyString_FromString("this");
-    pyobj = obj;
-    obj = PyObject_GetAttr(obj,SWIG_this);
-    newref = 1;
-    if (!obj) goto type_error;
-    if (!PySwigObject_Check(obj)) {
-      Py_DECREF(obj);
-      goto type_error;
-    }
-  }  
-  vptr = PySwigObject_AsVoidPtr(obj);
-  c = (const char *) PySwigObject_GetDesc(obj);
-  if (newref) { Py_DECREF(obj); }
-  goto type_check;
-#else
-  if (!(PyString_Check(obj))) {
-    if (!SWIG_this)
-      SWIG_this = PyString_FromString("this");
-    pyobj = obj;
-    obj = PyObject_GetAttr(obj,SWIG_this);
-    newref = 1;
-    if (!obj) goto type_error;
-    if (!PyString_Check(obj)) {
-      Py_DECREF(obj);
-      goto type_error;
-    }
-  } 
-  c = PyString_AsString(obj);
-  /* Pointer values must start with leading underscore */
-  c = SWIG_UnpackVoidPtr(c, &vptr, ty->name);
-  if (newref) { Py_DECREF(obj); }
-  if (!c) goto type_error;
-#endif
-
-type_check:
-  if (ty) {
-    tc = SWIG_TypeCheck(c,ty);
-    if (!tc) goto type_error;
-    *ptr = SWIG_TypeCast(tc,vptr);
+SWIG_Python_ConvertFunctionPtr(PyObject *obj, void **ptr, swig_type_info *ty) {
+  if (!PyCFunction_Check(obj)) {
+    return SWIG_ConvertPtr(obj, ptr, ty, 0);
   } else {
-    *ptr = vptr;
-  }
-  if ((pyobj) && (flags & SWIG_POINTER_DISOWN)) {
-    PyObject_SetAttrString(pyobj,(char*)"thisown",Py_False);
-  }
-  return 0;
-
-type_error:
-  PyErr_Clear();
-  if (pyobj && !obj) {    
-    obj = pyobj;
-    if (PyCFunction_Check(obj)) {
-      /* here we get the method pointer for callbacks */
-      char *doc = (((PyCFunctionObject *)obj) -> m_ml -> ml_doc);
-      c = doc ? strstr(doc, "swig_ptr: ") : 0;
-      if (c) {
-	c = ty ? SWIG_UnpackVoidPtr(c + 10, &vptr, ty->name) : 0;
-	if (!c) goto type_error;
-	goto type_check;
-      }
+    void *vptr = 0;
+    
+    /* here we get the method pointer for callbacks */
+    const char *doc = (((PyCFunctionObject *)obj) -> m_ml -> ml_doc);
+    const char *desc = doc ? strstr(doc, "swig_ptr: ") : 0;
+    if (desc) {
+      desc = ty ? SWIG_UnpackVoidPtr(desc + 10, &vptr, ty->name) : 0;
+      if (!desc) return SWIG_ERROR;
     }
-  }
-  if (flags & SWIG_POINTER_EXCEPTION) {
     if (ty) {
-      SWIG_Python_TypeError(SWIG_TypePrettyName(ty), obj);
+      swig_cast_info *tc = SWIG_TypeCheck(desc,ty);
+      if (!tc) return SWIG_ERROR;
+      *ptr = SWIG_TypeCast(tc,vptr);
     } else {
-      SWIG_Python_TypeError("C/C++ pointer", obj);
+      *ptr = vptr;
     }
+    return SWIG_OK;
   }
-  return -1;
 }
 
-/* Convert a pointer value, signal an exception on a type mismatch */
-SWIGRUNTIME void *
-SWIG_Python_MustGetPtr(PyObject *obj, swig_type_info *ty, int argnum, int flags) {
-  void *result;
-  if (SWIG_Python_ConvertPtr(obj, &result, ty, flags) == -1) {
-    PyErr_Clear();
-    if (flags & SWIG_POINTER_EXCEPTION) {
-      SWIG_Python_TypeError(SWIG_TypePrettyName(ty), obj);
-      SWIG_Python_ArgFail(argnum);
+/* Convert a packed value value */
+
+SWIGRUNTIME int
+SWIG_Python_ConvertPacked(PyObject *obj, void *ptr, size_t sz, swig_type_info *ty) {
+  swig_type_info *to = PySwigPacked_UnpackData(obj, ptr, sz);
+  if (!to) return SWIG_ERROR;
+  if (ty) {
+    if (to != ty) {
+      /* check type cast? */
+      swig_cast_info *tc = SWIG_TypeCheck(to->name,ty);
+      if (!tc) return SWIG_ERROR;
     }
   }
-  return result;
-}
+  return SWIG_OK;
+}  
 
-/* Convert a packed value value */
-SWIGRUNTIME int
-SWIG_Python_ConvertPacked(PyObject *obj, void *ptr, size_t sz, swig_type_info *ty, int flags) {
-  swig_cast_info *tc;
-  const char *c = 0;
+/* -----------------------------------------------------------------------------
+ * Create a new pointer object
+ * ----------------------------------------------------------------------------- */
+
+/*
+  Create a new instance object, whitout calling __init__, and set the
+  'this' attribute.
+*/
 
-#if defined(SWIG_COBJECT_TYPES) && !defined(SWIG_COBJECT_PYTHON)
-  c = PySwigPacked_UnpackData(obj, ptr, sz);
+SWIGRUNTIME PyObject* 
+SWIG_Python_NewShadowInstance(PySwigClientData *data, PyObject *swig_this)
+{
+#if (PY_VERSION_HEX >= 0x02020000)
+  PyObject *inst = 0;
+  PyObject *newraw = data->newraw;
+  if (newraw) {
+    inst = PyObject_Call(newraw, data->newargs, NULL);
+    if (inst) {
+#if !defined(SWIG_PYTHON_SLOW_GETSET_THIS)
+      PyObject **dictptr = _PyObject_GetDictPtr(inst);
+      if (dictptr != NULL) {
+	PyObject *dict = *dictptr;
+	if (dict == NULL) {
+	  dict = PyDict_New();
+	  *dictptr = dict;
+	  PyDict_SetItem(dict, SWIG_This(), swig_this);
+	}
+      }
 #else
-  if ((!obj) || (!PyString_Check(obj))) goto type_error;
-  c = PyString_AsString(obj);
-  /* Pointer values must start with leading underscore */
-  c = SWIG_UnpackDataName(c, ptr, sz, ty->name);
+      PyObject *key = SWIG_This();
+      PyObject_SetAttr(inst, key, swig_this);
 #endif
-  if (!c) goto type_error;
-  if (ty) {
-    tc = SWIG_TypeCheck(c,ty);
-    if (!tc) goto type_error;
+    }
+  } else {
+    PyObject *dict = PyDict_New();
+    PyDict_SetItem(dict, SWIG_This(), swig_this);
+    inst = PyInstance_NewRaw(data->newargs, dict);
+    Py_DECREF(dict);
   }
-  return 0;
+  return inst;
+#else
+#if (PY_VERSION_HEX >= 0x02010000)
+  PyObject *inst;
+  PyObject *dict = PyDict_New();
+  PyDict_SetItem(dict, SWIG_This(), swig_this);
+  inst = PyInstance_NewRaw(data->newargs, dict);
+  Py_DECREF(dict);
+  return (PyObject *) inst;
+#else
+  PyInstanceObject *inst = PyObject_NEW(PyInstanceObject, &PyInstance_Type);
+  if (inst == NULL) {
+    return NULL;
+  }
+  inst->in_class = (PyClassObject *)data->newargs;
+  Py_INCREF(inst->in_class);
+  inst->in_dict = PyDict_New();
+  if (inst->in_dict == NULL) {
+    Py_DECREF(inst);
+    return NULL;
+  }
+#ifdef Py_TPFLAGS_HAVE_WEAKREFS
+  inst->in_weakreflist = NULL;
+#endif
+#ifdef Py_TPFLAGS_GC
+  PyObject_GC_Init(inst);
+#endif
+  PyDict_SetItem(inst->in_dict, SWIG_This(), swig_this);
+  return (PyObject *) inst;
+#endif
+#endif
+}
 
-type_error:
-  PyErr_Clear();
-  if (flags & SWIG_POINTER_EXCEPTION) {
-    if (ty) {
-      SWIG_Python_TypeError(SWIG_TypePrettyName(ty), obj);
+SWIGRUNTIME void
+SWIG_Python_SetSwigThis(PyObject *inst, PyObject *swig_this)
+{
+ PyObject *dict;
+#if (PY_VERSION_HEX >= 0x02020000) && !defined(SWIG_PYTHON_SLOW_GETSET_THIS)
+ PyObject **dictptr = _PyObject_GetDictPtr(inst);
+ if (dictptr != NULL) {
+   dict = *dictptr;
+   if (dict == NULL) {
+     dict = PyDict_New();
+     *dictptr = dict;
+   }
+   PyDict_SetItem(dict, SWIG_This(), swig_this);
+   return;
+ }
+#endif
+ dict = PyObject_GetAttrString(inst, "__dict__");
+ PyDict_SetItem(dict, SWIG_This(), swig_this);
+ Py_DECREF(dict);
+} 
+
+
+SWIGINTERN PyObject *
+SWIG_Python_InitShadowInstance(PyObject *args) {
+  PyObject *obj[2];
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swiginit", 2, 2, obj)) {
+    return NULL;
+  } else {
+    PySwigObject *sthis = SWIG_Python_GetSwigThis(obj[0]);
+    if (sthis) {
+      PySwigObject_append((PyObject*) sthis, obj[1]);
     } else {
-      SWIG_Python_TypeError("C/C++ packed data", obj);
+      SWIG_Python_SetSwigThis(obj[0], obj[1]);
     }
+    return SWIG_Py_Void();
   }
-  return -1;
-}  
+}
+
+/* Create a new pointer object */
 
-/* Create a new array object */
 SWIGRUNTIME PyObject *
-SWIG_Python_NewPointerObj(void *ptr, swig_type_info *type, int own) {
-  PyObject *robj = 0;
-  if (!type) {
-    if (!PyErr_Occurred()) {
-      PyErr_Format(PyExc_TypeError, "Swig: null type passed to NewPointerObj");
-    }
-    return robj;
-  }
+SWIG_Python_NewPointerObj(void *ptr, swig_type_info *type, int flags) {
   if (!ptr) {
-    Py_INCREF(Py_None);
-    return Py_None;
-  }
-#ifdef SWIG_COBJECT_TYPES
-  robj = PySwigObject_FromVoidPtrAndDesc((void *) ptr, (char *)type->name);
-#else
-  {
-    char result[SWIG_BUFFER_SIZE];
-    robj = SWIG_PackVoidPtr(result, ptr, type->name, sizeof(result)) ?
-      PyString_FromString(result) : 0;
-  }
-#endif
-  if (!robj || (robj == Py_None)) return robj;
-  if (type->clientdata) {
-    PyObject *inst;
-    PyObject *args = Py_BuildValue((char*)"(O)", robj);
-    Py_DECREF(robj);
-    inst = PyObject_CallObject((PyObject *) type->clientdata, args);
-    Py_DECREF(args);
-    if (inst) {
-      if (own) {
-        PyObject_SetAttrString(inst,(char*)"thisown",Py_True);
+    return SWIG_Py_Void();
+  } else {
+    int own = (flags & SWIG_POINTER_OWN) ? SWIG_POINTER_OWN : 0;
+    PyObject *robj = PySwigObject_New(ptr, type, own);
+    PySwigClientData *clientdata = type ? (PySwigClientData *)(type->clientdata) : 0;
+    if (clientdata && !(flags & SWIG_POINTER_NOSHADOW)) {
+      PyObject *inst = SWIG_Python_NewShadowInstance(clientdata, robj);
+      if (inst) {
+	Py_DECREF(robj);
+	robj = inst;
       }
-      robj = inst;
     }
+    return robj;
   }
-  return robj;
 }
 
-SWIGRUNTIME PyObject *
+/* Create a new packed object */
+
+SWIGRUNTIMEINLINE PyObject *
 SWIG_Python_NewPackedObj(void *ptr, size_t sz, swig_type_info *type) {
-  PyObject *robj = 0;
-  if (!ptr) {
-    Py_INCREF(Py_None);
-    return Py_None;
-  }
-#if defined(SWIG_COBJECT_TYPES) && !defined(SWIG_COBJECT_PYTHON)
-  robj = PySwigPacked_FromDataAndDesc((void *) ptr, sz, (char *)type->name);
-#else
-  {
-    char result[SWIG_BUFFER_SIZE];
-    robj = SWIG_PackDataName(result, ptr, sz, type->name, sizeof(result)) ?
-      PyString_FromString(result) : 0;
-  }
-#endif
-  return robj;
+  return ptr ? PySwigPacked_New((void *) ptr, sz, type) : SWIG_Py_Void();
 }
 
 /* -----------------------------------------------------------------------------*
@@ -1382,7 +2252,7 @@ SWIG_Python_GetModule(void) {
 
 #if PY_MAJOR_VERSION < 2
 /* PyModule_AddObject function was introduced in Python 2.0.  The following function
-is copied out of Python/modsupport.c in python version 2.3.4 */
+   is copied out of Python/modsupport.c in python version 2.3.4 */
 SWIGINTERN int
 PyModule_AddObject(PyObject *m, char *name, PyObject *o)
 {
@@ -1390,12 +2260,12 @@ PyModule_AddObject(PyObject *m, char *na
   if (!PyModule_Check(m)) {
     PyErr_SetString(PyExc_TypeError,
 		    "PyModule_AddObject() needs module as first arg");
-    return -1;
+    return SWIG_ERROR;
   }
   if (!o) {
     PyErr_SetString(PyExc_TypeError,
 		    "PyModule_AddObject() needs non-NULL value");
-    return -1;
+    return SWIG_ERROR;
   }
   
   dict = PyModule_GetDict(m);
@@ -1403,4424 +2273,4557 @@ PyModule_AddObject(PyObject *m, char *na
     /* Internal error -- modules must have a dict! */
     PyErr_Format(PyExc_SystemError, "module '%s' has no __dict__",
 		 PyModule_GetName(m));
-    return -1;
+    return SWIG_ERROR;
   }
   if (PyDict_SetItemString(dict, name, o))
-    return -1;
+    return SWIG_ERROR;
   Py_DECREF(o);
-  return 0;
+  return SWIG_OK;
 }
 #endif
 
 SWIGRUNTIME void
+SWIG_Python_DestroyModule(void *vptr)
+{
+  swig_module_info *swig_module = (swig_module_info *) vptr;
+  swig_type_info **types = swig_module->types;
+  size_t i;
+  for (i =0; i < swig_module->size; ++i) {
+    swig_type_info *ty = types[i];
+    if (ty->owndata) {
+      PySwigClientData *data = (PySwigClientData *) ty->clientdata;
+      if (data) PySwigClientData_Del(data);
+    }
+  }
+  Py_DECREF(SWIG_This());
+}
+
+SWIGRUNTIME void
 SWIG_Python_SetModule(swig_module_info *swig_module) {
   static PyMethodDef swig_empty_runtime_method_table[] = { {NULL, NULL, 0, NULL} };/* Sentinel */
 
   PyObject *module = Py_InitModule((char*)"swig_runtime_data" SWIG_RUNTIME_VERSION,
 				   swig_empty_runtime_method_table);
-  PyObject *pointer = PyCObject_FromVoidPtr((void *) swig_module, NULL);
+  PyObject *pointer = PyCObject_FromVoidPtr((void *) swig_module, SWIG_Python_DestroyModule);
   if (pointer && module) {
     PyModule_AddObject(module, (char*)"type_pointer" SWIG_TYPE_TABLE_NAME, pointer);
+  } else {
+    Py_XDECREF(pointer);
   }
 }
 
-#ifdef __cplusplus
+/* The python cached type query */
+SWIGRUNTIME PyObject *
+SWIG_Python_TypeCache() {
+  static PyObject *SWIG_STATIC_POINTER(cache) = PyDict_New();
+  return cache;
 }
-#endif
-
-
-/* -------- TYPES TABLE (BEGIN) -------- */
-
-#define SWIGTYPE_p_char swig_types[0]
-#define SWIGTYPE_p_form_ops_t swig_types[1]
-#define SWIGTYPE_p_int swig_types[2]
-#define SWIGTYPE_p_unsigned_char swig_types[3]
-#define SWIGTYPE_p_unsigned_int swig_types[4]
-#define SWIGTYPE_p_unsigned_long swig_types[5]
-#define SWIGTYPE_p_wxANIHandler swig_types[6]
-#define SWIGTYPE_p_wxAcceleratorTable swig_types[7]
-#define SWIGTYPE_p_wxActivateEvent swig_types[8]
-#define SWIGTYPE_p_wxBMPHandler swig_types[9]
-#define SWIGTYPE_p_wxBoxSizer swig_types[10]
-#define SWIGTYPE_p_wxBusyInfo swig_types[11]
-#define SWIGTYPE_p_wxCURHandler swig_types[12]
-#define SWIGTYPE_p_wxCalculateLayoutEvent swig_types[13]
-#define SWIGTYPE_p_wxChildFocusEvent swig_types[14]
-#define SWIGTYPE_p_wxClipboard swig_types[15]
-#define SWIGTYPE_p_wxCloseEvent swig_types[16]
-#define SWIGTYPE_p_wxColourData swig_types[17]
-#define SWIGTYPE_p_wxColourDialog swig_types[18]
-#define SWIGTYPE_p_wxCommandEvent swig_types[19]
-#define SWIGTYPE_p_wxContextMenuEvent swig_types[20]
-#define SWIGTYPE_p_wxControl swig_types[21]
-#define SWIGTYPE_p_wxControlWithItems swig_types[22]
-#define SWIGTYPE_p_wxDateEvent swig_types[23]
-#define SWIGTYPE_p_wxDialog swig_types[24]
-#define SWIGTYPE_p_wxDirDialog swig_types[25]
-#define SWIGTYPE_p_wxDisplayChangedEvent swig_types[26]
-#define SWIGTYPE_p_wxDropFilesEvent swig_types[27]
-#define SWIGTYPE_p_wxDuplexMode swig_types[28]
-#define SWIGTYPE_p_wxEraseEvent swig_types[29]
-#define SWIGTYPE_p_wxEvent swig_types[30]
-#define SWIGTYPE_p_wxEvtHandler swig_types[31]
-#define SWIGTYPE_p_wxFSFile swig_types[32]
-#define SWIGTYPE_p_wxFileDialog swig_types[33]
-#define SWIGTYPE_p_wxFileHistory swig_types[34]
-#define SWIGTYPE_p_wxFileSystem swig_types[35]
-#define SWIGTYPE_p_wxFindDialogEvent swig_types[36]
-#define SWIGTYPE_p_wxFindReplaceData swig_types[37]
-#define SWIGTYPE_p_wxFindReplaceDialog swig_types[38]
-#define SWIGTYPE_p_wxFlexGridSizer swig_types[39]
-#define SWIGTYPE_p_wxFocusEvent swig_types[40]
-#define SWIGTYPE_p_wxFontData swig_types[41]
-#define SWIGTYPE_p_wxFontDialog swig_types[42]
-#define SWIGTYPE_p_wxFrame swig_types[43]
-#define SWIGTYPE_p_wxGBSizerItem swig_types[44]
-#define SWIGTYPE_p_wxGIFHandler swig_types[45]
-#define SWIGTYPE_p_wxGridBagSizer swig_types[46]
-#define SWIGTYPE_p_wxGridSizer swig_types[47]
-#define SWIGTYPE_p_wxICOHandler swig_types[48]
-#define SWIGTYPE_p_wxIconizeEvent swig_types[49]
-#define SWIGTYPE_p_wxIdleEvent swig_types[50]
-#define SWIGTYPE_p_wxImage swig_types[51]
-#define SWIGTYPE_p_wxImageHandler swig_types[52]
-#define SWIGTYPE_p_wxIndividualLayoutConstraint swig_types[53]
-#define SWIGTYPE_p_wxInitDialogEvent swig_types[54]
-#define SWIGTYPE_p_wxJPEGHandler swig_types[55]
-#define SWIGTYPE_p_wxJoystickEvent swig_types[56]
-#define SWIGTYPE_p_wxKeyEvent swig_types[57]
-#define SWIGTYPE_p_wxLayoutAlgorithm swig_types[58]
-#define SWIGTYPE_p_wxLayoutConstraints swig_types[59]
-#define SWIGTYPE_p_wxMDIChildFrame swig_types[60]
-#define SWIGTYPE_p_wxMDIClientWindow swig_types[61]
-#define SWIGTYPE_p_wxMDIParentFrame swig_types[62]
-#define SWIGTYPE_p_wxMaximizeEvent swig_types[63]
-#define SWIGTYPE_p_wxMenu swig_types[64]
-#define SWIGTYPE_p_wxMenuBar swig_types[65]
-#define SWIGTYPE_p_wxMenuEvent swig_types[66]
-#define SWIGTYPE_p_wxMenuItem swig_types[67]
-#define SWIGTYPE_p_wxMessageDialog swig_types[68]
-#define SWIGTYPE_p_wxMiniFrame swig_types[69]
-#define SWIGTYPE_p_wxMouseCaptureChangedEvent swig_types[70]
-#define SWIGTYPE_p_wxMouseEvent swig_types[71]
-#define SWIGTYPE_p_wxMoveEvent swig_types[72]
-#define SWIGTYPE_p_wxMozillaBeforeLoadEvent swig_types[73]
-#define SWIGTYPE_p_wxMozillaBrowser swig_types[74]
-#define SWIGTYPE_p_wxMozillaLinkChangedEvent swig_types[75]
-#define SWIGTYPE_p_wxMozillaLoadCompleteEvent swig_types[76]
-#define SWIGTYPE_p_wxMozillaProgressEvent swig_types[77]
-#define SWIGTYPE_p_wxMozillaRightClickEvent swig_types[78]
-#define SWIGTYPE_p_wxMozillaSecurityChangedEvent swig_types[79]
-#define SWIGTYPE_p_wxMozillaSettings swig_types[80]
-#define SWIGTYPE_p_wxMozillaStateChangedEvent swig_types[81]
-#define SWIGTYPE_p_wxMozillaStatusChangedEvent swig_types[82]
-#define SWIGTYPE_p_wxMozillaTitleChangedEvent swig_types[83]
-#define SWIGTYPE_p_wxMozillaWindow swig_types[84]
-#define SWIGTYPE_p_wxMultiChoiceDialog swig_types[85]
-#define SWIGTYPE_p_wxNavigationKeyEvent swig_types[86]
-#define SWIGTYPE_p_wxNcPaintEvent swig_types[87]
-#define SWIGTYPE_p_wxNotifyEvent swig_types[88]
-#define SWIGTYPE_p_wxObject swig_types[89]
-#define SWIGTYPE_p_wxPCXHandler swig_types[90]
-#define SWIGTYPE_p_wxPNGHandler swig_types[91]
-#define SWIGTYPE_p_wxPNMHandler swig_types[92]
-#define SWIGTYPE_p_wxPageSetupDialog swig_types[93]
-#define SWIGTYPE_p_wxPageSetupDialogData swig_types[94]
-#define SWIGTYPE_p_wxPaintEvent swig_types[95]
-#define SWIGTYPE_p_wxPaletteChangedEvent swig_types[96]
-#define SWIGTYPE_p_wxPanel swig_types[97]
-#define SWIGTYPE_p_wxPaperSize swig_types[98]
-#define SWIGTYPE_p_wxPasswordEntryDialog swig_types[99]
-#define SWIGTYPE_p_wxPopupWindow swig_types[100]
-#define SWIGTYPE_p_wxPreviewCanvas swig_types[101]
-#define SWIGTYPE_p_wxPreviewControlBar swig_types[102]
-#define SWIGTYPE_p_wxPreviewFrame swig_types[103]
-#define SWIGTYPE_p_wxPrintData swig_types[104]
-#define SWIGTYPE_p_wxPrintDialog swig_types[105]
-#define SWIGTYPE_p_wxPrintDialogData swig_types[106]
-#define SWIGTYPE_p_wxPrintPreview swig_types[107]
-#define SWIGTYPE_p_wxPrinter swig_types[108]
-#define SWIGTYPE_p_wxProcessEvent swig_types[109]
-#define SWIGTYPE_p_wxProgressDialog swig_types[110]
-#define SWIGTYPE_p_wxPyApp swig_types[111]
-#define SWIGTYPE_p_wxPyCommandEvent swig_types[112]
-#define SWIGTYPE_p_wxPyEvent swig_types[113]
-#define SWIGTYPE_p_wxPyHtmlListBox swig_types[114]
-#define SWIGTYPE_p_wxPyImageHandler swig_types[115]
-#define SWIGTYPE_p_wxPyPanel swig_types[116]
-#define SWIGTYPE_p_wxPyPopupTransientWindow swig_types[117]
-#define SWIGTYPE_p_wxPyPreviewControlBar swig_types[118]
-#define SWIGTYPE_p_wxPyPreviewFrame swig_types[119]
-#define SWIGTYPE_p_wxPyPrintPreview swig_types[120]
-#define SWIGTYPE_p_wxPyPrintout swig_types[121]
-#define SWIGTYPE_p_wxPyProcess swig_types[122]
-#define SWIGTYPE_p_wxPyScrolledWindow swig_types[123]
-#define SWIGTYPE_p_wxPySizer swig_types[124]
-#define SWIGTYPE_p_wxPyTaskBarIcon swig_types[125]
-#define SWIGTYPE_p_wxPyTimer swig_types[126]
-#define SWIGTYPE_p_wxPyVListBox swig_types[127]
-#define SWIGTYPE_p_wxPyVScrolledWindow swig_types[128]
-#define SWIGTYPE_p_wxPyValidator swig_types[129]
-#define SWIGTYPE_p_wxPyWindow swig_types[130]
-#define SWIGTYPE_p_wxQueryLayoutInfoEvent swig_types[131]
-#define SWIGTYPE_p_wxQueryNewPaletteEvent swig_types[132]
-#define SWIGTYPE_p_wxSashEvent swig_types[133]
-#define SWIGTYPE_p_wxSashLayoutWindow swig_types[134]
-#define SWIGTYPE_p_wxSashWindow swig_types[135]
-#define SWIGTYPE_p_wxScrollEvent swig_types[136]
-#define SWIGTYPE_p_wxScrollWinEvent swig_types[137]
-#define SWIGTYPE_p_wxScrolledWindow swig_types[138]
-#define SWIGTYPE_p_wxSetCursorEvent swig_types[139]
-#define SWIGTYPE_p_wxShowEvent swig_types[140]
-#define SWIGTYPE_p_wxSingleChoiceDialog swig_types[141]
-#define SWIGTYPE_p_wxSizeEvent swig_types[142]
-#define SWIGTYPE_p_wxSizer swig_types[143]
-#define SWIGTYPE_p_wxSizerItem swig_types[144]
-#define SWIGTYPE_p_wxSplashScreen swig_types[145]
-#define SWIGTYPE_p_wxSplashScreenWindow swig_types[146]
-#define SWIGTYPE_p_wxSplitterEvent swig_types[147]
-#define SWIGTYPE_p_wxSplitterWindow swig_types[148]
-#define SWIGTYPE_p_wxStaticBoxSizer swig_types[149]
-#define SWIGTYPE_p_wxStatusBar swig_types[150]
-#define SWIGTYPE_p_wxStdDialogButtonSizer swig_types[151]
-#define SWIGTYPE_p_wxSysColourChangedEvent swig_types[152]
-#define SWIGTYPE_p_wxSystemOptions swig_types[153]
-#define SWIGTYPE_p_wxTIFFHandler swig_types[154]
-#define SWIGTYPE_p_wxTaskBarIconEvent swig_types[155]
-#define SWIGTYPE_p_wxTextEntryDialog swig_types[156]
-#define SWIGTYPE_p_wxTimerEvent swig_types[157]
-#define SWIGTYPE_p_wxTipWindow swig_types[158]
-#define SWIGTYPE_p_wxToolTip swig_types[159]
-#define SWIGTYPE_p_wxTopLevelWindow swig_types[160]
-#define SWIGTYPE_p_wxUpdateUIEvent swig_types[161]
-#define SWIGTYPE_p_wxValidator swig_types[162]
-#define SWIGTYPE_p_wxWindow swig_types[163]
-#define SWIGTYPE_p_wxWindowCreateEvent swig_types[164]
-#define SWIGTYPE_p_wxWindowDestroyEvent swig_types[165]
-#define SWIGTYPE_p_wxXPMHandler swig_types[166]
-#define SWIGTYPE_ptrdiff_t swig_types[167]
-#define SWIGTYPE_std__ptrdiff_t swig_types[168]
-#define SWIGTYPE_unsigned_int swig_types[169]
-static swig_type_info *swig_types[171];
-static swig_module_info swig_module = {swig_types, 170, 0, 0, 0, 0};
-#define SWIG_TypeQuery(name) SWIG_TypeQueryModule(&swig_module, &swig_module, name)
-#define SWIG_MangledTypeQuery(name) SWIG_MangledTypeQueryModule(&swig_module, &swig_module, name)
 
-/* -------- TYPES TABLE (END) -------- */
-
-
-/*-----------------------------------------------
-              @(target):= _mozilla.so
-  ------------------------------------------------*/
-#define SWIG_init    init_mozilla
-
-#define SWIG_name    "_mozilla"
-
-#include "wx/wxPython/wxPython.h"
-#include "wx/wxPython/pyclasses.h"
-#include "wx/wxPython/pyistream.h"
-
-#ifdef __WXMAC__  // avoid a bug in Carbon headers
-#define scalb scalbn
-#endif
-
-#include "wxMozillaBrowser.h"
-#include "wxMozillaWindow.h"
-#include "wxMozilla.h"
+SWIGRUNTIME swig_type_info *
+SWIG_Python_TypeQuery(const char *type)
+{
+  PyObject *cache = SWIG_Python_TypeCache();
+  PyObject *key = PyString_FromString(type); 
+  PyObject *obj = PyDict_GetItem(cache, key);
+  swig_type_info *descriptor;
+  if (obj) {
+    descriptor = (swig_type_info *) PyCObject_AsVoidPtr(obj);
+  } else {
+    swig_module_info *swig_module = SWIG_Python_GetModule();
+    descriptor = SWIG_TypeQueryModule(swig_module, swig_module, type);
+    if (descriptor) {
+      obj = PyCObject_FromVoidPtr(descriptor, NULL);
+      PyDict_SetItem(cache, key, obj);
+      Py_DECREF(obj);
+    }
+  }
+  Py_DECREF(key);
+  return descriptor;
+}
 
+/* 
+   For backward compatibility only
+*/
+#define SWIG_POINTER_EXCEPTION  0
+#define SWIG_arg_fail(arg)      SWIG_Python_ArgFail(arg)
+#define SWIG_MustGetPtr(p, type, argnum, flags)  SWIG_Python_MustGetPtr(p, type, argnum, flags)
 
-    // Put some wx default wxChar* values into wxStrings.
-    DECLARE_DEF_STRING(PanelNameStr);
-
-
-  /*@/usr/local/swig-1.3.27/share/swig/1.3.27/python/pymacros.swg,72,SWIG_define@*/
-#define SWIG_From_int PyInt_FromLong
-/*@@*/
-
-
-#include <limits.h>
-
-
-SWIGINTERN int
-  SWIG_CheckLongInRange(long value, long min_value, long max_value,
-			const char *errmsg)
+SWIGRUNTIME int
+SWIG_Python_AddErrMesg(const char* mesg, int infront)
 {
-  if (value < min_value) {
-    if (errmsg) {
-      PyErr_Format(PyExc_OverflowError, 
-		   "value %ld is less than '%s' minimum %ld", 
-		   value, errmsg, min_value);
-    }
-    return 0;    
-  } else if (value > max_value) {
-    if (errmsg) {
-      PyErr_Format(PyExc_OverflowError,
-		   "value %ld is greater than '%s' maximum %ld", 
-		   value, errmsg, max_value);
+  if (PyErr_Occurred()) {
+    PyObject *type = 0;
+    PyObject *value = 0;
+    PyObject *traceback = 0;
+    PyErr_Fetch(&type, &value, &traceback);
+    if (value) {
+      PyObject *old_str = PyObject_Str(value);
+      Py_XINCREF(type);
+      PyErr_Clear();
+      if (infront) {
+	PyErr_Format(type, "%s %s", mesg, PyString_AsString(old_str));
+      } else {
+	PyErr_Format(type, "%s %s", PyString_AsString(old_str), mesg);
+      }
+      Py_DECREF(old_str);
     }
+    return 1;
+  } else {
     return 0;
   }
-  return 1;
 }
-
-
-SWIGINTERN int
-SWIG_AsVal_long(PyObject* obj, long* val)
+  
+SWIGRUNTIME int
+SWIG_Python_ArgFail(int argnum)
 {
-    if (PyNumber_Check(obj)) {
-        if (val) *val = PyInt_AsLong(obj);
-        return 1;
-    }
-    else {
-        SWIG_type_error("number", obj);
-    }
-    return 0;
-}
-
-
-#if INT_MAX != LONG_MAX
-SWIGINTERN int
-  SWIG_AsVal_int(PyObject *obj, int *val)
-{ 
-  const char* errmsg = val ? "int" : (char*)0;
-  long v;
-  if (SWIG_AsVal_long(obj, &v)) {
-    if (SWIG_CheckLongInRange(v, INT_MIN,INT_MAX, errmsg)) {
-      if (val) *val = static_cast<int >(v);
-      return 1;
-    } else {
-      return 0;
-    }
+  if (PyErr_Occurred()) {
+    /* add information about failing argument */
+    char mesg[256];
+    PyOS_snprintf(mesg, sizeof(mesg), "argument number %d:", argnum);
+    return SWIG_Python_AddErrMesg(mesg, 1);
   } else {
-    PyErr_Clear();
-  }
-  if (val) {
-    SWIG_type_error(errmsg, obj);
+    return 0;
   }
-  return 0;    
-}
-#else
-SWIGINTERNINLINE int
-  SWIG_AsVal_int(PyObject *obj, int *val)
-{
-  return SWIG_AsVal_long(obj,(long*)val);
 }
-#endif
-
 
-SWIGINTERNINLINE int
-SWIG_As_int(PyObject* obj)
+SWIGRUNTIMEINLINE const char *
+PySwigObject_GetDesc(PyObject *self)
 {
-  int v;
-  if (!SWIG_AsVal_int(obj, &v)) {
-    /*
-      this is needed to make valgrind/purify happier. 
-     */
-    memset((void*)&v, 0, sizeof(int));
-  }
-  return v;
+  PySwigObject *v = (PySwigObject *)self;
+  swig_type_info *ty = v ? v->ty : 0;
+  return ty ? ty->str : (char*)"";
 }
 
-
-SWIGINTERNINLINE long
-SWIG_As_long(PyObject* obj)
+SWIGRUNTIME void
+SWIG_Python_TypeError(const char *type, PyObject *obj)
 {
-  long v;
-  if (!SWIG_AsVal_long(obj, &v)) {
-    /*
-      this is needed to make valgrind/purify happier. 
-     */
-    memset((void*)&v, 0, sizeof(long));
+  if (type) {
+#if defined(SWIG_COBJECT_TYPES)
+    if (obj && PySwigObject_Check(obj)) {
+      const char *otype = (const char *) PySwigObject_GetDesc(obj);
+      if (otype) {
+	PyErr_Format(PyExc_TypeError, "a '%s' is expected, 'PySwigObject(%s)' is received",
+		     type, otype);
+	return;
+      }
+    } else 
+#endif      
+    {
+      const char *otype = (obj ? obj->ob_type->tp_name : 0); 
+      if (otype) {
+	PyObject *str = PyObject_Str(obj);
+	const char *cstr = str ? PyString_AsString(str) : 0;
+	if (cstr) {
+	  PyErr_Format(PyExc_TypeError, "a '%s' is expected, '%s(%s)' is received",
+		       type, otype, cstr);
+	} else {
+	  PyErr_Format(PyExc_TypeError, "a '%s' is expected, '%s' is received",
+		       type, otype);
+	}
+	Py_XDECREF(str);
+	return;
+      }
+    }   
+    PyErr_Format(PyExc_TypeError, "a '%s' is expected", type);
+  } else {
+    PyErr_Format(PyExc_TypeError, "unexpected type is received");
   }
-  return v;
-}
-
-  
-SWIGINTERNINLINE int
-SWIG_Check_int(PyObject* obj)
-{
-  return SWIG_AsVal_int(obj, (int*)0);
-}
-
-  
-SWIGINTERNINLINE int
-SWIG_Check_long(PyObject* obj)
-{
-  return SWIG_AsVal_long(obj, (long*)0);
 }
 
 
-SWIGINTERN int
-  SWIG_AsVal_bool(PyObject *obj, bool *val)
-{
-  if (obj == Py_True) {
-    if (val) *val = true;
-    return 1;
-  }
-  if (obj == Py_False) {
-    if (val) *val = false;
-    return 1;
-  }
-  int res = 0;
-  if (SWIG_AsVal_int(obj, &res)) {    
-    if (val) *val = res ? true : false;
-    return 1;
-  } else {
+/* Convert a pointer value, signal an exception on a type mismatch */
+SWIGRUNTIME void *
+SWIG_Python_MustGetPtr(PyObject *obj, swig_type_info *ty, int argnum, int flags) {
+  void *result;
+  if (SWIG_Python_ConvertPtr(obj, &result, ty, flags) == -1) {
     PyErr_Clear();
-  }  
-  if (val) {
-    SWIG_type_error("bool", obj);
+    if (flags & SWIG_POINTER_EXCEPTION) {
+      SWIG_Python_TypeError(SWIG_TypePrettyName(ty), obj);
+      SWIG_Python_ArgFail(argnum);
+    }
   }
-  return 0;
+  return result;
 }
 
 
-SWIGINTERNINLINE bool
-SWIG_As_bool(PyObject* obj)
-{
-  bool v;
-  if (!SWIG_AsVal_bool(obj, &v)) {
-    /*
-      this is needed to make valgrind/purify happier. 
-     */
-    memset((void*)&v, 0, sizeof(bool));
-  }
-  return v;
-}
-
-  
-SWIGINTERNINLINE int
-SWIG_Check_bool(PyObject* obj)
-{
-  return SWIG_AsVal_bool(obj, (bool*)0);
+#ifdef __cplusplus
+#if 0
+{ /* cc-mode */
+#endif
 }
+#endif
 
 
-#include <float.h>
-SWIGINTERN int
-  SWIG_CheckDoubleInRange(double value, double min_value, 
-			  double max_value, const char* errmsg)
-{
-  if (value < min_value) {
-    if (errmsg) {
-      PyErr_Format(PyExc_OverflowError, 
-		   "value %g is less than %s minimum %g", 
-		   value, errmsg, min_value);
-    }
-    return 0;
-  } else if (value > max_value) {
-    if (errmsg) {
-      PyErr_Format(PyExc_OverflowError, 
-		   "value %g is greater than %s maximum %g", 
-		   value, errmsg, max_value);
-    }
-    return 0;
-  }
-  return 1;
-}
 
+#define SWIG_exception_fail(code, msg) do { SWIG_Error(code, msg); SWIG_fail; } while(0) 
 
-SWIGINTERN int
-SWIG_AsVal_double(PyObject *obj, double* val)
-{
-    if (PyNumber_Check(obj)) {
-        if (val) *val = PyFloat_AsDouble(obj);
-        return 1;
-    }
-    else {
-        SWIG_type_error("number", obj);
-    }
-    return 0;
-}
+#define SWIG_contract_assert(expr, msg) if (!(expr)) { SWIG_Error(SWIG_RuntimeError, msg); SWIG_fail; } else 
 
 
-SWIGINTERN int
-  SWIG_AsVal_float(PyObject *obj, float *val)
-{
-  const char* errmsg = val ? "float" : (char*)0;
-  double v;
-  if (SWIG_AsVal_double(obj, &v)) {
-    if (SWIG_CheckDoubleInRange(v, -FLT_MAX, FLT_MAX, errmsg)) {
-      if (val) *val = static_cast<float >(v);
-      return 1;
-    } else {
-      return 0;
-    }
-  } else {
-    PyErr_Clear();
-  }
-  if (val) {
-    SWIG_type_error(errmsg, obj);
-  }
-  return 0;
-}
 
+/* -------- TYPES TABLE (BEGIN) -------- */
 
-SWIGINTERNINLINE float
-SWIG_As_float(PyObject* obj)
-{
-  float v;
-  if (!SWIG_AsVal_float(obj, &v)) {
-    /*
-      this is needed to make valgrind/purify happier. 
-     */
-    memset((void*)&v, 0, sizeof(float));
-  }
-  return v;
-}
+#define SWIGTYPE_p_char swig_types[0]
+#define SWIGTYPE_p_form_ops_t swig_types[1]
+#define SWIGTYPE_p_int swig_types[2]
+#define SWIGTYPE_p_unsigned_char swig_types[3]
+#define SWIGTYPE_p_unsigned_int swig_types[4]
+#define SWIGTYPE_p_unsigned_long swig_types[5]
+#define SWIGTYPE_p_wxANIHandler swig_types[6]
+#define SWIGTYPE_p_wxAcceleratorTable swig_types[7]
+#define SWIGTYPE_p_wxActivateEvent swig_types[8]
+#define SWIGTYPE_p_wxBMPHandler swig_types[9]
+#define SWIGTYPE_p_wxBoxSizer swig_types[10]
+#define SWIGTYPE_p_wxBusyInfo swig_types[11]
+#define SWIGTYPE_p_wxCURHandler swig_types[12]
+#define SWIGTYPE_p_wxCalculateLayoutEvent swig_types[13]
+#define SWIGTYPE_p_wxChildFocusEvent swig_types[14]
+#define SWIGTYPE_p_wxClipboard swig_types[15]
+#define SWIGTYPE_p_wxClipboardTextEvent swig_types[16]
+#define SWIGTYPE_p_wxCloseEvent swig_types[17]
+#define SWIGTYPE_p_wxColourData swig_types[18]
+#define SWIGTYPE_p_wxColourDialog swig_types[19]
+#define SWIGTYPE_p_wxCommandEvent swig_types[20]
+#define SWIGTYPE_p_wxContextMenuEvent swig_types[21]
+#define SWIGTYPE_p_wxControl swig_types[22]
+#define SWIGTYPE_p_wxControlWithItems swig_types[23]
+#define SWIGTYPE_p_wxDateEvent swig_types[24]
+#define SWIGTYPE_p_wxDialog swig_types[25]
+#define SWIGTYPE_p_wxDirDialog swig_types[26]
+#define SWIGTYPE_p_wxDisplayChangedEvent swig_types[27]
+#define SWIGTYPE_p_wxDropFilesEvent swig_types[28]
+#define SWIGTYPE_p_wxDuplexMode swig_types[29]
+#define SWIGTYPE_p_wxEraseEvent swig_types[30]
+#define SWIGTYPE_p_wxEvent swig_types[31]
+#define SWIGTYPE_p_wxEvtHandler swig_types[32]
+#define SWIGTYPE_p_wxFSFile swig_types[33]
+#define SWIGTYPE_p_wxFileDialog swig_types[34]
+#define SWIGTYPE_p_wxFileHistory swig_types[35]
+#define SWIGTYPE_p_wxFileSystem swig_types[36]
+#define SWIGTYPE_p_wxFindDialogEvent swig_types[37]
+#define SWIGTYPE_p_wxFindReplaceData swig_types[38]
+#define SWIGTYPE_p_wxFindReplaceDialog swig_types[39]
+#define SWIGTYPE_p_wxFlexGridSizer swig_types[40]
+#define SWIGTYPE_p_wxFocusEvent swig_types[41]
+#define SWIGTYPE_p_wxFontData swig_types[42]
+#define SWIGTYPE_p_wxFontDialog swig_types[43]
+#define SWIGTYPE_p_wxFrame swig_types[44]
+#define SWIGTYPE_p_wxGBSizerItem swig_types[45]
+#define SWIGTYPE_p_wxGIFHandler swig_types[46]
+#define SWIGTYPE_p_wxGridBagSizer swig_types[47]
+#define SWIGTYPE_p_wxGridSizer swig_types[48]
+#define SWIGTYPE_p_wxICOHandler swig_types[49]
+#define SWIGTYPE_p_wxIconizeEvent swig_types[50]
+#define SWIGTYPE_p_wxIdleEvent swig_types[51]
+#define SWIGTYPE_p_wxImage swig_types[52]
+#define SWIGTYPE_p_wxImageHandler swig_types[53]
+#define SWIGTYPE_p_wxIndividualLayoutConstraint swig_types[54]
+#define SWIGTYPE_p_wxInitDialogEvent swig_types[55]
+#define SWIGTYPE_p_wxJPEGHandler swig_types[56]
+#define SWIGTYPE_p_wxJoystickEvent swig_types[57]
+#define SWIGTYPE_p_wxKeyEvent swig_types[58]
+#define SWIGTYPE_p_wxLayoutAlgorithm swig_types[59]
+#define SWIGTYPE_p_wxLayoutConstraints swig_types[60]
+#define SWIGTYPE_p_wxMDIChildFrame swig_types[61]
+#define SWIGTYPE_p_wxMDIClientWindow swig_types[62]
+#define SWIGTYPE_p_wxMDIParentFrame swig_types[63]
+#define SWIGTYPE_p_wxMaximizeEvent swig_types[64]
+#define SWIGTYPE_p_wxMenu swig_types[65]
+#define SWIGTYPE_p_wxMenuBar swig_types[66]
+#define SWIGTYPE_p_wxMenuEvent swig_types[67]
+#define SWIGTYPE_p_wxMenuItem swig_types[68]
+#define SWIGTYPE_p_wxMessageDialog swig_types[69]
+#define SWIGTYPE_p_wxMiniFrame swig_types[70]
+#define SWIGTYPE_p_wxMouseCaptureChangedEvent swig_types[71]
+#define SWIGTYPE_p_wxMouseCaptureLostEvent swig_types[72]
+#define SWIGTYPE_p_wxMouseEvent swig_types[73]
+#define SWIGTYPE_p_wxMoveEvent swig_types[74]
+#define SWIGTYPE_p_wxMozillaBeforeLoadEvent swig_types[75]
+#define SWIGTYPE_p_wxMozillaBrowser swig_types[76]
+#define SWIGTYPE_p_wxMozillaLinkChangedEvent swig_types[77]
+#define SWIGTYPE_p_wxMozillaLoadCompleteEvent swig_types[78]
+#define SWIGTYPE_p_wxMozillaProgressEvent swig_types[79]
+#define SWIGTYPE_p_wxMozillaRightClickEvent swig_types[80]
+#define SWIGTYPE_p_wxMozillaSecurityChangedEvent swig_types[81]
+#define SWIGTYPE_p_wxMozillaSettings swig_types[82]
+#define SWIGTYPE_p_wxMozillaStateChangedEvent swig_types[83]
+#define SWIGTYPE_p_wxMozillaStatusChangedEvent swig_types[84]
+#define SWIGTYPE_p_wxMozillaTitleChangedEvent swig_types[85]
+#define SWIGTYPE_p_wxMozillaWindow swig_types[86]
+#define SWIGTYPE_p_wxMultiChoiceDialog swig_types[87]
+#define SWIGTYPE_p_wxNavigationKeyEvent swig_types[88]
+#define SWIGTYPE_p_wxNcPaintEvent swig_types[89]
+#define SWIGTYPE_p_wxNotifyEvent swig_types[90]
+#define SWIGTYPE_p_wxNumberEntryDialog swig_types[91]
+#define SWIGTYPE_p_wxObject swig_types[92]
+#define SWIGTYPE_p_wxPCXHandler swig_types[93]
+#define SWIGTYPE_p_wxPNGHandler swig_types[94]
+#define SWIGTYPE_p_wxPNMHandler swig_types[95]
+#define SWIGTYPE_p_wxPageSetupDialog swig_types[96]
+#define SWIGTYPE_p_wxPageSetupDialogData swig_types[97]
+#define SWIGTYPE_p_wxPaintEvent swig_types[98]
+#define SWIGTYPE_p_wxPaletteChangedEvent swig_types[99]
+#define SWIGTYPE_p_wxPanel swig_types[100]
+#define SWIGTYPE_p_wxPaperSize swig_types[101]
+#define SWIGTYPE_p_wxPasswordEntryDialog swig_types[102]
+#define SWIGTYPE_p_wxPopupWindow swig_types[103]
+#define SWIGTYPE_p_wxPowerEvent swig_types[104]
+#define SWIGTYPE_p_wxPreviewCanvas swig_types[105]
+#define SWIGTYPE_p_wxPreviewControlBar swig_types[106]
+#define SWIGTYPE_p_wxPreviewFrame swig_types[107]
+#define SWIGTYPE_p_wxPrintData swig_types[108]
+#define SWIGTYPE_p_wxPrintDialog swig_types[109]
+#define SWIGTYPE_p_wxPrintDialogData swig_types[110]
+#define SWIGTYPE_p_wxPrintPreview swig_types[111]
+#define SWIGTYPE_p_wxPrinter swig_types[112]
+#define SWIGTYPE_p_wxProcessEvent swig_types[113]
+#define SWIGTYPE_p_wxProgressDialog swig_types[114]
+#define SWIGTYPE_p_wxPyApp swig_types[115]
+#define SWIGTYPE_p_wxPyCommandEvent swig_types[116]
+#define SWIGTYPE_p_wxPyEvent swig_types[117]
+#define SWIGTYPE_p_wxPyHtmlListBox swig_types[118]
+#define SWIGTYPE_p_wxPyImageHandler swig_types[119]
+#define SWIGTYPE_p_wxPyPanel swig_types[120]
+#define SWIGTYPE_p_wxPyPopupTransientWindow swig_types[121]
+#define SWIGTYPE_p_wxPyPreviewControlBar swig_types[122]
+#define SWIGTYPE_p_wxPyPreviewFrame swig_types[123]
+#define SWIGTYPE_p_wxPyPrintPreview swig_types[124]
+#define SWIGTYPE_p_wxPyPrintout swig_types[125]
+#define SWIGTYPE_p_wxPyProcess swig_types[126]
+#define SWIGTYPE_p_wxPyScrolledWindow swig_types[127]
+#define SWIGTYPE_p_wxPySizer swig_types[128]
+#define SWIGTYPE_p_wxPyTaskBarIcon swig_types[129]
+#define SWIGTYPE_p_wxPyTimer swig_types[130]
+#define SWIGTYPE_p_wxPyVListBox swig_types[131]
+#define SWIGTYPE_p_wxPyVScrolledWindow swig_types[132]
+#define SWIGTYPE_p_wxPyValidator swig_types[133]
+#define SWIGTYPE_p_wxPyWindow swig_types[134]
+#define SWIGTYPE_p_wxQueryLayoutInfoEvent swig_types[135]
+#define SWIGTYPE_p_wxQueryNewPaletteEvent swig_types[136]
+#define SWIGTYPE_p_wxSashEvent swig_types[137]
+#define SWIGTYPE_p_wxSashLayoutWindow swig_types[138]
+#define SWIGTYPE_p_wxSashWindow swig_types[139]
+#define SWIGTYPE_p_wxScrollEvent swig_types[140]
+#define SWIGTYPE_p_wxScrollWinEvent swig_types[141]
+#define SWIGTYPE_p_wxScrolledWindow swig_types[142]
+#define SWIGTYPE_p_wxSetCursorEvent swig_types[143]
+#define SWIGTYPE_p_wxShowEvent swig_types[144]
+#define SWIGTYPE_p_wxSimpleHtmlListBox swig_types[145]
+#define SWIGTYPE_p_wxSingleChoiceDialog swig_types[146]
+#define SWIGTYPE_p_wxSizeEvent swig_types[147]
+#define SWIGTYPE_p_wxSizer swig_types[148]
+#define SWIGTYPE_p_wxSizerItem swig_types[149]
+#define SWIGTYPE_p_wxSplashScreen swig_types[150]
+#define SWIGTYPE_p_wxSplashScreenWindow swig_types[151]
+#define SWIGTYPE_p_wxSplitterEvent swig_types[152]
+#define SWIGTYPE_p_wxSplitterWindow swig_types[153]
+#define SWIGTYPE_p_wxStaticBoxSizer swig_types[154]
+#define SWIGTYPE_p_wxStatusBar swig_types[155]
+#define SWIGTYPE_p_wxStdDialogButtonSizer swig_types[156]
+#define SWIGTYPE_p_wxSysColourChangedEvent swig_types[157]
+#define SWIGTYPE_p_wxSystemOptions swig_types[158]
+#define SWIGTYPE_p_wxTGAHandler swig_types[159]
+#define SWIGTYPE_p_wxTIFFHandler swig_types[160]
+#define SWIGTYPE_p_wxTaskBarIconEvent swig_types[161]
+#define SWIGTYPE_p_wxTextEntryDialog swig_types[162]
+#define SWIGTYPE_p_wxTimerEvent swig_types[163]
+#define SWIGTYPE_p_wxTipWindow swig_types[164]
+#define SWIGTYPE_p_wxToolTip swig_types[165]
+#define SWIGTYPE_p_wxTopLevelWindow swig_types[166]
+#define SWIGTYPE_p_wxUpdateUIEvent swig_types[167]
+#define SWIGTYPE_p_wxValidator swig_types[168]
+#define SWIGTYPE_p_wxWindow swig_types[169]
+#define SWIGTYPE_p_wxWindowCreateEvent swig_types[170]
+#define SWIGTYPE_p_wxWindowDestroyEvent swig_types[171]
+#define SWIGTYPE_p_wxXPMHandler swig_types[172]
+static swig_type_info *swig_types[174];
+static swig_module_info swig_module = {swig_types, 173, 0, 0, 0, 0};
+#define SWIG_TypeQuery(name) SWIG_TypeQueryModule(&swig_module, &swig_module, name)
+#define SWIG_MangledTypeQuery(name) SWIG_MangledTypeQueryModule(&swig_module, &swig_module, name)
 
-  
-SWIGINTERNINLINE int
-SWIG_Check_float(PyObject* obj)
-{
-  return SWIG_AsVal_float(obj, (float*)0);
-}
+/* -------- TYPES TABLE (END) -------- */
 
-#ifdef __cplusplus
-extern "C" {
+#if (PY_VERSION_HEX <= 0x02000000)
+# if !defined(SWIG_PYTHON_CLASSIC)
+#  error "This python version requires to use swig with the '-classic' option"
+# endif
+#endif
+#if (PY_VERSION_HEX <= 0x02020000)
+# error "This python version requires to use swig with the '-nomodern' option"
+#endif
+#if (PY_VERSION_HEX <= 0x02020000)
+# error "This python version requires to use swig with the '-nomodernargs' option"
+#endif
+#ifndef METH_O
+# error "This python version requires to use swig with the '-nofastunpack' option"
 #endif
-static int _wrap_MOZ_MAJOR_VERSION_set(PyObject *) {
-    PyErr_SetString(PyExc_TypeError,"Variable MOZ_MAJOR_VERSION is read-only.");
-    return 1;
-}
 
+/*-----------------------------------------------
+              @(target):= _mozilla.so
+  ------------------------------------------------*/
+#define SWIG_init    init_mozilla
 
-static PyObject *_wrap_MOZ_MAJOR_VERSION_get(void) {
-    PyObject *pyobj = NULL;
-    
-    {
-        pyobj = SWIG_From_int(static_cast<int >(wxMOZ_MAJOR_VERSION)); 
-    }
-    return pyobj;
-}
+#define SWIG_name    "_mozilla"
 
+#define SWIGVERSION 0x010329 
 
-static int _wrap_MOZ_MINOR_VERSION_set(PyObject *) {
-    PyErr_SetString(PyExc_TypeError,"Variable MOZ_MINOR_VERSION is read-only.");
-    return 1;
-}
 
+#define SWIG_as_voidptr(a) const_cast< void * >(static_cast< const void * >(a)) 
+#define SWIG_as_voidptrptr(a) ((void)SWIG_as_voidptr(*a),reinterpret_cast< void** >(a)) 
 
-static PyObject *_wrap_MOZ_MINOR_VERSION_get(void) {
-    PyObject *pyobj = NULL;
-    
-    {
-        pyobj = SWIG_From_int(static_cast<int >(wxMOZ_MINOR_VERSION)); 
-    }
-    return pyobj;
-}
 
+#include <stdexcept>
 
-static int _wrap_MOZ_RELEASE_NUMBER_set(PyObject *) {
-    PyErr_SetString(PyExc_TypeError,"Variable MOZ_RELEASE_NUMBER is read-only.");
-    return 1;
-}
 
+namespace swig {
+  class PyObject_ptr {
+  protected:
+    PyObject *_obj;
 
-static PyObject *_wrap_MOZ_RELEASE_NUMBER_get(void) {
-    PyObject *pyobj = NULL;
-    
+  public:
+    PyObject_ptr() :_obj(0)
     {
-        pyobj = SWIG_From_int(static_cast<int >(wxMOZ_RELEASE_NUMBER)); 
     }
-    return pyobj;
-}
 
-
-static PyObject *_wrap_new_MozillaBrowser(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) 0 ;
-    int arg2 ;
-    wxPoint const &arg3_defvalue = wxDefaultPosition ;
-    wxPoint *arg3 = (wxPoint *) &arg3_defvalue ;
-    wxSize const &arg4_defvalue = wxDefaultSize ;
-    wxSize *arg4 = (wxSize *) &arg4_defvalue ;
-    long arg5 = (long) 0 ;
-    wxString const &arg6_defvalue = wxPyPanelNameStr ;
-    wxString *arg6 = (wxString *) &arg6_defvalue ;
-    wxMozillaBrowser *result;
-    wxPoint temp3 ;
-    wxSize temp4 ;
-    bool temp6 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    PyObject * obj3 = 0 ;
-    PyObject * obj4 = 0 ;
-    PyObject * obj5 = 0 ;
-    char *kwnames[] = {
-        (char *) "parent",(char *) "id",(char *) "pos",(char *) "size",(char *) "style",(char *) "name", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|OOOO:new_MozillaBrowser",kwnames,&obj0,&obj1,&obj2,&obj3,&obj4,&obj5)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
+    PyObject_ptr(const PyObject_ptr& item) : _obj(item._obj)
     {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    if (obj2) {
-        {
-            arg3 = &temp3;
-            if ( ! wxPoint_helper(obj2, &arg3)) SWIG_fail;
-        }
-    }
-    if (obj3) {
-        {
-            arg4 = &temp4;
-            if ( ! wxSize_helper(obj3, &arg4)) SWIG_fail;
-        }
-    }
-    if (obj4) {
-        {
-            arg5 = static_cast<long >(SWIG_As_long(obj4)); 
-            if (SWIG_arg_fail(5)) SWIG_fail;
-        }
-    }
-    if (obj5) {
-        {
-            arg6 = wxString_in_helper(obj5);
-            if (arg6 == NULL) SWIG_fail;
-            temp6 = true;
-        }
+      Py_XINCREF(_obj);      
     }
+    
+    PyObject_ptr(PyObject *obj, bool initial_ref = true) :_obj(obj)
     {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaBrowser *)new wxMozillaBrowser(arg1,arg2,(wxPoint const &)*arg3,(wxSize const &)*arg4,arg5,(wxString const &)*arg6);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
+      if (initial_ref) Py_XINCREF(_obj);
     }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaBrowser, 1);
+    
+    PyObject_ptr & operator=(const PyObject_ptr& item) 
     {
-        if (temp6)
-        delete arg6;
+      Py_XINCREF(item._obj);
+      Py_XDECREF(_obj);
+      _obj = item._obj;
+      return *this;      
     }
-    return resultobj;
-    fail:
+    
+    ~PyObject_ptr() 
     {
-        if (temp6)
-        delete arg6;
+      Py_XDECREF(_obj);
     }
-    return NULL;
-}
-
-
-static PyObject *_wrap_MozillaBrowser_Create(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxWindow *arg2 = (wxWindow *) 0 ;
-    int arg3 ;
-    wxPoint const &arg4_defvalue = wxDefaultPosition ;
-    wxPoint *arg4 = (wxPoint *) &arg4_defvalue ;
-    wxSize const &arg5_defvalue = wxDefaultSize ;
-    wxSize *arg5 = (wxSize *) &arg5_defvalue ;
-    long arg6 = (long) 0 ;
-    wxString const &arg7_defvalue = wxPyPanelNameStr ;
-    wxString *arg7 = (wxString *) &arg7_defvalue ;
-    bool result;
-    wxPoint temp4 ;
-    wxSize temp5 ;
-    bool temp7 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    PyObject * obj3 = 0 ;
-    PyObject * obj4 = 0 ;
-    PyObject * obj5 = 0 ;
-    PyObject * obj6 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "parent",(char *) "id",(char *) "pos",(char *) "size",(char *) "style",(char *) "name", NULL 
-    };
     
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO|OOOO:MozillaBrowser_Create",kwnames,&obj0,&obj1,&obj2,&obj3,&obj4,&obj5,&obj6)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    SWIG_Python_ConvertPtr(obj1, (void **)&arg2, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(2)) SWIG_fail;
+    operator PyObject *() const
     {
-        arg3 = static_cast<int >(SWIG_As_int(obj2)); 
-        if (SWIG_arg_fail(3)) SWIG_fail;
-    }
-    if (obj3) {
-        {
-            arg4 = &temp4;
-            if ( ! wxPoint_helper(obj3, &arg4)) SWIG_fail;
-        }
-    }
-    if (obj4) {
-        {
-            arg5 = &temp5;
-            if ( ! wxSize_helper(obj4, &arg5)) SWIG_fail;
-        }
-    }
-    if (obj5) {
-        {
-            arg6 = static_cast<long >(SWIG_As_long(obj5)); 
-            if (SWIG_arg_fail(6)) SWIG_fail;
-        }
-    }
-    if (obj6) {
-        {
-            arg7 = wxString_in_helper(obj6);
-            if (arg7 == NULL) SWIG_fail;
-            temp7 = true;
-        }
+      return _obj;
     }
+
+    PyObject *operator->() const
     {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->Create(arg2,arg3,(wxPoint const &)*arg4,(wxSize const &)*arg5,arg6,(wxString const &)*arg7);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
+      return _obj;
     }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  };
+}
+
+
+namespace swig {
+  struct PyObject_var : PyObject_ptr {
+    PyObject_var(PyObject* obj = 0) : PyObject_ptr(obj, false) { }
+    
+    PyObject_var & operator = (PyObject* obj)
+    {
+      Py_XDECREF(_obj);
+      _obj = obj;
+      return *this;      
     }
-    {
-        if (temp7)
-        delete arg7;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp7)
-        delete arg7;
-    }
-    return NULL;
+  };
 }
 
 
-static PyObject *_wrap_MozillaBrowser_LoadURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "location", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_LoadURL",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->LoadURL((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
-}
-
+#include "wx/wxPython/wxPython.h"
+#include "wx/wxPython/pyclasses.h"
+#include "wx/wxPython/pyistream.h"
 
-static PyObject *_wrap_MozillaBrowser_GetURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_GetURL",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetURL();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-#if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
-#else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+#ifdef __WXMAC__  // avoid a bug in Carbon headers
+#define scalb scalbn
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
-}
-
 
-static PyObject *_wrap_MozillaBrowser_SavePage(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool arg3 = (bool) TRUE ;
-    bool result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "filename",(char *) "saveFiles", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|O:MozillaBrowser_SavePage",kwnames,&obj0,&obj1,&obj2)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    if (obj2) {
-        {
-            arg3 = static_cast<bool >(SWIG_As_bool(obj2)); 
-            if (SWIG_arg_fail(3)) SWIG_fail;
-        }
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->SavePage((wxString const &)*arg2,arg3);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
-}
+#include "wxMozillaBrowser.h"
+#include "wxMozillaWindow.h"
+#include "wxMozilla.h"
 
 
-static PyObject *_wrap_MozillaBrowser_IsBusy(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_IsBusy",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->IsBusy();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
-}
+    // Put some wx default wxChar* values into wxStrings.
+    DECLARE_DEF_STRING(PanelNameStr);
 
 
-static PyObject *_wrap_MozillaBrowser_GoBack(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_GoBack",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->GoBack();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
-}
+  #define SWIG_From_long   PyInt_FromLong 
 
 
-static PyObject *_wrap_MozillaBrowser_CanGoBack(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_CanGoBack",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->CanGoBack();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERNINLINE PyObject *
+SWIG_From_int  (int value)
+{    
+  return SWIG_From_long  (value);
 }
 
 
-static PyObject *_wrap_MozillaBrowser_GoForward(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_GoForward",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->GoForward();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
-}
+#include <limits.h>
+#ifndef LLONG_MIN
+# define LLONG_MIN	LONG_LONG_MIN
+#endif
+#ifndef LLONG_MAX
+# define LLONG_MAX	LONG_LONG_MAX
+#endif
+#ifndef ULLONG_MAX
+# define ULLONG_MAX	ULONG_LONG_MAX
+#endif
 
 
-static PyObject *_wrap_MozillaBrowser_CanGoForward(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_CanGoForward",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->CanGoForward();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+SWIGINTERN int
+SWIG_AsVal_long (PyObject* obj, long* val)
+{
+    if (PyNumber_Check(obj)) {
+        if (val) *val = PyInt_AsLong(obj);
+        return SWIG_OK;
     }
-    return resultobj;
-    fail:
-    return NULL;
+    return SWIG_TypeError;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_Stop(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_Stop",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->Stop();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+SWIGINTERN int
+SWIG_AsVal_int (PyObject * obj, int *val)
+{
+  long v;
+  int res = SWIG_AsVal_long (obj, &v);
+  if (SWIG_IsOK(res)) {
+    if ((v < INT_MIN || v > INT_MAX)) {
+      return SWIG_OverflowError;
+    } else {
+      if (val) *val = static_cast< int >(v);
     }
-    return resultobj;
-    fail:
-    return NULL;
+  }  
+  return res;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_Reload(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_Reload",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->Reload();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN int
+SWIG_AsVal_bool (PyObject *obj, bool *val)
+{
+  if (obj == Py_True) {
+    if (val) *val = true;
+    return SWIG_OK;
+  } else if (obj == Py_False) {
+    if (val) *val = false;
+    return SWIG_OK;
+  } else {
+    long v = 0;
+    int res = SWIG_AddCast(SWIG_AsVal_long (obj, val ? &v : 0));
+    if (SWIG_IsOK(res) && val) *val = v ? true : false;
+    return res;
+  }
 }
 
 
-static PyObject *_wrap_MozillaBrowser_Find(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool arg3 = (bool) FALSE ;
-    bool arg4 = (bool) FALSE ;
-    bool arg5 = (bool) TRUE ;
-    bool arg6 = (bool) FALSE ;
-    bool result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    PyObject * obj3 = 0 ;
-    PyObject * obj4 = 0 ;
-    PyObject * obj5 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "searchString",(char *) "matchCase",(char *) "matchWholeWord",(char *) "wrapAround",(char *) "searchBackwards", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|OOOO:MozillaBrowser_Find",kwnames,&obj0,&obj1,&obj2,&obj3,&obj4,&obj5)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    if (obj2) {
-        {
-            arg3 = static_cast<bool >(SWIG_As_bool(obj2)); 
-            if (SWIG_arg_fail(3)) SWIG_fail;
-        }
-    }
-    if (obj3) {
-        {
-            arg4 = static_cast<bool >(SWIG_As_bool(obj3)); 
-            if (SWIG_arg_fail(4)) SWIG_fail;
-        }
-    }
-    if (obj4) {
-        {
-            arg5 = static_cast<bool >(SWIG_As_bool(obj4)); 
-            if (SWIG_arg_fail(5)) SWIG_fail;
-        }
-    }
-    if (obj5) {
-        {
-            arg6 = static_cast<bool >(SWIG_As_bool(obj5)); 
-            if (SWIG_arg_fail(6)) SWIG_fail;
-        }
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->Find((wxString const &)*arg2,arg3,arg4,arg5,arg6);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
-}
+#include <float.h>
 
 
-static PyObject *_wrap_MozillaBrowser_FindNext(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_FindNext",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->FindNext();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+SWIGINTERN int
+SWIG_AsVal_double (PyObject *obj, double* val)
+{
+    if (PyNumber_Check(obj)) {
+        if (val) *val = PyFloat_AsDouble(obj);
+        return SWIG_OK;
     }
-    return resultobj;
-    fail:
-    return NULL;
+    return SWIG_TypeError;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_GetStatus(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_GetStatus",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetStatus();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-#if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
-#else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
-#endif
+SWIGINTERN int
+SWIG_AsVal_float (PyObject * obj, float *val)
+{
+  double v;
+  int res = SWIG_AsVal_double (obj, &v);
+  if (SWIG_IsOK(res)) {
+    if ((v < -FLT_MAX || v > FLT_MAX)) {
+      return SWIG_OverflowError;
+    } else {
+      if (val) *val = static_cast< float >(v);
     }
-    return resultobj;
-    fail:
-    return NULL;
+  }  
+  return res;
 }
 
-
-static PyObject *_wrap_MozillaBrowser_GetSelection(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_GetSelection",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetSelection();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-#if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
-#else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+#ifdef __cplusplus
+extern "C" {
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN int MOZ_MAJOR_VERSION_set(PyObject *) {
+  SWIG_Error(SWIG_AttributeError,"Variable MOZ_MAJOR_VERSION is read-only.");
+  return 1;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_Copy(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_Copy",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->Copy();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MOZ_MAJOR_VERSION_get(void) {
+  PyObject *pyobj = 0;
+  
+  pyobj = SWIG_From_int(static_cast< int >(wxMOZ_MAJOR_VERSION));
+  return pyobj;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_SelectAll(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_SelectAll",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SelectAll();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN int MOZ_MINOR_VERSION_set(PyObject *) {
+  SWIG_Error(SWIG_AttributeError,"Variable MOZ_MINOR_VERSION is read-only.");
+  return 1;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_SelectNone(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_SelectNone",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SelectNone();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MOZ_MINOR_VERSION_get(void) {
+  PyObject *pyobj = 0;
+  
+  pyobj = SWIG_From_int(static_cast< int >(wxMOZ_MINOR_VERSION));
+  return pyobj;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_UpdateBaseURI(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_UpdateBaseURI",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->UpdateBaseURI();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN int MOZ_RELEASE_NUMBER_set(PyObject *) {
+  SWIG_Error(SWIG_AttributeError,"Variable MOZ_RELEASE_NUMBER is read-only.");
+  return 1;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_MakeEditable(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool arg2 = (bool) TRUE ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "enable", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O|O:MozillaBrowser_MakeEditable",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    if (obj1) {
-        {
-            arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-            if (SWIG_arg_fail(2)) SWIG_fail;
-        }
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->MakeEditable(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MOZ_RELEASE_NUMBER_get(void) {
+  PyObject *pyobj = 0;
+  
+  pyobj = SWIG_From_int(static_cast< int >(wxMOZ_RELEASE_NUMBER));
+  return pyobj;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_InsertHTML(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "html", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_InsertHTML",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->InsertHTML(*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
+SWIGINTERN PyObject *_wrap_new_MozillaBrowser(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) 0 ;
+  int arg2 ;
+  wxPoint const &arg3_defvalue = wxDefaultPosition ;
+  wxPoint *arg3 = (wxPoint *) &arg3_defvalue ;
+  wxSize const &arg4_defvalue = wxDefaultSize ;
+  wxSize *arg4 = (wxSize *) &arg4_defvalue ;
+  long arg5 = (long) 0 ;
+  wxString const &arg6_defvalue = wxPyPanelNameStr ;
+  wxString *arg6 = (wxString *) &arg6_defvalue ;
+  wxMozillaBrowser *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  wxPoint temp3 ;
+  wxSize temp4 ;
+  long val5 ;
+  int ecode5 = 0 ;
+  bool temp6 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  PyObject * obj3 = 0 ;
+  PyObject * obj4 = 0 ;
+  PyObject * obj5 = 0 ;
+  char *  kwnames[] = {
+    (char *) "parent",(char *) "id",(char *) "pos",(char *) "size",(char *) "style",(char *) "name", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|OOOO:new_MozillaBrowser",kwnames,&obj0,&obj1,&obj2,&obj3,&obj4,&obj5)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaBrowser" "', expected argument " "1"" of type '" "wxWindow *""'"); 
+  }
+  arg1 = reinterpret_cast< wxWindow * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "new_MozillaBrowser" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  if (obj2) {
     {
-        if (temp2)
-        delete arg2;
+      arg3 = &temp3;
+      if ( ! wxPoint_helper(obj2, &arg3)) SWIG_fail;
     }
-    return NULL;
-}
-
-
-static PyObject *_wrap_MozillaBrowser_IsEditable(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_IsEditable",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
+  }
+  if (obj3) {
     {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->IsEditable();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
+      arg4 = &temp4;
+      if ( ! wxSize_helper(obj3, &arg4)) SWIG_fail;
     }
+  }
+  if (obj4) {
+    ecode5 = SWIG_AsVal_long(obj4, &val5);
+    if (!SWIG_IsOK(ecode5)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode5), "in method '" "new_MozillaBrowser" "', expected argument " "5"" of type '" "long""'");
+    } 
+    arg5 = static_cast< long >(val5);
+  }
+  if (obj5) {
     {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+      arg6 = wxString_in_helper(obj5);
+      if (arg6 == NULL) SWIG_fail;
+      temp6 = true;
     }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaBrowser *)new wxMozillaBrowser(arg1,arg2,(wxPoint const &)*arg3,(wxSize const &)*arg4,arg5,(wxString const &)*arg6);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_NEW |  0 );
+  {
+    if (temp6)
+    delete arg6;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp6)
+    delete arg6;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_EditCommand(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    wxString const &arg3_defvalue = wxEmptyString ;
-    wxString *arg3 = (wxString *) &arg3_defvalue ;
-    bool temp2 = false ;
-    bool temp3 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "cmdId",(char *) "value", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|O:MozillaBrowser_EditCommand",kwnames,&obj0,&obj1,&obj2)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    if (obj2) {
-        {
-            arg3 = wxString_in_helper(obj2);
-            if (arg3 == NULL) SWIG_fail;
-            temp3 = true;
-        }
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->EditCommand((wxString const &)*arg2,(wxString const &)*arg3);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
+SWIGINTERN PyObject *_wrap_MozillaBrowser_Create(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxWindow *arg2 = (wxWindow *) 0 ;
+  int arg3 ;
+  wxPoint const &arg4_defvalue = wxDefaultPosition ;
+  wxPoint *arg4 = (wxPoint *) &arg4_defvalue ;
+  wxSize const &arg5_defvalue = wxDefaultSize ;
+  wxSize *arg5 = (wxSize *) &arg5_defvalue ;
+  long arg6 = (long) 0 ;
+  wxString const &arg7_defvalue = wxPyPanelNameStr ;
+  wxString *arg7 = (wxString *) &arg7_defvalue ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  void *argp2 = 0 ;
+  int res2 = 0 ;
+  int val3 ;
+  int ecode3 = 0 ;
+  wxPoint temp4 ;
+  wxSize temp5 ;
+  long val6 ;
+  int ecode6 = 0 ;
+  bool temp7 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  PyObject * obj3 = 0 ;
+  PyObject * obj4 = 0 ;
+  PyObject * obj5 = 0 ;
+  PyObject * obj6 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "parent",(char *) "id",(char *) "pos",(char *) "size",(char *) "style",(char *) "name", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO|OOOO:MozillaBrowser_Create",kwnames,&obj0,&obj1,&obj2,&obj3,&obj4,&obj5,&obj6)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_Create" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  res2 = SWIG_ConvertPtr(obj1, &argp2,SWIGTYPE_p_wxWindow, 0 |  0 );
+  if (!SWIG_IsOK(res2)) {
+    SWIG_exception_fail(SWIG_ArgError(res2), "in method '" "MozillaBrowser_Create" "', expected argument " "2"" of type '" "wxWindow *""'"); 
+  }
+  arg2 = reinterpret_cast< wxWindow * >(argp2);
+  ecode3 = SWIG_AsVal_int(obj2, &val3);
+  if (!SWIG_IsOK(ecode3)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode3), "in method '" "MozillaBrowser_Create" "', expected argument " "3"" of type '" "int""'");
+  } 
+  arg3 = static_cast< int >(val3);
+  if (obj3) {
     {
-        if (temp3)
-        delete arg3;
+      arg4 = &temp4;
+      if ( ! wxPoint_helper(obj3, &arg4)) SWIG_fail;
     }
-    return resultobj;
-    fail:
+  }
+  if (obj4) {
     {
-        if (temp2)
-        delete arg2;
+      arg5 = &temp5;
+      if ( ! wxSize_helper(obj4, &arg5)) SWIG_fail;
     }
+  }
+  if (obj5) {
+    ecode6 = SWIG_AsVal_long(obj5, &val6);
+    if (!SWIG_IsOK(ecode6)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode6), "in method '" "MozillaBrowser_Create" "', expected argument " "6"" of type '" "long""'");
+    } 
+    arg6 = static_cast< long >(val6);
+  }
+  if (obj6) {
     {
-        if (temp3)
-        delete arg3;
+      arg7 = wxString_in_helper(obj6);
+      if (arg7 == NULL) SWIG_fail;
+      temp7 = true;
     }
-    return NULL;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->Create(arg2,arg3,(wxPoint const &)*arg4,(wxSize const &)*arg5,arg6,(wxString const &)*arg7);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp7)
+    delete arg7;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp7)
+    delete arg7;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_GetCommandState(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    wxString *arg3 = 0 ;
-    bool result;
-    bool temp2 = false ;
-    bool temp3 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "command",(char *) "state", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO:MozillaBrowser_GetCommandState",kwnames,&obj0,&obj1,&obj2)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        arg3 = wxString_in_helper(obj2);
-        if (arg3 == NULL) SWIG_fail;
-        temp3 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->GetCommandState((wxString const &)*arg2,(wxString const &)*arg3);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    {
-        if (temp3)
-        delete arg3;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    {
-        if (temp3)
-        delete arg3;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_LoadURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "location", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_LoadURL",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_LoadURL" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->LoadURL((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_GetStateAttribute(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    wxString result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "command", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_GetStateAttribute",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetStateAttribute(*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetURL" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetURL();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_IsElementInSelection(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "element", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_IsElementInSelection",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->IsElementInSelection(*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SavePage(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  bool arg3 = (bool) TRUE ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  bool val3 ;
+  int ecode3 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "filename",(char *) "saveFiles", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|O:MozillaBrowser_SavePage",kwnames,&obj0,&obj1,&obj2)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SavePage" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  if (obj2) {
+    ecode3 = SWIG_AsVal_bool(obj2, &val3);
+    if (!SWIG_IsOK(ecode3)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode3), "in method '" "MozillaBrowser_SavePage" "', expected argument " "3"" of type '" "bool""'");
+    } 
+    arg3 = static_cast< bool >(val3);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->SavePage((wxString const &)*arg2,arg3);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_SelectElement(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "element", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_SelectElement",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->SelectElement(*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_IsBusy(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_IsBusy" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->IsBusy();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_GetElementAttribute(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    wxString *arg3 = 0 ;
-    wxString result;
-    bool temp2 = false ;
-    bool temp3 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "tagName",(char *) "attrName", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO:MozillaBrowser_GetElementAttribute",kwnames,&obj0,&obj1,&obj2)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        arg3 = wxString_in_helper(obj2);
-        if (arg3 == NULL) SWIG_fail;
-        temp3 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetElementAttribute(*arg2,*arg3);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GoBack(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GoBack" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->GoBack();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_CanGoBack(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_CanGoBack" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->CanGoBack();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GoForward(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GoForward" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->GoForward();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_CanGoForward(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_CanGoForward" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->CanGoForward();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_Stop(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_Stop" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->Stop();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_Reload(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_Reload" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->Reload();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_Find(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  bool arg3 = (bool) FALSE ;
+  bool arg4 = (bool) FALSE ;
+  bool arg5 = (bool) TRUE ;
+  bool arg6 = (bool) FALSE ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  bool val3 ;
+  int ecode3 = 0 ;
+  bool val4 ;
+  int ecode4 = 0 ;
+  bool val5 ;
+  int ecode5 = 0 ;
+  bool val6 ;
+  int ecode6 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  PyObject * obj3 = 0 ;
+  PyObject * obj4 = 0 ;
+  PyObject * obj5 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "searchString",(char *) "matchCase",(char *) "matchWholeWord",(char *) "wrapAround",(char *) "searchBackwards", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|OOOO:MozillaBrowser_Find",kwnames,&obj0,&obj1,&obj2,&obj3,&obj4,&obj5)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_Find" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  if (obj2) {
+    ecode3 = SWIG_AsVal_bool(obj2, &val3);
+    if (!SWIG_IsOK(ecode3)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode3), "in method '" "MozillaBrowser_Find" "', expected argument " "3"" of type '" "bool""'");
+    } 
+    arg3 = static_cast< bool >(val3);
+  }
+  if (obj3) {
+    ecode4 = SWIG_AsVal_bool(obj3, &val4);
+    if (!SWIG_IsOK(ecode4)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode4), "in method '" "MozillaBrowser_Find" "', expected argument " "4"" of type '" "bool""'");
+    } 
+    arg4 = static_cast< bool >(val4);
+  }
+  if (obj4) {
+    ecode5 = SWIG_AsVal_bool(obj4, &val5);
+    if (!SWIG_IsOK(ecode5)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode5), "in method '" "MozillaBrowser_Find" "', expected argument " "5"" of type '" "bool""'");
+    } 
+    arg5 = static_cast< bool >(val5);
+  }
+  if (obj5) {
+    ecode6 = SWIG_AsVal_bool(obj5, &val6);
+    if (!SWIG_IsOK(ecode6)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode6), "in method '" "MozillaBrowser_Find" "', expected argument " "6"" of type '" "bool""'");
+    } 
+    arg6 = static_cast< bool >(val6);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->Find((wxString const &)*arg2,arg3,arg4,arg5,arg6);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_FindNext(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_FindNext" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->FindNext();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetStatus(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetStatus" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetStatus();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    {
-        if (temp3)
-        delete arg3;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    {
-        if (temp3)
-        delete arg3;
-    }
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_SetElementAttribute(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    wxString *arg3 = 0 ;
-    bool temp2 = false ;
-    bool temp3 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "attrName",(char *) "attrValue", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO:MozillaBrowser_SetElementAttribute",kwnames,&obj0,&obj1,&obj2)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        arg3 = wxString_in_helper(obj2);
-        if (arg3 == NULL) SWIG_fail;
-        temp3 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetElementAttribute(*arg2,*arg3);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    {
-        if (temp3)
-        delete arg3;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    {
-        if (temp3)
-        delete arg3;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetSelection(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetSelection" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetSelection();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+#if wxUSE_UNICODE
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+#else
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+#endif
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_SetPage(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString *arg2 = 0 ;
-    bool result;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "data", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_SetPage",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->SetPage((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_Copy(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_Copy" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->Copy();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_GetPage(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBrowser_GetPage",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetPage();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SelectAll(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SelectAll" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SelectAll();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SelectNone(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SelectNone" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SelectNone();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_UpdateBaseURI(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_UpdateBaseURI" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->UpdateBaseURI();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_MakeEditable(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool arg2 = (bool) TRUE ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "enable", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O|O:MozillaBrowser_MakeEditable",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_MakeEditable" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  if (obj1) {
+    ecode2 = SWIG_AsVal_bool(obj1, &val2);
+    if (!SWIG_IsOK(ecode2)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaBrowser_MakeEditable" "', expected argument " "2"" of type '" "bool""'");
+    } 
+    arg2 = static_cast< bool >(val2);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->MakeEditable(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_InsertHTML(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "html", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_InsertHTML",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_InsertHTML" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->InsertHTML(*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_IsEditable(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_IsEditable" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->IsEditable();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_EditCommand(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  wxString const &arg3_defvalue = wxEmptyString ;
+  wxString *arg3 = (wxString *) &arg3_defvalue ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  bool temp3 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "cmdId",(char *) "value", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO|O:MozillaBrowser_EditCommand",kwnames,&obj0,&obj1,&obj2)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_EditCommand" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  if (obj2) {
+    {
+      arg3 = wxString_in_helper(obj2);
+      if (arg3 == NULL) SWIG_fail;
+      temp3 = true;
     }
-    {
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->EditCommand((wxString const &)*arg2,(wxString const &)*arg3);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetCommandState(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  wxString *arg3 = 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  bool temp3 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "command",(char *) "state", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO:MozillaBrowser_GetCommandState",kwnames,&obj0,&obj1,&obj2)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetCommandState" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    arg3 = wxString_in_helper(obj2);
+    if (arg3 == NULL) SWIG_fail;
+    temp3 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->GetCommandState((wxString const &)*arg2,(wxString const &)*arg3);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetStateAttribute(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "command", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_GetStateAttribute",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetStateAttribute" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetStateAttribute(*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBrowser_SetZoom(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    float arg2 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "level", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_SetZoom",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<float >(SWIG_As_float(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->SetZoom(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_IsElementInSelection(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "element", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_IsElementInSelection",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_IsElementInSelection" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->IsElementInSelection(*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaBrowser(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaBrowser",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SelectElement(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "element", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_SelectElement",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SelectElement" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->SelectElement(*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetElementAttribute(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  wxString *arg3 = 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  bool temp3 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "tagName",(char *) "attrName", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO:MozillaBrowser_GetElementAttribute",kwnames,&obj0,&obj1,&obj2)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetElementAttribute" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    arg3 = wxString_in_helper(obj2);
+    if (arg3 == NULL) SWIG_fail;
+    temp3 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetElementAttribute(*arg2,*arg3);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+#if wxUSE_UNICODE
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+#else
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+#endif
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SetElementAttribute(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  wxString *arg3 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  bool temp3 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "attrName",(char *) "attrValue", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OOO:MozillaBrowser_SetElementAttribute",kwnames,&obj0,&obj1,&obj2)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SetElementAttribute" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    arg3 = wxString_in_helper(obj2);
+    if (arg3 == NULL) SWIG_fail;
+    temp3 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetElementAttribute(*arg2,*arg3);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  {
+    if (temp3)
+    delete arg3;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SetPage(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString *arg2 = 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "data", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_SetPage",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SetPage" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->SetPage((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
+}
+
+
+SWIGINTERN PyObject *_wrap_MozillaBrowser_GetPage(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_GetPage" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetPage();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+#if wxUSE_UNICODE
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+#else
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+#endif
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject * MozillaBrowser_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaBrowser, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_new_MozillaWindow(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    bool arg1 = (bool) TRUE ;
-    bool arg2 = (bool) TRUE ;
-    bool arg3 = (bool) TRUE ;
-    wxMozillaWindow *result;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    PyObject * obj2 = 0 ;
-    char *kwnames[] = {
-        (char *) "showMenu",(char *) "showToolbar",(char *) "showStatusbar", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|OOO:new_MozillaWindow",kwnames,&obj0,&obj1,&obj2)) goto fail;
-    if (obj0) {
-        {
-            arg1 = static_cast<bool >(SWIG_As_bool(obj0)); 
-            if (SWIG_arg_fail(1)) SWIG_fail;
-        }
-    }
-    if (obj1) {
-        {
-            arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-            if (SWIG_arg_fail(2)) SWIG_fail;
-        }
-    }
-    if (obj2) {
-        {
-            arg3 = static_cast<bool >(SWIG_As_bool(obj2)); 
-            if (SWIG_arg_fail(3)) SWIG_fail;
-        }
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaWindow *)new wxMozillaWindow(arg1,arg2,arg3);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaWindow, 1);
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBrowser_SetZoom(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBrowser *arg1 = (wxMozillaBrowser *) 0 ;
+  float arg2 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  float val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "level", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBrowser_SetZoom",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBrowser_SetZoom" "', expected argument " "1"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBrowser * >(argp1);
+  ecode2 = SWIG_AsVal_float(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaBrowser_SetZoom" "', expected argument " "2"" of type '" "float""'");
+  } 
+  arg2 = static_cast< float >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->SetZoom(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaWindow_Mozilla_set(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaWindow *arg1 = (wxMozillaWindow *) 0 ;
-    wxMozillaBrowser *arg2 = (wxMozillaBrowser *) 0 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "Mozilla", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaWindow_Mozilla_set",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaWindow, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    SWIG_Python_ConvertPtr(obj1, (void **)&arg2, SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_EXCEPTION | SWIG_POINTER_DISOWN);
-    if (SWIG_arg_fail(2)) SWIG_fail;
-    if (arg1) (arg1)->Mozilla = arg2;
-    
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaBrowser_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaBrowser, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
+}
+
+SWIGINTERN PyObject *MozillaBrowser_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
+
+SWIGINTERN PyObject *_wrap_new_MozillaWindow(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  bool arg1 = (bool) TRUE ;
+  bool arg2 = (bool) TRUE ;
+  bool arg3 = (bool) TRUE ;
+  wxMozillaWindow *result = 0 ;
+  bool val1 ;
+  int ecode1 = 0 ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  bool val3 ;
+  int ecode3 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  PyObject * obj2 = 0 ;
+  char *  kwnames[] = {
+    (char *) "showMenu",(char *) "showToolbar",(char *) "showStatusbar", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|OOO:new_MozillaWindow",kwnames,&obj0,&obj1,&obj2)) SWIG_fail;
+  if (obj0) {
+    ecode1 = SWIG_AsVal_bool(obj0, &val1);
+    if (!SWIG_IsOK(ecode1)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode1), "in method '" "new_MozillaWindow" "', expected argument " "1"" of type '" "bool""'");
+    } 
+    arg1 = static_cast< bool >(val1);
+  }
+  if (obj1) {
+    ecode2 = SWIG_AsVal_bool(obj1, &val2);
+    if (!SWIG_IsOK(ecode2)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "new_MozillaWindow" "', expected argument " "2"" of type '" "bool""'");
+    } 
+    arg2 = static_cast< bool >(val2);
+  }
+  if (obj2) {
+    ecode3 = SWIG_AsVal_bool(obj2, &val3);
+    if (!SWIG_IsOK(ecode3)) {
+      SWIG_exception_fail(SWIG_ArgError(ecode3), "in method '" "new_MozillaWindow" "', expected argument " "3"" of type '" "bool""'");
+    } 
+    arg3 = static_cast< bool >(val3);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaWindow *)new wxMozillaWindow(arg1,arg2,arg3);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaWindow, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaWindow_Mozilla_get(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaWindow *arg1 = (wxMozillaWindow *) 0 ;
-    wxMozillaBrowser *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaWindow_Mozilla_get",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaWindow, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    result = (wxMozillaBrowser *) ((arg1)->Mozilla);
-    
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaBrowser, 0);
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaWindow_Mozilla_set(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaWindow *arg1 = (wxMozillaWindow *) 0 ;
+  wxMozillaBrowser *arg2 = (wxMozillaBrowser *) 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  void *argp2 = 0 ;
+  int res2 = 0 ;
+  PyObject *swig_obj[2] ;
+  
+  if (!SWIG_Python_UnpackTuple(args,"MozillaWindow_Mozilla_set",2,2,swig_obj)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaWindow, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaWindow_Mozilla_set" "', expected argument " "1"" of type '" "wxMozillaWindow *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaWindow * >(argp1);
+  res2 = SWIG_ConvertPtr(swig_obj[1], &argp2,SWIGTYPE_p_wxMozillaBrowser, SWIG_POINTER_DISOWN |  0 );
+  if (!SWIG_IsOK(res2)) {
+    SWIG_exception_fail(SWIG_ArgError(res2), "in method '" "MozillaWindow_Mozilla_set" "', expected argument " "2"" of type '" "wxMozillaBrowser *""'"); 
+  }
+  arg2 = reinterpret_cast< wxMozillaBrowser * >(argp2);
+  if (arg1) (arg1)->Mozilla = arg2;
+  
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaWindow(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaWindow *arg1 = (wxMozillaWindow *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaWindow",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaWindow, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaWindow_Mozilla_get(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaWindow *arg1 = (wxMozillaWindow *) 0 ;
+  wxMozillaBrowser *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaWindow, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaWindow_Mozilla_get" "', expected argument " "1"" of type '" "wxMozillaWindow *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaWindow * >(argp1);
+  result = (wxMozillaBrowser *) ((arg1)->Mozilla);
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaBrowser, 0 |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject * MozillaWindow_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaWindow, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaSettings_SetProfilePath(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    bool result;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "path", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_SetProfilePath",kwnames,&obj0)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)wxMozillaSettings::SetProfilePath((wxString const &)*arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
+SWIGINTERN PyObject *MozillaWindow_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaWindow, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
+}
+
+SWIGINTERN PyObject *MozillaWindow_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
+
+SWIGINTERN PyObject *_wrap_MozillaSettings_SetProfilePath(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  bool result;
+  bool temp1 = false ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "path", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_SetProfilePath",kwnames,&obj0)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)wxMozillaSettings::SetProfilePath((wxString const &)*arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_GetProfilePath(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString result;
-    char *kwnames[] = {
-        NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)":MozillaSettings_GetProfilePath",kwnames)) goto fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = wxMozillaSettings::GetProfilePath();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaSettings_GetProfilePath(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxString result;
+  
+  if (!SWIG_Python_UnpackTuple(args,"MozillaSettings_GetProfilePath",0,0,0)) SWIG_fail;
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = wxMozillaSettings::GetProfilePath();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_SetMozillaPath(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "path", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_SetMozillaPath",kwnames,&obj0)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        wxMozillaSettings::SetMozillaPath((wxString const &)*arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_SetMozillaPath(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  bool temp1 = false ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "path", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_SetMozillaPath",kwnames,&obj0)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    wxMozillaSettings::SetMozillaPath((wxString const &)*arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_GetMozillaPath(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString result;
-    char *kwnames[] = {
-        NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)":MozillaSettings_GetMozillaPath",kwnames)) goto fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = wxMozillaSettings::GetMozillaPath();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaSettings_GetMozillaPath(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxString result;
+  
+  if (!SWIG_Python_UnpackTuple(args,"MozillaSettings_GetMozillaPath",0,0,0)) SWIG_fail;
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = wxMozillaSettings::GetMozillaPath();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_SetBoolPref(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    bool arg2 ;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "name",(char *) "value", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSettings_SetBoolPref",kwnames,&obj0,&obj1)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        wxMozillaSettings::SetBoolPref((wxString const &)*arg1,arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_SetBoolPref(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  bool arg2 ;
+  bool temp1 = false ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "name",(char *) "value", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSettings_SetBoolPref",kwnames,&obj0,&obj1)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  ecode2 = SWIG_AsVal_bool(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaSettings_SetBoolPref" "', expected argument " "2"" of type '" "bool""'");
+  } 
+  arg2 = static_cast< bool >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    wxMozillaSettings::SetBoolPref((wxString const &)*arg1,arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_GetBoolPref(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    bool result;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "name", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_GetBoolPref",kwnames,&obj0)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)wxMozillaSettings::GetBoolPref((wxString const &)*arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_GetBoolPref(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  bool result;
+  bool temp1 = false ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "name", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_GetBoolPref",kwnames,&obj0)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)wxMozillaSettings::GetBoolPref((wxString const &)*arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_SetStrPref(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    wxString *arg2 = 0 ;
-    bool temp1 = false ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "name",(char *) "value", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSettings_SetStrPref",kwnames,&obj0,&obj1)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        wxMozillaSettings::SetStrPref((wxString const &)*arg1,(wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp1)
-        delete arg1;
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_SetStrPref(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  wxString *arg2 = 0 ;
+  bool temp1 = false ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "name",(char *) "value", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSettings_SetStrPref",kwnames,&obj0,&obj1)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    wxMozillaSettings::SetStrPref((wxString const &)*arg1,(wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp1)
+    delete arg1;
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_GetStrPref(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    wxString result;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "name", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_GetStrPref",kwnames,&obj0)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = wxMozillaSettings::GetStrPref((wxString const &)*arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaSettings_GetStrPref(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  wxString result;
+  bool temp1 = false ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "name", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_GetStrPref",kwnames,&obj0)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = wxMozillaSettings::GetStrPref((wxString const &)*arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
-}
-
-
-static PyObject *_wrap_MozillaSettings_SetIntPref(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    int arg2 ;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "name",(char *) "value", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSettings_SetIntPref",kwnames,&obj0,&obj1)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        wxMozillaSettings::SetIntPref((wxString const &)*arg1,arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
-}
-
-
-static PyObject *_wrap_MozillaSettings_GetIntPref(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxString *arg1 = 0 ;
-    int result;
-    bool temp1 = false ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "name", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_GetIntPref",kwnames,&obj0)) goto fail;
-    {
-        arg1 = wxString_in_helper(obj0);
-        if (arg1 == NULL) SWIG_fail;
-        temp1 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)wxMozillaSettings::GetIntPref((wxString const &)*arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp1)
-        delete arg1;
-    }
-    return NULL;
+  }
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaSettings_SavePrefs(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    char *kwnames[] = {
-        NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)":MozillaSettings_SavePrefs",kwnames)) goto fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        wxMozillaSettings::SavePrefs();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_SetIntPref(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  int arg2 ;
+  bool temp1 = false ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "name",(char *) "value", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSettings_SetIntPref",kwnames,&obj0,&obj1)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaSettings_SetIntPref" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    wxMozillaSettings::SetIntPref((wxString const &)*arg1,arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaSettings(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaSettings *result;
-    char *kwnames[] = {
-        NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)":new_MozillaSettings",kwnames)) goto fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaSettings *)new wxMozillaSettings();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaSettings, 1);
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_GetIntPref(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxString *arg1 = 0 ;
+  int result;
+  bool temp1 = false ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "name", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSettings_GetIntPref",kwnames,&obj0)) SWIG_fail;
+  {
+    arg1 = wxString_in_helper(obj0);
+    if (arg1 == NULL) SWIG_fail;
+    temp1 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)wxMozillaSettings::GetIntPref((wxString const &)*arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp1)
+    delete arg1;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaSettings(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaSettings *arg1 = (wxMozillaSettings *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaSettings",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaSettings, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSettings_SavePrefs(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  
+  if (!SWIG_Python_UnpackTuple(args,"MozillaSettings_SavePrefs",0,0,0)) SWIG_fail;
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    wxMozillaSettings::SavePrefs();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject * MozillaSettings_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaSettings, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaBeforeLoadEvent_GetURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBeforeLoadEvent_GetURL",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetURL();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *MozillaSettings_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaSettings, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
+}
+
+SWIGINTERN PyObject *_wrap_MozillaBeforeLoadEvent_GetURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBeforeLoadEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBeforeLoadEvent_GetURL" "', expected argument " "1"" of type '" "wxMozillaBeforeLoadEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBeforeLoadEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetURL();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBeforeLoadEvent_SetURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "newURL", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBeforeLoadEvent_SetURL",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetURL((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBeforeLoadEvent_SetURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "newURL", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaBeforeLoadEvent_SetURL",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaBeforeLoadEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBeforeLoadEvent_SetURL" "', expected argument " "1"" of type '" "wxMozillaBeforeLoadEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBeforeLoadEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetURL((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBeforeLoadEvent_Cancel(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBeforeLoadEvent_Cancel",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->Cancel();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBeforeLoadEvent_Cancel(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBeforeLoadEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBeforeLoadEvent_Cancel" "', expected argument " "1"" of type '" "wxMozillaBeforeLoadEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBeforeLoadEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->Cancel();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaBeforeLoadEvent_IsCancelled(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaBeforeLoadEvent_IsCancelled",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->IsCancelled();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaBeforeLoadEvent_IsCancelled(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaBeforeLoadEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaBeforeLoadEvent_IsCancelled" "', expected argument " "1"" of type '" "wxMozillaBeforeLoadEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaBeforeLoadEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->IsCancelled();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaBeforeLoadEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaBeforeLoadEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaBeforeLoadEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaBeforeLoadEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaBeforeLoadEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaBeforeLoadEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaBeforeLoadEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaBeforeLoadEvent *)new wxMozillaBeforeLoadEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaBeforeLoadEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaBeforeLoadEvent *)new wxMozillaBeforeLoadEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaBeforeLoadEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaBeforeLoadEvent *arg1 = (wxMozillaBeforeLoadEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaBeforeLoadEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaBeforeLoadEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaBeforeLoadEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
+SWIGINTERN PyObject *MozillaBeforeLoadEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
 
-static PyObject * MozillaBeforeLoadEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaBeforeLoadEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaLinkChangedEvent_GetNewURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaLinkChangedEvent_GetNewURL",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetNewURL();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaLinkChangedEvent_GetNewURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaLinkChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaLinkChangedEvent_GetNewURL" "', expected argument " "1"" of type '" "wxMozillaLinkChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaLinkChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetNewURL();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaLinkChangedEvent_CanGoBack(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaLinkChangedEvent_CanGoBack",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->CanGoBack();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaLinkChangedEvent_CanGoBack(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaLinkChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaLinkChangedEvent_CanGoBack" "', expected argument " "1"" of type '" "wxMozillaLinkChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaLinkChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->CanGoBack();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaLinkChangedEvent_CanGoForward(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaLinkChangedEvent_CanGoForward",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->CanGoForward();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaLinkChangedEvent_CanGoForward(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaLinkChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaLinkChangedEvent_CanGoForward" "', expected argument " "1"" of type '" "wxMozillaLinkChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaLinkChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->CanGoForward();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaLinkChangedEvent_SetNewURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "newurl", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaLinkChangedEvent_SetNewURL",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetNewURL((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaLinkChangedEvent_SetNewURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "newurl", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaLinkChangedEvent_SetNewURL",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaLinkChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaLinkChangedEvent_SetNewURL" "', expected argument " "1"" of type '" "wxMozillaLinkChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaLinkChangedEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetNewURL((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaLinkChangedEvent_SetCanGoBack(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    bool arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "goback", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaLinkChangedEvent_SetCanGoBack",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetCanGoBack(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaLinkChangedEvent_SetCanGoBack(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
+  bool arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "goback", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaLinkChangedEvent_SetCanGoBack",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaLinkChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaLinkChangedEvent_SetCanGoBack" "', expected argument " "1"" of type '" "wxMozillaLinkChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaLinkChangedEvent * >(argp1);
+  ecode2 = SWIG_AsVal_bool(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaLinkChangedEvent_SetCanGoBack" "', expected argument " "2"" of type '" "bool""'");
+  } 
+  arg2 = static_cast< bool >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetCanGoBack(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaLinkChangedEvent_SetCanGoForward(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    bool arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "goforward", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaLinkChangedEvent_SetCanGoForward",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetCanGoForward(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaLinkChangedEvent_SetCanGoForward(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
+  bool arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "goforward", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaLinkChangedEvent_SetCanGoForward",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaLinkChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaLinkChangedEvent_SetCanGoForward" "', expected argument " "1"" of type '" "wxMozillaLinkChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaLinkChangedEvent * >(argp1);
+  ecode2 = SWIG_AsVal_bool(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaLinkChangedEvent_SetCanGoForward" "', expected argument " "2"" of type '" "bool""'");
+  } 
+  arg2 = static_cast< bool >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetCanGoForward(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaLinkChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaLinkChangedEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaLinkChangedEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaLinkChangedEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaLinkChangedEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaLinkChangedEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaLinkChangedEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaLinkChangedEvent *)new wxMozillaLinkChangedEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaLinkChangedEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaLinkChangedEvent *)new wxMozillaLinkChangedEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaLinkChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLinkChangedEvent *arg1 = (wxMozillaLinkChangedEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaLinkChangedEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaLinkChangedEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaLinkChangedEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
+SWIGINTERN PyObject *MozillaLinkChangedEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
 
-static PyObject * MozillaLinkChangedEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaLinkChangedEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaStateChangedEvent_GetState(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaStateChangedEvent_GetState",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetState();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaStateChangedEvent_GetState(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaStateChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStateChangedEvent_GetState" "', expected argument " "1"" of type '" "wxMozillaStateChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStateChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetState();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaStateChangedEvent_SetState(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "state", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStateChangedEvent_SetState",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int const >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetState(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaStateChangedEvent_SetState(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "state", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStateChangedEvent_SetState",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaStateChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStateChangedEvent_SetState" "', expected argument " "1"" of type '" "wxMozillaStateChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStateChangedEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaStateChangedEvent_SetState" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetState(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaStateChangedEvent_GetURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaStateChangedEvent_GetURL",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetURL();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaStateChangedEvent_GetURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaStateChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStateChangedEvent_GetURL" "', expected argument " "1"" of type '" "wxMozillaStateChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStateChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetURL();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaStateChangedEvent_SetURL(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "url", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStateChangedEvent_SetURL",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetURL((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaStateChangedEvent_SetURL(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "url", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStateChangedEvent_SetURL",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaStateChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStateChangedEvent_SetURL" "', expected argument " "1"" of type '" "wxMozillaStateChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStateChangedEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetURL((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaStateChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaStateChangedEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaStateChangedEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaStateChangedEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaStateChangedEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaStateChangedEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaStateChangedEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaStateChangedEvent *)new wxMozillaStateChangedEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaStateChangedEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaStateChangedEvent *)new wxMozillaStateChangedEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaStateChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStateChangedEvent *arg1 = (wxMozillaStateChangedEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaStateChangedEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaStateChangedEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaStateChangedEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
-
-static PyObject * MozillaStateChangedEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaStateChangedEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaSecurityChangedEvent_GetSecurity(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaSecurityChangedEvent *arg1 = (wxMozillaSecurityChangedEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaSecurityChangedEvent_GetSecurity",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaSecurityChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetSecurity();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaStateChangedEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
 }
 
-
-static PyObject *_wrap_MozillaSecurityChangedEvent_SetSecurity(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaSecurityChangedEvent *arg1 = (wxMozillaSecurityChangedEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "security", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSecurityChangedEvent_SetSecurity",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaSecurityChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int const >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetSecurity(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSecurityChangedEvent_GetSecurity(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaSecurityChangedEvent *arg1 = (wxMozillaSecurityChangedEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaSecurityChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaSecurityChangedEvent_GetSecurity" "', expected argument " "1"" of type '" "wxMozillaSecurityChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaSecurityChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetSecurity();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaSecurityChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaSecurityChangedEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaSecurityChangedEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaSecurityChangedEvent *)new wxMozillaSecurityChangedEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaSecurityChangedEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaSecurityChangedEvent_SetSecurity(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaSecurityChangedEvent *arg1 = (wxMozillaSecurityChangedEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "security", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaSecurityChangedEvent_SetSecurity",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaSecurityChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaSecurityChangedEvent_SetSecurity" "', expected argument " "1"" of type '" "wxMozillaSecurityChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaSecurityChangedEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaSecurityChangedEvent_SetSecurity" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetSecurity(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaSecurityChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaSecurityChangedEvent *arg1 = (wxMozillaSecurityChangedEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaSecurityChangedEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaSecurityChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_new_MozillaSecurityChangedEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaSecurityChangedEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaSecurityChangedEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaSecurityChangedEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
+    }
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaSecurityChangedEvent *)new wxMozillaSecurityChangedEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaSecurityChangedEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject * MozillaSecurityChangedEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaSecurityChangedEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_new_MozillaLoadCompleteEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaLoadCompleteEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaLoadCompleteEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *MozillaSecurityChangedEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaSecurityChangedEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
+}
+
+SWIGINTERN PyObject *MozillaSecurityChangedEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
+
+SWIGINTERN PyObject *_wrap_new_MozillaLoadCompleteEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaLoadCompleteEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaLoadCompleteEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaLoadCompleteEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaLoadCompleteEvent *)new wxMozillaLoadCompleteEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaLoadCompleteEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaLoadCompleteEvent *)new wxMozillaLoadCompleteEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaLoadCompleteEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaLoadCompleteEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaLoadCompleteEvent *arg1 = (wxMozillaLoadCompleteEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaLoadCompleteEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaLoadCompleteEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaLoadCompleteEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaLoadCompleteEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
+SWIGINTERN PyObject *MozillaLoadCompleteEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
 
-static PyObject * MozillaLoadCompleteEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaLoadCompleteEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaStatusChangedEvent_GetStatusText(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaStatusChangedEvent_GetStatusText",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetStatusText();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaStatusChangedEvent_GetStatusText(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaStatusChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStatusChangedEvent_GetStatusText" "', expected argument " "1"" of type '" "wxMozillaStatusChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStatusChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetStatusText();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaStatusChangedEvent_IsBusy(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaStatusChangedEvent_IsBusy",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->IsBusy();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaStatusChangedEvent_IsBusy(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaStatusChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStatusChangedEvent_IsBusy" "', expected argument " "1"" of type '" "wxMozillaStatusChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStatusChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->IsBusy();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaStatusChangedEvent_SetStatusText(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "status", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStatusChangedEvent_SetStatusText",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetStatusText((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaStatusChangedEvent_SetStatusText(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "status", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStatusChangedEvent_SetStatusText",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaStatusChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStatusChangedEvent_SetStatusText" "', expected argument " "1"" of type '" "wxMozillaStatusChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStatusChangedEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetStatusText((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaStatusChangedEvent_SetBusy(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
-    bool arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "isbusy", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStatusChangedEvent_SetBusy",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetBusy(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaStatusChangedEvent_SetBusy(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
+  bool arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "isbusy", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaStatusChangedEvent_SetBusy",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaStatusChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaStatusChangedEvent_SetBusy" "', expected argument " "1"" of type '" "wxMozillaStatusChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaStatusChangedEvent * >(argp1);
+  ecode2 = SWIG_AsVal_bool(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaStatusChangedEvent_SetBusy" "', expected argument " "2"" of type '" "bool""'");
+  } 
+  arg2 = static_cast< bool >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetBusy(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaStatusChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaStatusChangedEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaStatusChangedEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaStatusChangedEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaStatusChangedEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaStatusChangedEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaStatusChangedEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaStatusChangedEvent *)new wxMozillaStatusChangedEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaStatusChangedEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaStatusChangedEvent *)new wxMozillaStatusChangedEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaStatusChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaStatusChangedEvent *arg1 = (wxMozillaStatusChangedEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaStatusChangedEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaStatusChangedEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaStatusChangedEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
+SWIGINTERN PyObject *MozillaStatusChangedEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
 
-static PyObject * MozillaStatusChangedEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaStatusChangedEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaTitleChangedEvent_GetTitle(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaTitleChangedEvent *arg1 = (wxMozillaTitleChangedEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaTitleChangedEvent_GetTitle",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaTitleChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetTitle();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaTitleChangedEvent_GetTitle(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaTitleChangedEvent *arg1 = (wxMozillaTitleChangedEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaTitleChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaTitleChangedEvent_GetTitle" "', expected argument " "1"" of type '" "wxMozillaTitleChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaTitleChangedEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetTitle();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaTitleChangedEvent_SetTitle(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaTitleChangedEvent *arg1 = (wxMozillaTitleChangedEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "title", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaTitleChangedEvent_SetTitle",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaTitleChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetTitle((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaTitleChangedEvent_SetTitle(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaTitleChangedEvent *arg1 = (wxMozillaTitleChangedEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "title", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaTitleChangedEvent_SetTitle",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaTitleChangedEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaTitleChangedEvent_SetTitle" "', expected argument " "1"" of type '" "wxMozillaTitleChangedEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaTitleChangedEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetTitle((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaTitleChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaTitleChangedEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaTitleChangedEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaTitleChangedEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaTitleChangedEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaTitleChangedEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaTitleChangedEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaTitleChangedEvent *)new wxMozillaTitleChangedEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaTitleChangedEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaTitleChangedEvent *)new wxMozillaTitleChangedEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaTitleChangedEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaTitleChangedEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaTitleChangedEvent *arg1 = (wxMozillaTitleChangedEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaTitleChangedEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaTitleChangedEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaTitleChangedEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaTitleChangedEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
+SWIGINTERN PyObject *MozillaTitleChangedEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
 
-static PyObject * MozillaTitleChangedEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaTitleChangedEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaProgressEvent_GetSelfCurrentProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaProgressEvent_GetSelfCurrentProgress",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetSelfCurrentProgress();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_GetSelfCurrentProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_GetSelfCurrentProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetSelfCurrentProgress();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_SetSelfCurrentProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "progress", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetSelfCurrentProgress",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetSelfCurrentProgress(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_SetSelfCurrentProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "progress", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetSelfCurrentProgress",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_SetSelfCurrentProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaProgressEvent_SetSelfCurrentProgress" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetSelfCurrentProgress(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_GetSelfMaxProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaProgressEvent_GetSelfMaxProgress",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetSelfMaxProgress();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_GetSelfMaxProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_GetSelfMaxProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetSelfMaxProgress();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_SetSelfMaxProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "progress", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetSelfMaxProgress",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetSelfMaxProgress(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_SetSelfMaxProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "progress", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetSelfMaxProgress",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_SetSelfMaxProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaProgressEvent_SetSelfMaxProgress" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetSelfMaxProgress(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_GetTotalCurrentProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaProgressEvent_GetTotalCurrentProgress",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetTotalCurrentProgress();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_GetTotalCurrentProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_GetTotalCurrentProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetTotalCurrentProgress();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_SetTotalCurrentProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "progress", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetTotalCurrentProgress",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetTotalCurrentProgress(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_SetTotalCurrentProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "progress", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetTotalCurrentProgress",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_SetTotalCurrentProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaProgressEvent_SetTotalCurrentProgress" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetTotalCurrentProgress(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_GetTotalMaxProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaProgressEvent_GetTotalMaxProgress",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetTotalMaxProgress();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_GetTotalMaxProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_GetTotalMaxProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetTotalMaxProgress();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaProgressEvent_SetTotalMaxProgress(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "progress", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetTotalMaxProgress",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetTotalMaxProgress(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaProgressEvent_SetTotalMaxProgress(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "progress", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaProgressEvent_SetTotalMaxProgress",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaProgressEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaProgressEvent_SetTotalMaxProgress" "', expected argument " "1"" of type '" "wxMozillaProgressEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaProgressEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaProgressEvent_SetTotalMaxProgress" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetTotalMaxProgress(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaProgressEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaProgressEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaProgressEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaProgressEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaProgressEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaProgressEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaProgressEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaProgressEvent *)new wxMozillaProgressEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaProgressEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaProgressEvent *)new wxMozillaProgressEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaProgressEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaProgressEvent *arg1 = (wxMozillaProgressEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaProgressEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaProgressEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaProgressEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaProgressEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
+SWIGINTERN PyObject *MozillaProgressEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
+}
 
-static PyObject * MozillaProgressEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaProgressEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
-}
-static PyObject *_wrap_MozillaRightClickEvent_IsBusy(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    bool result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaRightClickEvent_IsBusy",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (bool)(arg1)->IsBusy();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_IsBusy(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  bool result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_IsBusy" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (bool)(arg1)->IsBusy();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
+    resultobj = result ? Py_True : Py_False; Py_INCREF(resultobj);
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_SetBusy(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    bool arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "isbusy", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetBusy",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<bool >(SWIG_As_bool(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetBusy(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_SetBusy(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  bool arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "isbusy", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetBusy",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_SetBusy" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  ecode2 = SWIG_AsVal_bool(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaRightClickEvent_SetBusy" "', expected argument " "2"" of type '" "bool""'");
+  } 
+  arg2 = static_cast< bool >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetBusy(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_GetBackgroundImageSrc(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaRightClickEvent_GetBackgroundImageSrc",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetBackgroundImageSrc();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_GetBackgroundImageSrc(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_GetBackgroundImageSrc" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetBackgroundImageSrc();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_SetBackgroundImageSrc(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "name", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetBackgroundImageSrc",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetBackgroundImageSrc((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_SetBackgroundImageSrc(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "name", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetBackgroundImageSrc",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_SetBackgroundImageSrc" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetBackgroundImageSrc((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_GetText(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaRightClickEvent_GetText",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetText();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_GetText(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_GetText" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetText();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_SetText(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "text", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetText",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetText((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_SetText(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "text", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetText",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_SetText" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetText((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_GetImageSrc(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaRightClickEvent_GetImageSrc",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetImageSrc();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_GetImageSrc(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_GetImageSrc" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetImageSrc();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_SetImageSrc(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "src", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetImageSrc",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetImageSrc((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_SetImageSrc(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "src", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetImageSrc",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_SetImageSrc" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetImageSrc((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_GetLink(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaRightClickEvent_GetLink",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (arg1)->GetLink();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_GetLink(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_GetLink" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (arg1)->GetLink();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  {
 #if wxUSE_UNICODE
-        resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
+    resultobj = PyUnicode_FromWideChar((&result)->c_str(), (&result)->Len());
 #else
-        resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
+    resultobj = PyString_FromStringAndSize((&result)->c_str(), (&result)->Len());
 #endif
-    }
-    return resultobj;
-    fail:
-    return NULL;
+  }
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_SetLink(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    wxString *arg2 = 0 ;
-    bool temp2 = false ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "link", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetLink",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = wxString_in_helper(obj1);
-        if (arg2 == NULL) SWIG_fail;
-        temp2 = true;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetLink((wxString const &)*arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return resultobj;
-    fail:
-    {
-        if (temp2)
-        delete arg2;
-    }
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_SetLink(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  wxString *arg2 = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  bool temp2 = false ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "link", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetLink",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_SetLink" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    arg2 = wxString_in_helper(obj1);
+    if (arg2 == NULL) SWIG_fail;
+    temp2 = true;
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetLink((wxString const &)*arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return resultobj;
+fail:
+  {
+    if (temp2)
+    delete arg2;
+  }
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_GetContext(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    int result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:MozillaRightClickEvent_GetContext",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (int)(arg1)->GetContext();
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    {
-        resultobj = SWIG_From_int(static_cast<int >(result)); 
-    }
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_GetContext(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  int result;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject *swig_obj[1] ;
+  
+  if (!args) SWIG_fail;
+  swig_obj[0] = args;
+  res1 = SWIG_ConvertPtr(swig_obj[0], &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_GetContext" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (int)(arg1)->GetContext();
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_From_int(static_cast< int >(result));
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_MozillaRightClickEvent_SetContext(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    int arg2 ;
-    PyObject * obj0 = 0 ;
-    PyObject * obj1 = 0 ;
-    char *kwnames[] = {
-        (char *) "self",(char *) "context", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetContext",kwnames,&obj0,&obj1)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        arg2 = static_cast<int >(SWIG_As_int(obj1)); 
-        if (SWIG_arg_fail(2)) SWIG_fail;
-    }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        (arg1)->SetContext(arg2);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *_wrap_MozillaRightClickEvent_SetContext(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
+  int arg2 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  int val2 ;
+  int ecode2 = 0 ;
+  PyObject * obj0 = 0 ;
+  PyObject * obj1 = 0 ;
+  char *  kwnames[] = {
+    (char *) "self",(char *) "context", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"OO:MozillaRightClickEvent_SetContext",kwnames,&obj0,&obj1)) SWIG_fail;
+  res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxMozillaRightClickEvent, 0 |  0 );
+  if (!SWIG_IsOK(res1)) {
+    SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "MozillaRightClickEvent_SetContext" "', expected argument " "1"" of type '" "wxMozillaRightClickEvent *""'"); 
+  }
+  arg1 = reinterpret_cast< wxMozillaRightClickEvent * >(argp1);
+  ecode2 = SWIG_AsVal_int(obj1, &val2);
+  if (!SWIG_IsOK(ecode2)) {
+    SWIG_exception_fail(SWIG_ArgError(ecode2), "in method '" "MozillaRightClickEvent_SetContext" "', expected argument " "2"" of type '" "int""'");
+  } 
+  arg2 = static_cast< int >(val2);
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    (arg1)->SetContext(arg2);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_Py_Void();
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_new_MozillaRightClickEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxWindow *arg1 = (wxWindow *) NULL ;
-    wxMozillaRightClickEvent *result;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "win", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaRightClickEvent",kwnames,&obj0)) goto fail;
-    if (obj0) {
-        SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxWindow, SWIG_POINTER_EXCEPTION | 0);
-        if (SWIG_arg_fail(1)) SWIG_fail;
+SWIGINTERN PyObject *_wrap_new_MozillaRightClickEvent(PyObject *SWIGUNUSEDPARM(self), PyObject *args, PyObject *kwargs) {
+  PyObject *resultobj = 0;
+  wxWindow *arg1 = (wxWindow *) NULL ;
+  wxMozillaRightClickEvent *result = 0 ;
+  void *argp1 = 0 ;
+  int res1 = 0 ;
+  PyObject * obj0 = 0 ;
+  char *  kwnames[] = {
+    (char *) "win", NULL 
+  };
+  
+  if (!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"|O:new_MozillaRightClickEvent",kwnames,&obj0)) SWIG_fail;
+  if (obj0) {
+    res1 = SWIG_ConvertPtr(obj0, &argp1,SWIGTYPE_p_wxWindow, 0 |  0 );
+    if (!SWIG_IsOK(res1)) {
+      SWIG_exception_fail(SWIG_ArgError(res1), "in method '" "new_MozillaRightClickEvent" "', expected argument " "1"" of type '" "wxWindow *""'"); 
     }
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        result = (wxMozillaRightClickEvent *)new wxMozillaRightClickEvent(arg1);
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    resultobj = SWIG_NewPointerObj((void*)(result), SWIGTYPE_p_wxMozillaRightClickEvent, 1);
-    return resultobj;
-    fail:
-    return NULL;
+    arg1 = reinterpret_cast< wxWindow * >(argp1);
+  }
+  {
+    PyThreadState* __tstate = wxPyBeginAllowThreads();
+    result = (wxMozillaRightClickEvent *)new wxMozillaRightClickEvent(arg1);
+    wxPyEndAllowThreads(__tstate);
+    if (PyErr_Occurred()) SWIG_fail;
+  }
+  resultobj = SWIG_NewPointerObj(SWIG_as_voidptr(result), SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_NEW |  0 );
+  return resultobj;
+fail:
+  return NULL;
 }
 
 
-static PyObject *_wrap_delete_MozillaRightClickEvent(PyObject *, PyObject *args, PyObject *kwargs) {
-    PyObject *resultobj = NULL;
-    wxMozillaRightClickEvent *arg1 = (wxMozillaRightClickEvent *) 0 ;
-    PyObject * obj0 = 0 ;
-    char *kwnames[] = {
-        (char *) "self", NULL 
-    };
-    
-    if(!PyArg_ParseTupleAndKeywords(args,kwargs,(char *)"O:delete_MozillaRightClickEvent",kwnames,&obj0)) goto fail;
-    SWIG_Python_ConvertPtr(obj0, (void **)&arg1, SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_POINTER_EXCEPTION | 0);
-    if (SWIG_arg_fail(1)) SWIG_fail;
-    {
-        PyThreadState* __tstate = wxPyBeginAllowThreads();
-        delete arg1;
-        
-        wxPyEndAllowThreads(__tstate);
-        if (PyErr_Occurred()) SWIG_fail;
-    }
-    Py_INCREF(Py_None); resultobj = Py_None;
-    return resultobj;
-    fail:
-    return NULL;
+SWIGINTERN PyObject *MozillaRightClickEvent_swigregister(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  PyObject *obj;
+  if (!SWIG_Python_UnpackTuple(args,(char*)"swigregister", 1, 1,&obj)) return NULL;
+  SWIG_TypeNewClientData(SWIGTYPE_p_wxMozillaRightClickEvent, SWIG_NewClientData(obj));
+  return SWIG_Py_Void();
 }
 
-
-static PyObject * MozillaRightClickEvent_swigregister(PyObject *, PyObject *args) {
-    PyObject *obj;
-    if (!PyArg_ParseTuple(args,(char*)"O", &obj)) return NULL;
-    SWIG_TypeClientData(SWIGTYPE_p_wxMozillaRightClickEvent, obj);
-    Py_INCREF(obj);
-    return Py_BuildValue((char *)"");
+SWIGINTERN PyObject *MozillaRightClickEvent_swiginit(PyObject *SWIGUNUSEDPARM(self), PyObject *args) {
+  return SWIG_Python_InitShadowInstance(args);
 }
+
 static PyMethodDef SwigMethods[] = {
 	 { (char *)"new_MozillaBrowser", (PyCFunction) _wrap_new_MozillaBrowser, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_Create", (PyCFunction) _wrap_MozillaBrowser_Create, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_LoadURL", (PyCFunction) _wrap_MozillaBrowser_LoadURL, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_GetURL", (PyCFunction) _wrap_MozillaBrowser_GetURL, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBrowser_GetURL", (PyCFunction)_wrap_MozillaBrowser_GetURL, METH_O, NULL},
 	 { (char *)"MozillaBrowser_SavePage", (PyCFunction) _wrap_MozillaBrowser_SavePage, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_IsBusy", (PyCFunction) _wrap_MozillaBrowser_IsBusy, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_GoBack", (PyCFunction) _wrap_MozillaBrowser_GoBack, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_CanGoBack", (PyCFunction) _wrap_MozillaBrowser_CanGoBack, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_GoForward", (PyCFunction) _wrap_MozillaBrowser_GoForward, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_CanGoForward", (PyCFunction) _wrap_MozillaBrowser_CanGoForward, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_Stop", (PyCFunction) _wrap_MozillaBrowser_Stop, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_Reload", (PyCFunction) _wrap_MozillaBrowser_Reload, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBrowser_IsBusy", (PyCFunction)_wrap_MozillaBrowser_IsBusy, METH_O, NULL},
+	 { (char *)"MozillaBrowser_GoBack", (PyCFunction)_wrap_MozillaBrowser_GoBack, METH_O, NULL},
+	 { (char *)"MozillaBrowser_CanGoBack", (PyCFunction)_wrap_MozillaBrowser_CanGoBack, METH_O, NULL},
+	 { (char *)"MozillaBrowser_GoForward", (PyCFunction)_wrap_MozillaBrowser_GoForward, METH_O, NULL},
+	 { (char *)"MozillaBrowser_CanGoForward", (PyCFunction)_wrap_MozillaBrowser_CanGoForward, METH_O, NULL},
+	 { (char *)"MozillaBrowser_Stop", (PyCFunction)_wrap_MozillaBrowser_Stop, METH_O, NULL},
+	 { (char *)"MozillaBrowser_Reload", (PyCFunction)_wrap_MozillaBrowser_Reload, METH_O, NULL},
 	 { (char *)"MozillaBrowser_Find", (PyCFunction) _wrap_MozillaBrowser_Find, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_FindNext", (PyCFunction) _wrap_MozillaBrowser_FindNext, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_GetStatus", (PyCFunction) _wrap_MozillaBrowser_GetStatus, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_GetSelection", (PyCFunction) _wrap_MozillaBrowser_GetSelection, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_Copy", (PyCFunction) _wrap_MozillaBrowser_Copy, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_SelectAll", (PyCFunction) _wrap_MozillaBrowser_SelectAll, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_SelectNone", (PyCFunction) _wrap_MozillaBrowser_SelectNone, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_UpdateBaseURI", (PyCFunction) _wrap_MozillaBrowser_UpdateBaseURI, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBrowser_FindNext", (PyCFunction)_wrap_MozillaBrowser_FindNext, METH_O, NULL},
+	 { (char *)"MozillaBrowser_GetStatus", (PyCFunction)_wrap_MozillaBrowser_GetStatus, METH_O, NULL},
+	 { (char *)"MozillaBrowser_GetSelection", (PyCFunction)_wrap_MozillaBrowser_GetSelection, METH_O, NULL},
+	 { (char *)"MozillaBrowser_Copy", (PyCFunction)_wrap_MozillaBrowser_Copy, METH_O, NULL},
+	 { (char *)"MozillaBrowser_SelectAll", (PyCFunction)_wrap_MozillaBrowser_SelectAll, METH_O, NULL},
+	 { (char *)"MozillaBrowser_SelectNone", (PyCFunction)_wrap_MozillaBrowser_SelectNone, METH_O, NULL},
+	 { (char *)"MozillaBrowser_UpdateBaseURI", (PyCFunction)_wrap_MozillaBrowser_UpdateBaseURI, METH_O, NULL},
 	 { (char *)"MozillaBrowser_MakeEditable", (PyCFunction) _wrap_MozillaBrowser_MakeEditable, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_InsertHTML", (PyCFunction) _wrap_MozillaBrowser_InsertHTML, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_IsEditable", (PyCFunction) _wrap_MozillaBrowser_IsEditable, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBrowser_IsEditable", (PyCFunction)_wrap_MozillaBrowser_IsEditable, METH_O, NULL},
 	 { (char *)"MozillaBrowser_EditCommand", (PyCFunction) _wrap_MozillaBrowser_EditCommand, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_GetCommandState", (PyCFunction) _wrap_MozillaBrowser_GetCommandState, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_GetStateAttribute", (PyCFunction) _wrap_MozillaBrowser_GetStateAttribute, METH_VARARGS | METH_KEYWORDS, NULL},
@@ -5829,98 +6832,96 @@ static PyMethodDef SwigMethods[] = {
 	 { (char *)"MozillaBrowser_GetElementAttribute", (PyCFunction) _wrap_MozillaBrowser_GetElementAttribute, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_SetElementAttribute", (PyCFunction) _wrap_MozillaBrowser_SetElementAttribute, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_SetPage", (PyCFunction) _wrap_MozillaBrowser_SetPage, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBrowser_GetPage", (PyCFunction) _wrap_MozillaBrowser_GetPage, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBrowser_GetPage", (PyCFunction)_wrap_MozillaBrowser_GetPage, METH_O, NULL},
 	 { (char *)"MozillaBrowser_SetZoom", (PyCFunction) _wrap_MozillaBrowser_SetZoom, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaBrowser", (PyCFunction) _wrap_delete_MozillaBrowser, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBrowser_swigregister", MozillaBrowser_swigregister, METH_VARARGS, NULL},
+	 { (char *)"MozillaBrowser_swiginit", MozillaBrowser_swiginit, METH_VARARGS, NULL},
 	 { (char *)"new_MozillaWindow", (PyCFunction) _wrap_new_MozillaWindow, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaWindow_Mozilla_set", (PyCFunction) _wrap_MozillaWindow_Mozilla_set, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaWindow_Mozilla_get", (PyCFunction) _wrap_MozillaWindow_Mozilla_get, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaWindow", (PyCFunction) _wrap_delete_MozillaWindow, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaWindow_Mozilla_set", _wrap_MozillaWindow_Mozilla_set, METH_VARARGS, NULL},
+	 { (char *)"MozillaWindow_Mozilla_get", (PyCFunction)_wrap_MozillaWindow_Mozilla_get, METH_O, NULL},
 	 { (char *)"MozillaWindow_swigregister", MozillaWindow_swigregister, METH_VARARGS, NULL},
+	 { (char *)"MozillaWindow_swiginit", MozillaWindow_swiginit, METH_VARARGS, NULL},
 	 { (char *)"MozillaSettings_SetProfilePath", (PyCFunction) _wrap_MozillaSettings_SetProfilePath, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaSettings_GetProfilePath", (PyCFunction) _wrap_MozillaSettings_GetProfilePath, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaSettings_GetProfilePath", (PyCFunction)_wrap_MozillaSettings_GetProfilePath, METH_NOARGS, NULL},
 	 { (char *)"MozillaSettings_SetMozillaPath", (PyCFunction) _wrap_MozillaSettings_SetMozillaPath, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaSettings_GetMozillaPath", (PyCFunction) _wrap_MozillaSettings_GetMozillaPath, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaSettings_GetMozillaPath", (PyCFunction)_wrap_MozillaSettings_GetMozillaPath, METH_NOARGS, NULL},
 	 { (char *)"MozillaSettings_SetBoolPref", (PyCFunction) _wrap_MozillaSettings_SetBoolPref, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaSettings_GetBoolPref", (PyCFunction) _wrap_MozillaSettings_GetBoolPref, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaSettings_SetStrPref", (PyCFunction) _wrap_MozillaSettings_SetStrPref, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaSettings_GetStrPref", (PyCFunction) _wrap_MozillaSettings_GetStrPref, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaSettings_SetIntPref", (PyCFunction) _wrap_MozillaSettings_SetIntPref, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaSettings_GetIntPref", (PyCFunction) _wrap_MozillaSettings_GetIntPref, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaSettings_SavePrefs", (PyCFunction) _wrap_MozillaSettings_SavePrefs, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"new_MozillaSettings", (PyCFunction) _wrap_new_MozillaSettings, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaSettings", (PyCFunction) _wrap_delete_MozillaSettings, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaSettings_SavePrefs", (PyCFunction)_wrap_MozillaSettings_SavePrefs, METH_NOARGS, NULL},
 	 { (char *)"MozillaSettings_swigregister", MozillaSettings_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaBeforeLoadEvent_GetURL", (PyCFunction) _wrap_MozillaBeforeLoadEvent_GetURL, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBeforeLoadEvent_GetURL", (PyCFunction)_wrap_MozillaBeforeLoadEvent_GetURL, METH_O, NULL},
 	 { (char *)"MozillaBeforeLoadEvent_SetURL", (PyCFunction) _wrap_MozillaBeforeLoadEvent_SetURL, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBeforeLoadEvent_Cancel", (PyCFunction) _wrap_MozillaBeforeLoadEvent_Cancel, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaBeforeLoadEvent_IsCancelled", (PyCFunction) _wrap_MozillaBeforeLoadEvent_IsCancelled, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBeforeLoadEvent_Cancel", (PyCFunction)_wrap_MozillaBeforeLoadEvent_Cancel, METH_O, NULL},
+	 { (char *)"MozillaBeforeLoadEvent_IsCancelled", (PyCFunction)_wrap_MozillaBeforeLoadEvent_IsCancelled, METH_O, NULL},
 	 { (char *)"new_MozillaBeforeLoadEvent", (PyCFunction) _wrap_new_MozillaBeforeLoadEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaBeforeLoadEvent", (PyCFunction) _wrap_delete_MozillaBeforeLoadEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaBeforeLoadEvent_swigregister", MozillaBeforeLoadEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaLinkChangedEvent_GetNewURL", (PyCFunction) _wrap_MozillaLinkChangedEvent_GetNewURL, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaLinkChangedEvent_CanGoBack", (PyCFunction) _wrap_MozillaLinkChangedEvent_CanGoBack, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaLinkChangedEvent_CanGoForward", (PyCFunction) _wrap_MozillaLinkChangedEvent_CanGoForward, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaBeforeLoadEvent_swiginit", MozillaBeforeLoadEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaLinkChangedEvent_GetNewURL", (PyCFunction)_wrap_MozillaLinkChangedEvent_GetNewURL, METH_O, NULL},
+	 { (char *)"MozillaLinkChangedEvent_CanGoBack", (PyCFunction)_wrap_MozillaLinkChangedEvent_CanGoBack, METH_O, NULL},
+	 { (char *)"MozillaLinkChangedEvent_CanGoForward", (PyCFunction)_wrap_MozillaLinkChangedEvent_CanGoForward, METH_O, NULL},
 	 { (char *)"MozillaLinkChangedEvent_SetNewURL", (PyCFunction) _wrap_MozillaLinkChangedEvent_SetNewURL, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaLinkChangedEvent_SetCanGoBack", (PyCFunction) _wrap_MozillaLinkChangedEvent_SetCanGoBack, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaLinkChangedEvent_SetCanGoForward", (PyCFunction) _wrap_MozillaLinkChangedEvent_SetCanGoForward, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaLinkChangedEvent", (PyCFunction) _wrap_new_MozillaLinkChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaLinkChangedEvent", (PyCFunction) _wrap_delete_MozillaLinkChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaLinkChangedEvent_swigregister", MozillaLinkChangedEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaStateChangedEvent_GetState", (PyCFunction) _wrap_MozillaStateChangedEvent_GetState, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaLinkChangedEvent_swiginit", MozillaLinkChangedEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaStateChangedEvent_GetState", (PyCFunction)_wrap_MozillaStateChangedEvent_GetState, METH_O, NULL},
 	 { (char *)"MozillaStateChangedEvent_SetState", (PyCFunction) _wrap_MozillaStateChangedEvent_SetState, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaStateChangedEvent_GetURL", (PyCFunction) _wrap_MozillaStateChangedEvent_GetURL, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaStateChangedEvent_GetURL", (PyCFunction)_wrap_MozillaStateChangedEvent_GetURL, METH_O, NULL},
 	 { (char *)"MozillaStateChangedEvent_SetURL", (PyCFunction) _wrap_MozillaStateChangedEvent_SetURL, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaStateChangedEvent", (PyCFunction) _wrap_new_MozillaStateChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaStateChangedEvent", (PyCFunction) _wrap_delete_MozillaStateChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaStateChangedEvent_swigregister", MozillaStateChangedEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaSecurityChangedEvent_GetSecurity", (PyCFunction) _wrap_MozillaSecurityChangedEvent_GetSecurity, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaStateChangedEvent_swiginit", MozillaStateChangedEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaSecurityChangedEvent_GetSecurity", (PyCFunction)_wrap_MozillaSecurityChangedEvent_GetSecurity, METH_O, NULL},
 	 { (char *)"MozillaSecurityChangedEvent_SetSecurity", (PyCFunction) _wrap_MozillaSecurityChangedEvent_SetSecurity, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaSecurityChangedEvent", (PyCFunction) _wrap_new_MozillaSecurityChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaSecurityChangedEvent", (PyCFunction) _wrap_delete_MozillaSecurityChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaSecurityChangedEvent_swigregister", MozillaSecurityChangedEvent_swigregister, METH_VARARGS, NULL},
+	 { (char *)"MozillaSecurityChangedEvent_swiginit", MozillaSecurityChangedEvent_swiginit, METH_VARARGS, NULL},
 	 { (char *)"new_MozillaLoadCompleteEvent", (PyCFunction) _wrap_new_MozillaLoadCompleteEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaLoadCompleteEvent", (PyCFunction) _wrap_delete_MozillaLoadCompleteEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaLoadCompleteEvent_swigregister", MozillaLoadCompleteEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaStatusChangedEvent_GetStatusText", (PyCFunction) _wrap_MozillaStatusChangedEvent_GetStatusText, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaStatusChangedEvent_IsBusy", (PyCFunction) _wrap_MozillaStatusChangedEvent_IsBusy, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaLoadCompleteEvent_swiginit", MozillaLoadCompleteEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaStatusChangedEvent_GetStatusText", (PyCFunction)_wrap_MozillaStatusChangedEvent_GetStatusText, METH_O, NULL},
+	 { (char *)"MozillaStatusChangedEvent_IsBusy", (PyCFunction)_wrap_MozillaStatusChangedEvent_IsBusy, METH_O, NULL},
 	 { (char *)"MozillaStatusChangedEvent_SetStatusText", (PyCFunction) _wrap_MozillaStatusChangedEvent_SetStatusText, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaStatusChangedEvent_SetBusy", (PyCFunction) _wrap_MozillaStatusChangedEvent_SetBusy, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaStatusChangedEvent", (PyCFunction) _wrap_new_MozillaStatusChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaStatusChangedEvent", (PyCFunction) _wrap_delete_MozillaStatusChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaStatusChangedEvent_swigregister", MozillaStatusChangedEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaTitleChangedEvent_GetTitle", (PyCFunction) _wrap_MozillaTitleChangedEvent_GetTitle, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaStatusChangedEvent_swiginit", MozillaStatusChangedEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaTitleChangedEvent_GetTitle", (PyCFunction)_wrap_MozillaTitleChangedEvent_GetTitle, METH_O, NULL},
 	 { (char *)"MozillaTitleChangedEvent_SetTitle", (PyCFunction) _wrap_MozillaTitleChangedEvent_SetTitle, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaTitleChangedEvent", (PyCFunction) _wrap_new_MozillaTitleChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaTitleChangedEvent", (PyCFunction) _wrap_delete_MozillaTitleChangedEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaTitleChangedEvent_swigregister", MozillaTitleChangedEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaProgressEvent_GetSelfCurrentProgress", (PyCFunction) _wrap_MozillaProgressEvent_GetSelfCurrentProgress, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaTitleChangedEvent_swiginit", MozillaTitleChangedEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaProgressEvent_GetSelfCurrentProgress", (PyCFunction)_wrap_MozillaProgressEvent_GetSelfCurrentProgress, METH_O, NULL},
 	 { (char *)"MozillaProgressEvent_SetSelfCurrentProgress", (PyCFunction) _wrap_MozillaProgressEvent_SetSelfCurrentProgress, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaProgressEvent_GetSelfMaxProgress", (PyCFunction) _wrap_MozillaProgressEvent_GetSelfMaxProgress, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaProgressEvent_GetSelfMaxProgress", (PyCFunction)_wrap_MozillaProgressEvent_GetSelfMaxProgress, METH_O, NULL},
 	 { (char *)"MozillaProgressEvent_SetSelfMaxProgress", (PyCFunction) _wrap_MozillaProgressEvent_SetSelfMaxProgress, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaProgressEvent_GetTotalCurrentProgress", (PyCFunction) _wrap_MozillaProgressEvent_GetTotalCurrentProgress, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaProgressEvent_GetTotalCurrentProgress", (PyCFunction)_wrap_MozillaProgressEvent_GetTotalCurrentProgress, METH_O, NULL},
 	 { (char *)"MozillaProgressEvent_SetTotalCurrentProgress", (PyCFunction) _wrap_MozillaProgressEvent_SetTotalCurrentProgress, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaProgressEvent_GetTotalMaxProgress", (PyCFunction) _wrap_MozillaProgressEvent_GetTotalMaxProgress, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaProgressEvent_GetTotalMaxProgress", (PyCFunction)_wrap_MozillaProgressEvent_GetTotalMaxProgress, METH_O, NULL},
 	 { (char *)"MozillaProgressEvent_SetTotalMaxProgress", (PyCFunction) _wrap_MozillaProgressEvent_SetTotalMaxProgress, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaProgressEvent", (PyCFunction) _wrap_new_MozillaProgressEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaProgressEvent", (PyCFunction) _wrap_delete_MozillaProgressEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaProgressEvent_swigregister", MozillaProgressEvent_swigregister, METH_VARARGS, NULL},
-	 { (char *)"MozillaRightClickEvent_IsBusy", (PyCFunction) _wrap_MozillaRightClickEvent_IsBusy, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaProgressEvent_swiginit", MozillaProgressEvent_swiginit, METH_VARARGS, NULL},
+	 { (char *)"MozillaRightClickEvent_IsBusy", (PyCFunction)_wrap_MozillaRightClickEvent_IsBusy, METH_O, NULL},
 	 { (char *)"MozillaRightClickEvent_SetBusy", (PyCFunction) _wrap_MozillaRightClickEvent_SetBusy, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaRightClickEvent_GetBackgroundImageSrc", (PyCFunction) _wrap_MozillaRightClickEvent_GetBackgroundImageSrc, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaRightClickEvent_GetBackgroundImageSrc", (PyCFunction)_wrap_MozillaRightClickEvent_GetBackgroundImageSrc, METH_O, NULL},
 	 { (char *)"MozillaRightClickEvent_SetBackgroundImageSrc", (PyCFunction) _wrap_MozillaRightClickEvent_SetBackgroundImageSrc, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaRightClickEvent_GetText", (PyCFunction) _wrap_MozillaRightClickEvent_GetText, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaRightClickEvent_GetText", (PyCFunction)_wrap_MozillaRightClickEvent_GetText, METH_O, NULL},
 	 { (char *)"MozillaRightClickEvent_SetText", (PyCFunction) _wrap_MozillaRightClickEvent_SetText, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaRightClickEvent_GetImageSrc", (PyCFunction) _wrap_MozillaRightClickEvent_GetImageSrc, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaRightClickEvent_GetImageSrc", (PyCFunction)_wrap_MozillaRightClickEvent_GetImageSrc, METH_O, NULL},
 	 { (char *)"MozillaRightClickEvent_SetImageSrc", (PyCFunction) _wrap_MozillaRightClickEvent_SetImageSrc, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaRightClickEvent_GetLink", (PyCFunction) _wrap_MozillaRightClickEvent_GetLink, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaRightClickEvent_GetLink", (PyCFunction)_wrap_MozillaRightClickEvent_GetLink, METH_O, NULL},
 	 { (char *)"MozillaRightClickEvent_SetLink", (PyCFunction) _wrap_MozillaRightClickEvent_SetLink, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"MozillaRightClickEvent_GetContext", (PyCFunction) _wrap_MozillaRightClickEvent_GetContext, METH_VARARGS | METH_KEYWORDS, NULL},
+	 { (char *)"MozillaRightClickEvent_GetContext", (PyCFunction)_wrap_MozillaRightClickEvent_GetContext, METH_O, NULL},
 	 { (char *)"MozillaRightClickEvent_SetContext", (PyCFunction) _wrap_MozillaRightClickEvent_SetContext, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"new_MozillaRightClickEvent", (PyCFunction) _wrap_new_MozillaRightClickEvent, METH_VARARGS | METH_KEYWORDS, NULL},
-	 { (char *)"delete_MozillaRightClickEvent", (PyCFunction) _wrap_delete_MozillaRightClickEvent, METH_VARARGS | METH_KEYWORDS, NULL},
 	 { (char *)"MozillaRightClickEvent_swigregister", MozillaRightClickEvent_swigregister, METH_VARARGS, NULL},
+	 { (char *)"MozillaRightClickEvent_swiginit", MozillaRightClickEvent_swiginit, METH_VARARGS, NULL},
 	 { NULL, NULL, 0, NULL }
 };
 
@@ -5951,314 +6952,377 @@ static void *_p_wxSplashScreenTo_p_wxFra
 static void *_p_wxMDIParentFrameTo_p_wxFrame(void *x) {
     return (void *)((wxFrame *)  ((wxMDIParentFrame *) x));
 }
-static void *_p_wxLayoutConstraintsTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxLayoutConstraints *) x));
+static void *_p_wxUpdateUIEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxUpdateUIEvent *) x));
 }
-static void *_p_wxQueryLayoutInfoEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxQueryLayoutInfoEvent *) x));
+static void *_p_wxPreviewCanvasTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxScrolledWindow *) ((wxPreviewCanvas *) x));
 }
-static void *_p_wxPreviewFrameTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxPreviewFrame *) x));
+static void *_p_wxEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxEvent *) x));
+}
+static void *_p_wxFindDialogEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxFindDialogEvent *) x));
+}
+static void *_p_wxInitDialogEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxInitDialogEvent *) x));
+}
+static void *_p_wxIndividualLayoutConstraintTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxIndividualLayoutConstraint *) x));
 }
 static void *_p_wxPyPreviewFrameTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *)(wxPreviewFrame *) ((wxPyPreviewFrame *) x));
 }
-static void *_p_wxGBSizerItemTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizerItem *) ((wxGBSizerItem *) x));
+static void *_p_wxPreviewFrameTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxPreviewFrame *) x));
 }
-static void *_p_wxSizerItemTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxSizerItem *) x));
+static void *_p_wxMenuItemTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxMenuItem *) x));
+}
+static void *_p_wxImageTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxImage *) x));
+}
+static void *_p_wxPySizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *) ((wxPySizer *) x));
+}
+static void *_p_wxPyTaskBarIconTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyTaskBarIcon *) x));
+}
+static void *_p_wxLayoutAlgorithmTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxLayoutAlgorithm *) x));
+}
+static void *_p_wxPyAppTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyApp *) x));
+}
+static void *_p_wxMozillaBrowserTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxMozillaBrowser *) x));
+}
+static void *_p_wxPyPreviewControlBarTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPreviewControlBar *) ((wxPyPreviewControlBar *) x));
+}
+static void *_p_wxPreviewControlBarTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxPreviewControlBar *) x));
+}
+static void *_p_wxFindReplaceDataTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxFindReplaceData *) x));
+}
+static void *_p_wxValidatorTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxValidator *) x));
+}
+static void *_p_wxPyValidatorTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxValidator *) ((wxPyValidator *) x));
+}
+static void *_p_wxEraseEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxEraseEvent *) x));
+}
+static void *_p_wxMouseEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxMouseEvent *) x));
+}
+static void *_p_wxCloseEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxCloseEvent *) x));
 }
 static void *_p_wxScrollEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxScrollEvent *) x));
 }
-static void *_p_wxIndividualLayoutConstraintTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxIndividualLayoutConstraint *) x));
+static void *_p_wxPrintDialogDataTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPrintDialogData *) x));
 }
-static void *_p_wxStaticBoxSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *)(wxBoxSizer *) ((wxStaticBoxSizer *) x));
+static void *_p_wxPageSetupDialogDataTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPageSetupDialogData *) x));
 }
-static void *_p_wxBoxSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *) ((wxBoxSizer *) x));
+static void *_p_wxPrinterTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPrinter *) x));
 }
-static void *_p_wxSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxSizer *) x));
+static void *_p_wxControlWithItemsTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxControl *) ((wxControlWithItems *) x));
 }
-static void *_p_wxGridBagSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *)(wxGridSizer *)(wxFlexGridSizer *) ((wxGridBagSizer *) x));
+static void *_p_wxSystemOptionsTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxSystemOptions *) x));
 }
-static void *_p_wxFileHistoryTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxFileHistory *) x));
+static void *_p_wxGridSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *) ((wxGridSizer *) x));
 }
-static void *_p_wxUpdateUIEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxUpdateUIEvent *) x));
+static void *_p_wxFlexGridSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *)(wxGridSizer *) ((wxFlexGridSizer *) x));
 }
-static void *_p_wxPyPanelTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxPyPanel *) x));
+static void *_p_wxAcceleratorTableTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxAcceleratorTable *) x));
 }
-static void *_p_wxEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxEvent *) x));
+static void *_p_wxControlTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxControl *) x));
 }
-static void *_p_wxFontDataTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxFontData *) x));
+static void *_p_wxPyProcessTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyProcess *) x));
+}
+static void *_p_wxColourDataTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxColourData *) x));
+}
+static void *_p_wxActivateEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxActivateEvent *) x));
+}
+static void *_p_wxMoveEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxMoveEvent *) x));
 }
-static void *_p_wxPrintDataTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPrintData *) x));
+static void *_p_wxSizeEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxSizeEvent *) x));
 }
-static void *_p_wxFlexGridSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *)(wxGridSizer *) ((wxFlexGridSizer *) x));
+static void *_p_wxIconizeEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxIconizeEvent *) x));
 }
-static void *_p_wxGridSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *) ((wxGridSizer *) x));
+static void *_p_wxMaximizeEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxMaximizeEvent *) x));
 }
-static void *_p_wxInitDialogEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxInitDialogEvent *) x));
+static void *_p_wxQueryNewPaletteEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxQueryNewPaletteEvent *) x));
 }
-static void *_p_wxLayoutAlgorithmTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxLayoutAlgorithm *) x));
+static void *_p_wxWindowCreateEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxWindowCreateEvent *) x));
 }
-static void *_p_wxPyTaskBarIconTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyTaskBarIcon *) x));
+static void *_p_wxIdleEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxIdleEvent *) x));
 }
-static void *_p_wxFindDialogEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxFindDialogEvent *) x));
+static void *_p_wxDateEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxDateEvent *) x));
 }
-static void *_p_wxPaintEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxPaintEvent *) x));
+static void *_p_wxMozillaLoadCompleteEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaLoadCompleteEvent *) x));
 }
-static void *_p_wxNcPaintEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxNcPaintEvent *) x));
+static void *_p_wxCalculateLayoutEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxCalculateLayoutEvent *) x));
 }
-static void *_p_wxPaletteChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxPaletteChangedEvent *) x));
+static void *_p_wxMouseCaptureLostEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxMouseCaptureLostEvent *) x));
 }
-static void *_p_wxDisplayChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxDisplayChangedEvent *) x));
+static void *_p_wxPyTimerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyTimer *) x));
 }
-static void *_p_wxMouseCaptureChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxMouseCaptureChangedEvent *) x));
+static void *_p_wxPyPrintoutTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPyPrintout *) x));
 }
-static void *_p_wxSysColourChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxSysColourChangedEvent *) x));
+static void *_p_wxMDIChildFrameTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMDIChildFrame *) x));
 }
-static void *_p_wxPreviewCanvasTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxScrolledWindow *) ((wxPreviewCanvas *) x));
+static void *_p_wxStdDialogButtonSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *)(wxBoxSizer *) ((wxStdDialogButtonSizer *) x));
 }
-static void *_p_wxMozillaBeforeLoadEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaBeforeLoadEvent *) x));
+static void *_p_wxKeyEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxKeyEvent *) x));
 }
-static void *_p_wxMozillaLinkChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaLinkChangedEvent *) x));
+static void *_p_wxNavigationKeyEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxNavigationKeyEvent *) x));
 }
-static void *_p_wxMozillaStateChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaStateChangedEvent *) x));
+static void *_p_wxWindowDestroyEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxWindowDestroyEvent *) x));
 }
-static void *_p_wxMozillaSecurityChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaSecurityChangedEvent *) x));
+static void *_p_wxSashEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxSashEvent *) x));
 }
-static void *_p_wxMozillaStatusChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaStatusChangedEvent *) x));
+static void *_p_wxSimpleHtmlListBoxTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *)(wxPyHtmlListBox *) ((wxSimpleHtmlListBox *) x));
 }
-static void *_p_wxMozillaTitleChangedEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaTitleChangedEvent *) x));
+static void *_p_wxPyHtmlListBoxTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *) ((wxPyHtmlListBox *) x));
 }
-static void *_p_wxControlTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxControl *) x));
+static void *_p_wxPyVListBoxTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPyVScrolledWindow *) ((wxPyVListBox *) x));
 }
-static void *_p_wxSetCursorEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxSetCursorEvent *) x));
+static void *_p_wxPrintDataTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPrintData *) x));
 }
-static void *_p_wxSplitterEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *)(wxNotifyEvent *) ((wxSplitterEvent *) x));
+static void *_p_wxFontDataTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxFontData *) x));
 }
-static void *_p_wxTimerEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxTimerEvent *) x));
+static void *_p_wxMiniFrameTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMiniFrame *) x));
 }
-static void *_p_wxFSFileTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxFSFile *) x));
+static void *_p_wxFrameTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *) ((wxFrame *) x));
 }
-static void *_p_wxMozillaBrowserTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxMozillaBrowser *) x));
+static void *_p_wxPyPanelTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxPyPanel *) x));
 }
-static void *_p_wxFindReplaceDataTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxFindReplaceData *) x));
+static void *_p_wxQueryLayoutInfoEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxQueryLayoutInfoEvent *) x));
 }
-static void *_p_wxClipboardTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxClipboard *) x));
+static void *_p_wxSplashScreenTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxSplashScreen *) x));
 }
-static void *_p_wxPySizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *) ((wxPySizer *) x));
+static void *_p_wxFileSystemTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxFileSystem *) x));
 }
-static void *_p_wxMDIChildFrameTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMDIChildFrame *) x));
+static void *_p_wxPyPrintPreviewTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxPrintPreview *) ((wxPyPrintPreview *) x));
 }
-static void *_p_wxColourDataTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxColourData *) x));
+static void *_p_wxPrintPreviewTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPrintPreview *) x));
 }
-static void *_p_wxPyEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxPyEvent *) x));
+static void *_p_wxLayoutConstraintsTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxLayoutConstraints *) x));
 }
-static void *_p_wxNotifyEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxNotifyEvent *) x));
+static void *_p_wxSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxSizer *) x));
 }
-static void *_p_wxPyWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxPyWindow *) x));
+static void *_p_wxBoxSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *) ((wxBoxSizer *) x));
 }
-static void *_p_wxMozillaWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMozillaWindow *) x));
+static void *_p_wxStaticBoxSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *)(wxBoxSizer *) ((wxStaticBoxSizer *) x));
 }
-static void *_p_wxSplashScreenTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxSplashScreen *) x));
+static void *_p_wxGridBagSizerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizer *)(wxGridSizer *)(wxFlexGridSizer *) ((wxGridBagSizer *) x));
 }
-static void *_p_wxFileDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFileDialog *) x));
+static void *_p_wxNcPaintEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxNcPaintEvent *) x));
 }
-static void *_p_wxMultiChoiceDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxMultiChoiceDialog *) x));
+static void *_p_wxPaintEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxPaintEvent *) x));
 }
-static void *_p_wxSingleChoiceDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxSingleChoiceDialog *) x));
+static void *_p_wxClipboardTextEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxClipboardTextEvent *) x));
 }
-static void *_p_wxTextEntryDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxTextEntryDialog *) x));
+static void *_p_wxFSFileTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxFSFile *) x));
 }
-static void *_p_wxPasswordEntryDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *)(wxTextEntryDialog *) ((wxPasswordEntryDialog *) x));
+static void *_p_wxClipboardTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxClipboard *) x));
 }
-static void *_p_wxMessageDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxMessageDialog *) x));
+static void *_p_wxPowerEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxPowerEvent *) x));
 }
-static void *_p_wxProgressDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxProgressDialog *) x));
+static void *_p_wxTimerEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxTimerEvent *) x));
 }
-static void *_p_wxFindReplaceDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFindReplaceDialog *) x));
+static void *_p_wxSplitterEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *)(wxNotifyEvent *) ((wxSplitterEvent *) x));
 }
-static void *_p_wxShowEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxShowEvent *) x));
+static void *_p_wxSetCursorEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxSetCursorEvent *) x));
 }
-static void *_p_wxToolTipTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxToolTip *) x));
+static void *_p_wxBusyInfoTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxBusyInfo *) x));
 }
-static void *_p_wxPrinterTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPrinter *) x));
+static void *_p_wxMenuTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxMenu *) x));
 }
-static void *_p_wxMenuItemTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxMenuItem *) x));
+static void *_p_wxGBSizerItemTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxSizerItem *) ((wxGBSizerItem *) x));
 }
-static void *_p_wxDateEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxDateEvent *) x));
+static void *_p_wxSizerItemTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxSizerItem *) x));
 }
-static void *_p_wxIdleEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxIdleEvent *) x));
+static void *_p_wxPrintDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPrintDialog *) x));
 }
-static void *_p_wxWindowCreateEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxWindowCreateEvent *) x));
+static void *_p_wxPageSetupDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxPageSetupDialog *) x));
 }
-static void *_p_wxQueryNewPaletteEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxQueryNewPaletteEvent *) x));
+static void *_p_wxFontDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFontDialog *) x));
 }
-static void *_p_wxMaximizeEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxMaximizeEvent *) x));
+static void *_p_wxDirDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxDirDialog *) x));
 }
-static void *_p_wxIconizeEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxIconizeEvent *) x));
+static void *_p_wxColourDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxColourDialog *) x));
 }
-static void *_p_wxSizeEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxSizeEvent *) x));
+static void *_p_wxDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *) ((wxDialog *) x));
 }
-static void *_p_wxMoveEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxMoveEvent *) x));
+static void *_p_wxNotifyEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxNotifyEvent *) x));
 }
-static void *_p_wxActivateEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxActivateEvent *) x));
+static void *_p_wxPyEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxPyEvent *) x));
 }
-static void *_p_wxMozillaLoadCompleteEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaLoadCompleteEvent *) x));
+static void *_p_wxToolTipTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxToolTip *) x));
 }
-static void *_p_wxPNMHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxPNMHandler *) x));
+static void *_p_wxEvtHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxEvtHandler *) x));
 }
-static void *_p_wxJPEGHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxJPEGHandler *) x));
+static void *_p_wxTGAHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxTGAHandler *) x));
 }
-static void *_p_wxPCXHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxPCXHandler *) x));
+static void *_p_wxTIFFHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxTIFFHandler *) x));
 }
-static void *_p_wxGIFHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxGIFHandler *) x));
+static void *_p_wxXPMHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxXPMHandler *) x));
 }
-static void *_p_wxPNGHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxPNGHandler *) x));
+static void *_p_wxImageHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxImageHandler *) x));
 }
-static void *_p_wxANIHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *)(wxBMPHandler *)(wxICOHandler *)(wxCURHandler *) ((wxANIHandler *) x));
+static void *_p_wxPyImageHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxPyImageHandler *) x));
 }
-static void *_p_wxCURHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *)(wxBMPHandler *)(wxICOHandler *) ((wxCURHandler *) x));
+static void *_p_wxBMPHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxBMPHandler *) x));
 }
 static void *_p_wxICOHandlerTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxImageHandler *)(wxBMPHandler *) ((wxICOHandler *) x));
 }
-static void *_p_wxBMPHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxBMPHandler *) x));
+static void *_p_wxCURHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *)(wxBMPHandler *)(wxICOHandler *) ((wxCURHandler *) x));
+}
+static void *_p_wxANIHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *)(wxBMPHandler *)(wxICOHandler *)(wxCURHandler *) ((wxANIHandler *) x));
 }
-static void *_p_wxPyImageHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxPyImageHandler *) x));
+static void *_p_wxPNGHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxPNGHandler *) x));
 }
-static void *_p_wxImageHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxImageHandler *) x));
+static void *_p_wxGIFHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxGIFHandler *) x));
 }
-static void *_p_wxXPMHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxXPMHandler *) x));
+static void *_p_wxPCXHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxPCXHandler *) x));
 }
-static void *_p_wxTIFFHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxImageHandler *) ((wxTIFFHandler *) x));
+static void *_p_wxJPEGHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxJPEGHandler *) x));
 }
-static void *_p_wxEvtHandlerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxEvtHandler *) x));
+static void *_p_wxPNMHandlerTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxImageHandler *) ((wxPNMHandler *) x));
 }
-static void *_p_wxCalculateLayoutEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxCalculateLayoutEvent *) x));
+static void *_p_wxShowEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxShowEvent *) x));
 }
-static void *_p_wxPyVListBoxTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPyVScrolledWindow *) ((wxPyVListBox *) x));
+static void *_p_wxPyScrolledWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxScrolledWindow *) ((wxPyScrolledWindow *) x));
 }
-static void *_p_wxPyHtmlListBoxTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *) ((wxPyHtmlListBox *) x));
+static void *_p_wxMDIClientWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxMDIClientWindow *) x));
 }
-static void *_p_wxStdDialogButtonSizerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxSizer *)(wxBoxSizer *) ((wxStdDialogButtonSizer *) x));
+static void *_p_wxPyVScrolledWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxPyVScrolledWindow *) x));
 }
-static void *_p_wxAcceleratorTableTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxAcceleratorTable *) x));
+static void *_p_wxTipWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPopupWindow *)(wxPyPopupTransientWindow *) ((wxTipWindow *) x));
 }
-static void *_p_wxMiniFrameTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMiniFrame *) x));
+static void *_p_wxPyPopupTransientWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPopupWindow *) ((wxPyPopupTransientWindow *) x));
 }
-static void *_p_wxImageTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxImage *) x));
+static void *_p_wxPopupWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxPopupWindow *) x));
 }
-static void *_p_wxFrameTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *) ((wxFrame *) x));
+static void *_p_wxSashLayoutWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxSashWindow *) ((wxSashLayoutWindow *) x));
 }
-static void *_p_wxPyPrintoutTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPyPrintout *) x));
+static void *_p_wxSashWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxSashWindow *) x));
 }
-static void *_p_wxScrollWinEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxScrollWinEvent *) x));
+static void *_p_wxSplitterWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxSplitterWindow *) x));
 }
-static void *_p_wxTaskBarIconEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxTaskBarIconEvent *) x));
+static void *_p_wxSplashScreenWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxSplashScreenWindow *) x));
 }
-static void *_p_wxStatusBarTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxStatusBar *) x));
+static void *_p_wxTopLevelWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxTopLevelWindow *) x));
 }
-static void *_p_wxSystemOptionsTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxSystemOptions *) x));
+static void *_p_wxScrolledWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxScrolledWindow *) x));
 }
-static void *_p_wxMDIParentFrameTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMDIParentFrame *) x));
+static void *_p_wxWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *) ((wxWindow *) x));
 }
 static void *_p_wxJoystickEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *) ((wxJoystickEvent *) x));
@@ -6266,161 +7330,116 @@ static void *_p_wxJoystickEventTo_p_wxOb
 static void *_p_wxMozillaRightClickEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *)(wxMouseEvent *) ((wxMozillaRightClickEvent *) x));
 }
-static void *_p_wxWindowDestroyEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxWindowDestroyEvent *) x));
+static void *_p_wxFindReplaceDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFindReplaceDialog *) x));
 }
-static void *_p_wxNavigationKeyEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxNavigationKeyEvent *) x));
+static void *_p_wxProgressDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxProgressDialog *) x));
 }
-static void *_p_wxKeyEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxKeyEvent *) x));
+static void *_p_wxMessageDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxMessageDialog *) x));
 }
-static void *_p_wxWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxWindow *) x));
+static void *_p_wxNumberEntryDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxNumberEntryDialog *) x));
 }
-static void *_p_wxMenuTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxMenu *) x));
+static void *_p_wxPasswordEntryDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *)(wxTextEntryDialog *) ((wxPasswordEntryDialog *) x));
 }
-static void *_p_wxMenuBarTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxMenuBar *) x));
+static void *_p_wxTextEntryDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxTextEntryDialog *) x));
 }
-static void *_p_wxScrolledWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxScrolledWindow *) x));
+static void *_p_wxSingleChoiceDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxSingleChoiceDialog *) x));
 }
-static void *_p_wxTopLevelWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxTopLevelWindow *) x));
+static void *_p_wxMultiChoiceDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxMultiChoiceDialog *) x));
 }
-static void *_p_wxSplashScreenWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxSplashScreenWindow *) x));
+static void *_p_wxFileDialogTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFileDialog *) x));
 }
-static void *_p_wxSplitterWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxSplitterWindow *) x));
+static void *_p_wxFileHistoryTo_p_wxObject(void *x) {
+    return (void *)((wxObject *)  ((wxFileHistory *) x));
 }
-static void *_p_wxSashWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxSashWindow *) x));
+static void *_p_wxMozillaWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMozillaWindow *) x));
 }
-static void *_p_wxSashLayoutWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxSashWindow *) ((wxSashLayoutWindow *) x));
+static void *_p_wxPyWindowTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxPyWindow *) x));
 }
-static void *_p_wxPopupWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxPopupWindow *) x));
+static void *_p_wxMozillaSecurityChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaSecurityChangedEvent *) x));
 }
-static void *_p_wxPyPopupTransientWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPopupWindow *) ((wxPyPopupTransientWindow *) x));
+static void *_p_wxMozillaStateChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaStateChangedEvent *) x));
 }
-static void *_p_wxTipWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPopupWindow *)(wxPyPopupTransientWindow *) ((wxTipWindow *) x));
+static void *_p_wxMozillaLinkChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaLinkChangedEvent *) x));
 }
-static void *_p_wxPyVScrolledWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxPyVScrolledWindow *) x));
+static void *_p_wxMozillaBeforeLoadEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaBeforeLoadEvent *) x));
 }
-static void *_p_wxMDIClientWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxMDIClientWindow *) x));
+static void *_p_wxSysColourChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxSysColourChangedEvent *) x));
 }
-static void *_p_wxPyScrolledWindowTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxScrolledWindow *) ((wxPyScrolledWindow *) x));
+static void *_p_wxMouseCaptureChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxMouseCaptureChangedEvent *) x));
 }
-static void *_p_wxSashEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxSashEvent *) x));
+static void *_p_wxDisplayChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxDisplayChangedEvent *) x));
 }
-static void *_p_wxPrintPreviewTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPrintPreview *) x));
+static void *_p_wxPaletteChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxPaletteChangedEvent *) x));
 }
-static void *_p_wxPyPrintPreviewTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxPrintPreview *) ((wxPyPrintPreview *) x));
+static void *_p_wxMozillaStatusChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaStatusChangedEvent *) x));
 }
-static void *_p_wxPyProcessTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyProcess *) x));
+static void *_p_wxMozillaTitleChangedEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaTitleChangedEvent *) x));
 }
 static void *_p_wxPanelTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxPanel *) x));
 }
-static void *_p_wxDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *) ((wxDialog *) x));
-}
-static void *_p_wxColourDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxColourDialog *) x));
-}
-static void *_p_wxDirDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxDirDialog *) x));
-}
-static void *_p_wxFontDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFontDialog *) x));
-}
-static void *_p_wxPageSetupDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPageSetupDialog *) x));
-}
-static void *_p_wxPrintDialogTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPrintDialog *) x));
-}
-static void *_p_wxFileSystemTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxFileSystem *) x));
+static void *_p_wxTaskBarIconEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxTaskBarIconEvent *) x));
 }
-static void *_p_wxContextMenuEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxContextMenuEvent *) x));
+static void *_p_wxScrollWinEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxScrollWinEvent *) x));
 }
 static void *_p_wxMenuEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *) ((wxMenuEvent *) x));
 }
-static void *_p_wxPyAppTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyApp *) x));
-}
-static void *_p_wxCloseEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxCloseEvent *) x));
-}
-static void *_p_wxMouseEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxMouseEvent *) x));
-}
-static void *_p_wxEraseEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxEraseEvent *) x));
+static void *_p_wxContextMenuEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxContextMenuEvent *) x));
 }
-static void *_p_wxBusyInfoTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxBusyInfo *) x));
+static void *_p_wxCommandEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxCommandEvent *) x));
 }
 static void *_p_wxPyCommandEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxPyCommandEvent *) x));
 }
-static void *_p_wxCommandEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxCommandEvent *) x));
-}
-static void *_p_wxPreviewControlBarTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *) ((wxPreviewControlBar *) x));
+static void *_p_wxStatusBarTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxStatusBar *) x));
 }
-static void *_p_wxPyPreviewControlBarTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxPanel *)(wxPreviewControlBar *) ((wxPyPreviewControlBar *) x));
+static void *_p_wxProcessEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxProcessEvent *) x));
 }
-static void *_p_wxDropFilesEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxDropFilesEvent *) x));
+static void *_p_wxChildFocusEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxChildFocusEvent *) x));
 }
 static void *_p_wxFocusEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *) ((wxFocusEvent *) x));
 }
-static void *_p_wxChildFocusEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxChildFocusEvent *) x));
-}
-static void *_p_wxProcessEventTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvent *) ((wxProcessEvent *) x));
+static void *_p_wxDropFilesEventTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvent *) ((wxDropFilesEvent *) x));
 }
 static void *_p_wxMozillaProgressEventTo_p_wxObject(void *x) {
     return (void *)((wxObject *) (wxEvent *)(wxCommandEvent *) ((wxMozillaProgressEvent *) x));
 }
-static void *_p_wxControlWithItemsTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxControl *) ((wxControlWithItems *) x));
-}
-static void *_p_wxPageSetupDialogDataTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPageSetupDialogData *) x));
-}
-static void *_p_wxPrintDialogDataTo_p_wxObject(void *x) {
-    return (void *)((wxObject *)  ((wxPrintDialogData *) x));
-}
-static void *_p_wxPyValidatorTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *)(wxValidator *) ((wxPyValidator *) x));
-}
-static void *_p_wxValidatorTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxValidator *) x));
+static void *_p_wxMDIParentFrameTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMDIParentFrame *) x));
 }
-static void *_p_wxPyTimerTo_p_wxObject(void *x) {
-    return (void *)((wxObject *) (wxEvtHandler *) ((wxPyTimer *) x));
+static void *_p_wxMenuBarTo_p_wxObject(void *x) {
+    return (void *)((wxObject *) (wxEvtHandler *)(wxWindow *) ((wxMenuBar *) x));
 }
 static void *_p_wxFrameTo_p_wxTopLevelWindow(void *x) {
     return (void *)((wxTopLevelWindow *)  ((wxFrame *) x));
@@ -6452,12 +7471,12 @@ static void *_p_wxMDIParentFrameTo_p_wxT
 static void *_p_wxMDIChildFrameTo_p_wxTopLevelWindow(void *x) {
     return (void *)((wxTopLevelWindow *) (wxFrame *) ((wxMDIChildFrame *) x));
 }
-static void *_p_wxProgressDialogTo_p_wxTopLevelWindow(void *x) {
-    return (void *)((wxTopLevelWindow *) (wxFrame *) ((wxProgressDialog *) x));
-}
 static void *_p_wxMessageDialogTo_p_wxTopLevelWindow(void *x) {
     return (void *)((wxTopLevelWindow *) (wxDialog *) ((wxMessageDialog *) x));
 }
+static void *_p_wxNumberEntryDialogTo_p_wxTopLevelWindow(void *x) {
+    return (void *)((wxTopLevelWindow *) (wxDialog *) ((wxNumberEntryDialog *) x));
+}
 static void *_p_wxPasswordEntryDialogTo_p_wxTopLevelWindow(void *x) {
     return (void *)((wxTopLevelWindow *) (wxDialog *)(wxTextEntryDialog *) ((wxPasswordEntryDialog *) x));
 }
@@ -6473,6 +7492,9 @@ static void *_p_wxMultiChoiceDialogTo_p_
 static void *_p_wxFileDialogTo_p_wxTopLevelWindow(void *x) {
     return (void *)((wxTopLevelWindow *) (wxDialog *) ((wxFileDialog *) x));
 }
+static void *_p_wxProgressDialogTo_p_wxTopLevelWindow(void *x) {
+    return (void *)((wxTopLevelWindow *) (wxFrame *) ((wxProgressDialog *) x));
+}
 static void *_p_wxFindReplaceDialogTo_p_wxTopLevelWindow(void *x) {
     return (void *)((wxTopLevelWindow *) (wxDialog *) ((wxFindReplaceDialog *) x));
 }
@@ -6506,6 +7528,9 @@ static void *_p_wxProgressDialogTo_p_wxW
 static void *_p_wxMessageDialogTo_p_wxWindow(void *x) {
     return (void *)((wxWindow *) (wxTopLevelWindow *)(wxDialog *) ((wxMessageDialog *) x));
 }
+static void *_p_wxNumberEntryDialogTo_p_wxWindow(void *x) {
+    return (void *)((wxWindow *) (wxTopLevelWindow *)(wxDialog *) ((wxNumberEntryDialog *) x));
+}
 static void *_p_wxPasswordEntryDialogTo_p_wxWindow(void *x) {
     return (void *)((wxWindow *) (wxTopLevelWindow *)(wxDialog *)(wxTextEntryDialog *) ((wxPasswordEntryDialog *) x));
 }
@@ -6587,6 +7612,9 @@ static void *_p_wxPreviewCanvasTo_p_wxWi
 static void *_p_wxMozillaWindowTo_p_wxWindow(void *x) {
     return (void *)((wxWindow *) (wxTopLevelWindow *)(wxFrame *) ((wxMozillaWindow *) x));
 }
+static void *_p_wxSimpleHtmlListBoxTo_p_wxWindow(void *x) {
+    return (void *)((wxWindow *) (wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *)(wxPyHtmlListBox *) ((wxSimpleHtmlListBox *) x));
+}
 static void *_p_wxPyHtmlListBoxTo_p_wxWindow(void *x) {
     return (void *)((wxWindow *) (wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *) ((wxPyHtmlListBox *) x));
 }
@@ -6626,6 +7654,9 @@ static void *_p_wxWindowDestroyEventTo_p
 static void *_p_wxSplitterEventTo_p_wxCommandEvent(void *x) {
     return (void *)((wxCommandEvent *) (wxNotifyEvent *) ((wxSplitterEvent *) x));
 }
+static void *_p_wxClipboardTextEventTo_p_wxCommandEvent(void *x) {
+    return (void *)((wxCommandEvent *)  ((wxClipboardTextEvent *) x));
+}
 static void *_p_wxScrollEventTo_p_wxCommandEvent(void *x) {
     return (void *)((wxCommandEvent *)  ((wxScrollEvent *) x));
 }
@@ -6650,12 +7681,12 @@ static void *_p_wxWindowCreateEventTo_p_
 static void *_p_wxMozillaLoadCompleteEventTo_p_wxCommandEvent(void *x) {
     return (void *)((wxCommandEvent *)  ((wxMozillaLoadCompleteEvent *) x));
 }
-static void *_p_wxMozillaLinkChangedEventTo_p_wxCommandEvent(void *x) {
-    return (void *)((wxCommandEvent *)  ((wxMozillaLinkChangedEvent *) x));
-}
 static void *_p_wxMozillaBeforeLoadEventTo_p_wxCommandEvent(void *x) {
     return (void *)((wxCommandEvent *)  ((wxMozillaBeforeLoadEvent *) x));
 }
+static void *_p_wxMozillaLinkChangedEventTo_p_wxCommandEvent(void *x) {
+    return (void *)((wxCommandEvent *)  ((wxMozillaLinkChangedEvent *) x));
+}
 static void *_p_wxMozillaStateChangedEventTo_p_wxCommandEvent(void *x) {
     return (void *)((wxCommandEvent *)  ((wxMozillaStateChangedEvent *) x));
 }
@@ -6704,9 +7735,6 @@ static void *_p_wxMozillaBrowserTo_p_wxE
 static void *_p_wxMenuTo_p_wxEvtHandler(void *x) {
     return (void *)((wxEvtHandler *)  ((wxMenu *) x));
 }
-static void *_p_wxPasswordEntryDialogTo_p_wxEvtHandler(void *x) {
-    return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxDialog *)(wxTextEntryDialog *) ((wxPasswordEntryDialog *) x));
-}
 static void *_p_wxTextEntryDialogTo_p_wxEvtHandler(void *x) {
     return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxTextEntryDialog *) x));
 }
@@ -6719,6 +7747,12 @@ static void *_p_wxMultiChoiceDialogTo_p_
 static void *_p_wxFileDialogTo_p_wxEvtHandler(void *x) {
     return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxFileDialog *) x));
 }
+static void *_p_wxPasswordEntryDialogTo_p_wxEvtHandler(void *x) {
+    return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxDialog *)(wxTextEntryDialog *) ((wxPasswordEntryDialog *) x));
+}
+static void *_p_wxNumberEntryDialogTo_p_wxEvtHandler(void *x) {
+    return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxNumberEntryDialog *) x));
+}
 static void *_p_wxMessageDialogTo_p_wxEvtHandler(void *x) {
     return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxDialog *) ((wxMessageDialog *) x));
 }
@@ -6803,6 +7837,9 @@ static void *_p_wxPreviewCanvasTo_p_wxEv
 static void *_p_wxMozillaWindowTo_p_wxEvtHandler(void *x) {
     return (void *)((wxEvtHandler *) (wxWindow *)(wxTopLevelWindow *)(wxFrame *) ((wxMozillaWindow *) x));
 }
+static void *_p_wxSimpleHtmlListBoxTo_p_wxEvtHandler(void *x) {
+    return (void *)((wxEvtHandler *) (wxWindow *)(wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *)(wxPyHtmlListBox *) ((wxSimpleHtmlListBox *) x));
+}
 static void *_p_wxPyHtmlListBoxTo_p_wxEvtHandler(void *x) {
     return (void *)((wxEvtHandler *) (wxWindow *)(wxPanel *)(wxPyVScrolledWindow *)(wxPyVListBox *) ((wxPyHtmlListBox *) x));
 }
@@ -6863,6 +7900,9 @@ static void *_p_wxSplitterEventTo_p_wxEv
 static void *_p_wxTimerEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *)  ((wxTimerEvent *) x));
 }
+static void *_p_wxPowerEventTo_p_wxEvent(void *x) {
+    return (void *)((wxEvent *)  ((wxPowerEvent *) x));
+}
 static void *_p_wxInitDialogEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *)  ((wxInitDialogEvent *) x));
 }
@@ -6872,12 +7912,15 @@ static void *_p_wxScrollEventTo_p_wxEven
 static void *_p_wxFindDialogEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *) (wxCommandEvent *) ((wxFindDialogEvent *) x));
 }
-static void *_p_wxPyEventTo_p_wxEvent(void *x) {
-    return (void *)((wxEvent *)  ((wxPyEvent *) x));
-}
 static void *_p_wxNotifyEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *) (wxCommandEvent *) ((wxNotifyEvent *) x));
 }
+static void *_p_wxMouseCaptureLostEventTo_p_wxEvent(void *x) {
+    return (void *)((wxEvent *)  ((wxMouseCaptureLostEvent *) x));
+}
+static void *_p_wxPyEventTo_p_wxEvent(void *x) {
+    return (void *)((wxEvent *)  ((wxPyEvent *) x));
+}
 static void *_p_wxCalculateLayoutEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *)  ((wxCalculateLayoutEvent *) x));
 }
@@ -6923,6 +7966,9 @@ static void *_p_wxPaintEventTo_p_wxEvent
 static void *_p_wxNcPaintEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *)  ((wxNcPaintEvent *) x));
 }
+static void *_p_wxClipboardTextEventTo_p_wxEvent(void *x) {
+    return (void *)((wxEvent *) (wxCommandEvent *) ((wxClipboardTextEvent *) x));
+}
 static void *_p_wxUpdateUIEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *) (wxCommandEvent *) ((wxUpdateUIEvent *) x));
 }
@@ -7001,176 +8047,179 @@ static void *_p_wxScrollWinEventTo_p_wxE
 static void *_p_wxTaskBarIconEventTo_p_wxEvent(void *x) {
     return (void *)((wxEvent *)  ((wxTaskBarIconEvent *) x));
 }
-static swig_type_info _swigt__p_char = {"_p_char", "char *", 0, 0, 0};
-static swig_type_info _swigt__p_form_ops_t = {"_p_form_ops_t", "enum form_ops_t *|form_ops_t *", 0, 0, 0};
-static swig_type_info _swigt__p_int = {"_p_int", "int *|wxEventType *", 0, 0, 0};
-static swig_type_info _swigt__p_unsigned_char = {"_p_unsigned_char", "unsigned char *|byte *", 0, 0, 0};
-static swig_type_info _swigt__p_unsigned_int = {"_p_unsigned_int", "unsigned int *|time_t *", 0, 0, 0};
-static swig_type_info _swigt__p_unsigned_long = {"_p_unsigned_long", "unsigned long *|wxLogLevel *", 0, 0, 0};
-static swig_type_info _swigt__p_wxCommandEvent = {"_p_wxCommandEvent", "wxCommandEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxSashEvent = {"_p_wxSashEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxWindowDestroyEvent = {"_p_wxWindowDestroyEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSplitterEvent = {"_p_wxSplitterEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxScrollEvent = {"_p_wxScrollEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyCommandEvent = {"_p_wxPyCommandEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxContextMenuEvent = {"_p_wxContextMenuEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxChildFocusEvent = {"_p_wxChildFocusEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxDateEvent = {"_p_wxDateEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxWindowCreateEvent = {"_p_wxWindowCreateEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxNotifyEvent = {"_p_wxNotifyEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFindDialogEvent = {"_p_wxFindDialogEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxUpdateUIEvent = {"_p_wxUpdateUIEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxDuplexMode = {"_p_wxDuplexMode", "enum wxDuplexMode *|wxDuplexMode *", 0, 0, 0};
-static swig_type_info _swigt__p_wxEvent = {"_p_wxEvent", "wxEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMenuEvent = {"_p_wxMenuEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxCloseEvent = {"_p_wxCloseEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxEraseEvent = {"_p_wxEraseEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSetCursorEvent = {"_p_wxSetCursorEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxTimerEvent = {"_p_wxTimerEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxInitDialogEvent = {"_p_wxInitDialogEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyEvent = {"_p_wxPyEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxCalculateLayoutEvent = {"_p_wxCalculateLayoutEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxJoystickEvent = {"_p_wxJoystickEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxIdleEvent = {"_p_wxIdleEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxQueryNewPaletteEvent = {"_p_wxQueryNewPaletteEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMaximizeEvent = {"_p_wxMaximizeEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxIconizeEvent = {"_p_wxIconizeEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxActivateEvent = {"_p_wxActivateEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSizeEvent = {"_p_wxSizeEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMoveEvent = {"_p_wxMoveEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPaintEvent = {"_p_wxPaintEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxNcPaintEvent = {"_p_wxNcPaintEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPaletteChangedEvent = {"_p_wxPaletteChangedEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxDisplayChangedEvent = {"_p_wxDisplayChangedEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMouseCaptureChangedEvent = {"_p_wxMouseCaptureChangedEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSysColourChangedEvent = {"_p_wxSysColourChangedEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxDropFilesEvent = {"_p_wxDropFilesEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFocusEvent = {"_p_wxFocusEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxProcessEvent = {"_p_wxProcessEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxQueryLayoutInfoEvent = {"_p_wxQueryLayoutInfoEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxShowEvent = {"_p_wxShowEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxNavigationKeyEvent = {"_p_wxNavigationKeyEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxKeyEvent = {"_p_wxKeyEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxScrollWinEvent = {"_p_wxScrollWinEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxTaskBarIconEvent = {"_p_wxTaskBarIconEvent", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxEvtHandler = {"_p_wxEvtHandler", "wxEvtHandler *", 0, 0, 0};
-static swig_type_info _swigt__p_wxSplashScreen = {"_p_wxSplashScreen", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMiniFrame = {"_p_wxMiniFrame", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyPanel = {"_p_wxPyPanel", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyTimer = {"_p_wxPyTimer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMenuBar = {"_p_wxMenuBar", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxValidator = {"_p_wxValidator", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyValidator = {"_p_wxPyValidator", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMultiChoiceDialog = {"_p_wxMultiChoiceDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSingleChoiceDialog = {"_p_wxSingleChoiceDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxTextEntryDialog = {"_p_wxTextEntryDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFindReplaceDialog = {"_p_wxFindReplaceDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxProgressDialog = {"_p_wxProgressDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMessageDialog = {"_p_wxMessageDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFileDialog = {"_p_wxFileDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPasswordEntryDialog = {"_p_wxPasswordEntryDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPanel = {"_p_wxPanel", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxStatusBar = {"_p_wxStatusBar", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxScrolledWindow = {"_p_wxScrolledWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMDIClientWindow = {"_p_wxMDIClientWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyScrolledWindow = {"_p_wxPyScrolledWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSashWindow = {"_p_wxSashWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSplitterWindow = {"_p_wxSplitterWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSplashScreenWindow = {"_p_wxSplashScreenWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSashLayoutWindow = {"_p_wxSashLayoutWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPopupWindow = {"_p_wxPopupWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyPopupTransientWindow = {"_p_wxPyPopupTransientWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxTipWindow = {"_p_wxTipWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyVScrolledWindow = {"_p_wxPyVScrolledWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyPreviewFrame = {"_p_wxPyPreviewFrame", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPreviewFrame = {"_p_wxPreviewFrame", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxControl = {"_p_wxControl", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMDIChildFrame = {"_p_wxMDIChildFrame", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyApp = {"_p_wxPyApp", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyProcess = {"_p_wxPyProcess", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxControlWithItems = {"_p_wxControlWithItems", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyWindow = {"_p_wxPyWindow", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPreviewCanvas = {"_p_wxPreviewCanvas", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyHtmlListBox = {"_p_wxPyHtmlListBox", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyVListBox = {"_p_wxPyVListBox", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPreviewControlBar = {"_p_wxPreviewControlBar", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyPreviewControlBar = {"_p_wxPyPreviewControlBar", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyTaskBarIcon = {"_p_wxPyTaskBarIcon", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFontDialog = {"_p_wxFontDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxDirDialog = {"_p_wxDirDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxColourDialog = {"_p_wxColourDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxDialog = {"_p_wxDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMenu = {"_p_wxMenu", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMDIParentFrame = {"_p_wxMDIParentFrame", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFrame = {"_p_wxFrame", "wxFrame *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMouseEvent = {"_p_wxMouseEvent", "wxMouseEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaBeforeLoadEvent = {"_p_wxMozillaBeforeLoadEvent", "wxMozillaBeforeLoadEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaBrowser = {"_p_wxMozillaBrowser", "wxMozillaBrowser *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaLinkChangedEvent = {"_p_wxMozillaLinkChangedEvent", "wxMozillaLinkChangedEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaLoadCompleteEvent = {"_p_wxMozillaLoadCompleteEvent", "wxMozillaLoadCompleteEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaProgressEvent = {"_p_wxMozillaProgressEvent", "wxMozillaProgressEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaRightClickEvent = {"_p_wxMozillaRightClickEvent", "wxMozillaRightClickEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaSecurityChangedEvent = {"_p_wxMozillaSecurityChangedEvent", "wxMozillaSecurityChangedEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaSettings = {"_p_wxMozillaSettings", "wxMozillaSettings *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaStateChangedEvent = {"_p_wxMozillaStateChangedEvent", "wxMozillaStateChangedEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaStatusChangedEvent = {"_p_wxMozillaStatusChangedEvent", "wxMozillaStatusChangedEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaTitleChangedEvent = {"_p_wxMozillaTitleChangedEvent", "wxMozillaTitleChangedEvent *", 0, 0, 0};
-static swig_type_info _swigt__p_wxMozillaWindow = {"_p_wxMozillaWindow", "wxMozillaWindow *", 0, 0, 0};
-static swig_type_info _swigt__p_wxObject = {"_p_wxObject", "wxObject *", 0, 0, 0};
-static swig_type_info _swigt__p_wxIndividualLayoutConstraint = {"_p_wxIndividualLayoutConstraint", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxMenuItem = {"_p_wxMenuItem", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxImage = {"_p_wxImage", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPySizer = {"_p_wxPySizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxLayoutAlgorithm = {"_p_wxLayoutAlgorithm", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFindReplaceData = {"_p_wxFindReplaceData", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPrintDialogData = {"_p_wxPrintDialogData", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPageSetupDialogData = {"_p_wxPageSetupDialogData", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPrinter = {"_p_wxPrinter", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSystemOptions = {"_p_wxSystemOptions", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFlexGridSizer = {"_p_wxFlexGridSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxGridSizer = {"_p_wxGridSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxAcceleratorTable = {"_p_wxAcceleratorTable", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxColourData = {"_p_wxColourData", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyPrintout = {"_p_wxPyPrintout", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxStdDialogButtonSizer = {"_p_wxStdDialogButtonSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFontData = {"_p_wxFontData", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPrintData = {"_p_wxPrintData", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFileSystem = {"_p_wxFileSystem", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPrintPreview = {"_p_wxPrintPreview", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyPrintPreview = {"_p_wxPyPrintPreview", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxLayoutConstraints = {"_p_wxLayoutConstraints", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSizer = {"_p_wxSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxBoxSizer = {"_p_wxBoxSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxStaticBoxSizer = {"_p_wxStaticBoxSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxGridBagSizer = {"_p_wxGridBagSizer", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFSFile = {"_p_wxFSFile", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxClipboard = {"_p_wxClipboard", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxBusyInfo = {"_p_wxBusyInfo", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxSizerItem = {"_p_wxSizerItem", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxGBSizerItem = {"_p_wxGBSizerItem", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPageSetupDialog = {"_p_wxPageSetupDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPrintDialog = {"_p_wxPrintDialog", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxToolTip = {"_p_wxToolTip", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPNMHandler = {"_p_wxPNMHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxJPEGHandler = {"_p_wxJPEGHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPCXHandler = {"_p_wxPCXHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxGIFHandler = {"_p_wxGIFHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPNGHandler = {"_p_wxPNGHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxANIHandler = {"_p_wxANIHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxCURHandler = {"_p_wxCURHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxICOHandler = {"_p_wxICOHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxBMPHandler = {"_p_wxBMPHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPyImageHandler = {"_p_wxPyImageHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxImageHandler = {"_p_wxImageHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxXPMHandler = {"_p_wxXPMHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxTIFFHandler = {"_p_wxTIFFHandler", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxFileHistory = {"_p_wxFileHistory", 0, 0, 0, 0};
-static swig_type_info _swigt__p_wxPaperSize = {"_p_wxPaperSize", "enum wxPaperSize *|wxPaperSize *", 0, 0, 0};
-static swig_type_info _swigt__p_wxTopLevelWindow = {"_p_wxTopLevelWindow", "wxTopLevelWindow *", 0, 0, 0};
-static swig_type_info _swigt__p_wxWindow = {"_p_wxWindow", "wxWindow *", 0, 0, 0};
-static swig_type_info _swigt__ptrdiff_t = {"_ptrdiff_t", "ptrdiff_t", 0, 0, 0};
-static swig_type_info _swigt__std__ptrdiff_t = {"_std__ptrdiff_t", "std::ptrdiff_t", 0, 0, 0};
-static swig_type_info _swigt__unsigned_int = {"_unsigned_int", "unsigned int|std::size_t", 0, 0, 0};
+static swig_type_info _swigt__p_char = {"_p_char", "char *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_form_ops_t = {"_p_form_ops_t", "enum form_ops_t *|form_ops_t *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_int = {"_p_int", "int *|wxEventType *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_unsigned_char = {"_p_unsigned_char", "unsigned char *|byte *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_unsigned_int = {"_p_unsigned_int", "unsigned int *|time_t *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_unsigned_long = {"_p_unsigned_long", "unsigned long *|wxLogLevel *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxCommandEvent = {"_p_wxCommandEvent", "wxCommandEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxSashEvent = {"_p_wxSashEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxWindowDestroyEvent = {"_p_wxWindowDestroyEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSplitterEvent = {"_p_wxSplitterEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxClipboardTextEvent = {"_p_wxClipboardTextEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxScrollEvent = {"_p_wxScrollEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyCommandEvent = {"_p_wxPyCommandEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxContextMenuEvent = {"_p_wxContextMenuEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxChildFocusEvent = {"_p_wxChildFocusEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxDateEvent = {"_p_wxDateEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxWindowCreateEvent = {"_p_wxWindowCreateEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxNotifyEvent = {"_p_wxNotifyEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFindDialogEvent = {"_p_wxFindDialogEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxUpdateUIEvent = {"_p_wxUpdateUIEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxDuplexMode = {"_p_wxDuplexMode", "enum wxDuplexMode *|wxDuplexMode *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxEvent = {"_p_wxEvent", "wxEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMenuEvent = {"_p_wxMenuEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxCloseEvent = {"_p_wxCloseEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxEraseEvent = {"_p_wxEraseEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSetCursorEvent = {"_p_wxSetCursorEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxTimerEvent = {"_p_wxTimerEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPowerEvent = {"_p_wxPowerEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxInitDialogEvent = {"_p_wxInitDialogEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyEvent = {"_p_wxPyEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMouseCaptureLostEvent = {"_p_wxMouseCaptureLostEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxCalculateLayoutEvent = {"_p_wxCalculateLayoutEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxJoystickEvent = {"_p_wxJoystickEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxIdleEvent = {"_p_wxIdleEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxQueryNewPaletteEvent = {"_p_wxQueryNewPaletteEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMaximizeEvent = {"_p_wxMaximizeEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxIconizeEvent = {"_p_wxIconizeEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxActivateEvent = {"_p_wxActivateEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSizeEvent = {"_p_wxSizeEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMoveEvent = {"_p_wxMoveEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPaintEvent = {"_p_wxPaintEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxNcPaintEvent = {"_p_wxNcPaintEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPaletteChangedEvent = {"_p_wxPaletteChangedEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxDisplayChangedEvent = {"_p_wxDisplayChangedEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMouseCaptureChangedEvent = {"_p_wxMouseCaptureChangedEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSysColourChangedEvent = {"_p_wxSysColourChangedEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxDropFilesEvent = {"_p_wxDropFilesEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFocusEvent = {"_p_wxFocusEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxProcessEvent = {"_p_wxProcessEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxQueryLayoutInfoEvent = {"_p_wxQueryLayoutInfoEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxShowEvent = {"_p_wxShowEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxNavigationKeyEvent = {"_p_wxNavigationKeyEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxKeyEvent = {"_p_wxKeyEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxScrollWinEvent = {"_p_wxScrollWinEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxTaskBarIconEvent = {"_p_wxTaskBarIconEvent", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxEvtHandler = {"_p_wxEvtHandler", "wxEvtHandler *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxSplashScreen = {"_p_wxSplashScreen", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMiniFrame = {"_p_wxMiniFrame", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyPanel = {"_p_wxPyPanel", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyTimer = {"_p_wxPyTimer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMenuBar = {"_p_wxMenuBar", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxValidator = {"_p_wxValidator", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyValidator = {"_p_wxPyValidator", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFileDialog = {"_p_wxFileDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMultiChoiceDialog = {"_p_wxMultiChoiceDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSingleChoiceDialog = {"_p_wxSingleChoiceDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxTextEntryDialog = {"_p_wxTextEntryDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFindReplaceDialog = {"_p_wxFindReplaceDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxProgressDialog = {"_p_wxProgressDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMessageDialog = {"_p_wxMessageDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxNumberEntryDialog = {"_p_wxNumberEntryDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPasswordEntryDialog = {"_p_wxPasswordEntryDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPanel = {"_p_wxPanel", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxStatusBar = {"_p_wxStatusBar", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxScrolledWindow = {"_p_wxScrolledWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMDIClientWindow = {"_p_wxMDIClientWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyScrolledWindow = {"_p_wxPyScrolledWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSashWindow = {"_p_wxSashWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSplitterWindow = {"_p_wxSplitterWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSplashScreenWindow = {"_p_wxSplashScreenWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSashLayoutWindow = {"_p_wxSashLayoutWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPopupWindow = {"_p_wxPopupWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyPopupTransientWindow = {"_p_wxPyPopupTransientWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxTipWindow = {"_p_wxTipWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyVScrolledWindow = {"_p_wxPyVScrolledWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyPreviewFrame = {"_p_wxPyPreviewFrame", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPreviewFrame = {"_p_wxPreviewFrame", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxControl = {"_p_wxControl", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMDIChildFrame = {"_p_wxMDIChildFrame", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyApp = {"_p_wxPyApp", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyProcess = {"_p_wxPyProcess", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxControlWithItems = {"_p_wxControlWithItems", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyWindow = {"_p_wxPyWindow", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPreviewCanvas = {"_p_wxPreviewCanvas", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSimpleHtmlListBox = {"_p_wxSimpleHtmlListBox", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyHtmlListBox = {"_p_wxPyHtmlListBox", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyVListBox = {"_p_wxPyVListBox", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPreviewControlBar = {"_p_wxPreviewControlBar", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyPreviewControlBar = {"_p_wxPyPreviewControlBar", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyTaskBarIcon = {"_p_wxPyTaskBarIcon", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFontDialog = {"_p_wxFontDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxDirDialog = {"_p_wxDirDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxColourDialog = {"_p_wxColourDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxDialog = {"_p_wxDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMenu = {"_p_wxMenu", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMDIParentFrame = {"_p_wxMDIParentFrame", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFrame = {"_p_wxFrame", "wxFrame *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMouseEvent = {"_p_wxMouseEvent", "wxMouseEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaBeforeLoadEvent = {"_p_wxMozillaBeforeLoadEvent", "wxMozillaBeforeLoadEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaBrowser = {"_p_wxMozillaBrowser", "wxMozillaBrowser *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaLinkChangedEvent = {"_p_wxMozillaLinkChangedEvent", "wxMozillaLinkChangedEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaLoadCompleteEvent = {"_p_wxMozillaLoadCompleteEvent", "wxMozillaLoadCompleteEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaProgressEvent = {"_p_wxMozillaProgressEvent", "wxMozillaProgressEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaRightClickEvent = {"_p_wxMozillaRightClickEvent", "wxMozillaRightClickEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaSecurityChangedEvent = {"_p_wxMozillaSecurityChangedEvent", "wxMozillaSecurityChangedEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaSettings = {"_p_wxMozillaSettings", "wxMozillaSettings *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaStateChangedEvent = {"_p_wxMozillaStateChangedEvent", "wxMozillaStateChangedEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaStatusChangedEvent = {"_p_wxMozillaStatusChangedEvent", "wxMozillaStatusChangedEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaTitleChangedEvent = {"_p_wxMozillaTitleChangedEvent", "wxMozillaTitleChangedEvent *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxMozillaWindow = {"_p_wxMozillaWindow", "wxMozillaWindow *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxObject = {"_p_wxObject", "wxObject *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxIndividualLayoutConstraint = {"_p_wxIndividualLayoutConstraint", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxMenuItem = {"_p_wxMenuItem", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxImage = {"_p_wxImage", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPySizer = {"_p_wxPySizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxLayoutAlgorithm = {"_p_wxLayoutAlgorithm", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFindReplaceData = {"_p_wxFindReplaceData", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPrintDialogData = {"_p_wxPrintDialogData", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPageSetupDialogData = {"_p_wxPageSetupDialogData", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPrinter = {"_p_wxPrinter", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSystemOptions = {"_p_wxSystemOptions", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxGridSizer = {"_p_wxGridSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFlexGridSizer = {"_p_wxFlexGridSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxAcceleratorTable = {"_p_wxAcceleratorTable", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxColourData = {"_p_wxColourData", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyPrintout = {"_p_wxPyPrintout", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxStdDialogButtonSizer = {"_p_wxStdDialogButtonSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFontData = {"_p_wxFontData", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPrintData = {"_p_wxPrintData", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFileSystem = {"_p_wxFileSystem", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPrintPreview = {"_p_wxPrintPreview", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyPrintPreview = {"_p_wxPyPrintPreview", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxLayoutConstraints = {"_p_wxLayoutConstraints", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxStaticBoxSizer = {"_p_wxStaticBoxSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxBoxSizer = {"_p_wxBoxSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSizer = {"_p_wxSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxGridBagSizer = {"_p_wxGridBagSizer", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFSFile = {"_p_wxFSFile", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxClipboard = {"_p_wxClipboard", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxBusyInfo = {"_p_wxBusyInfo", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxGBSizerItem = {"_p_wxGBSizerItem", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxSizerItem = {"_p_wxSizerItem", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPrintDialog = {"_p_wxPrintDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPageSetupDialog = {"_p_wxPageSetupDialog", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxToolTip = {"_p_wxToolTip", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxTGAHandler = {"_p_wxTGAHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxTIFFHandler = {"_p_wxTIFFHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxXPMHandler = {"_p_wxXPMHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxImageHandler = {"_p_wxImageHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPyImageHandler = {"_p_wxPyImageHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxBMPHandler = {"_p_wxBMPHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxICOHandler = {"_p_wxICOHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxCURHandler = {"_p_wxCURHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxANIHandler = {"_p_wxANIHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPNGHandler = {"_p_wxPNGHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxGIFHandler = {"_p_wxGIFHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPCXHandler = {"_p_wxPCXHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxJPEGHandler = {"_p_wxJPEGHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPNMHandler = {"_p_wxPNMHandler", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxFileHistory = {"_p_wxFileHistory", 0, 0, 0, 0, 0};
+static swig_type_info _swigt__p_wxPaperSize = {"_p_wxPaperSize", "enum wxPaperSize *|wxPaperSize *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxTopLevelWindow = {"_p_wxTopLevelWindow", "wxTopLevelWindow *", 0, 0, (void*)0, 0};
+static swig_type_info _swigt__p_wxWindow = {"_p_wxWindow", "wxWindow *", 0, 0, (void*)0, 0};
 
 static swig_type_info *swig_type_initial[] = {
   &_swigt__p_char,
@@ -7189,6 +8238,7 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxCalculateLayoutEvent,
   &_swigt__p_wxChildFocusEvent,
   &_swigt__p_wxClipboard,
+  &_swigt__p_wxClipboardTextEvent,
   &_swigt__p_wxCloseEvent,
   &_swigt__p_wxColourData,
   &_swigt__p_wxColourDialog,
@@ -7244,6 +8294,7 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxMessageDialog,
   &_swigt__p_wxMiniFrame,
   &_swigt__p_wxMouseCaptureChangedEvent,
+  &_swigt__p_wxMouseCaptureLostEvent,
   &_swigt__p_wxMouseEvent,
   &_swigt__p_wxMoveEvent,
   &_swigt__p_wxMozillaBeforeLoadEvent,
@@ -7262,6 +8313,7 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxNavigationKeyEvent,
   &_swigt__p_wxNcPaintEvent,
   &_swigt__p_wxNotifyEvent,
+  &_swigt__p_wxNumberEntryDialog,
   &_swigt__p_wxObject,
   &_swigt__p_wxPCXHandler,
   &_swigt__p_wxPNGHandler,
@@ -7274,6 +8326,7 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxPaperSize,
   &_swigt__p_wxPasswordEntryDialog,
   &_swigt__p_wxPopupWindow,
+  &_swigt__p_wxPowerEvent,
   &_swigt__p_wxPreviewCanvas,
   &_swigt__p_wxPreviewControlBar,
   &_swigt__p_wxPreviewFrame,
@@ -7314,6 +8367,7 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxScrolledWindow,
   &_swigt__p_wxSetCursorEvent,
   &_swigt__p_wxShowEvent,
+  &_swigt__p_wxSimpleHtmlListBox,
   &_swigt__p_wxSingleChoiceDialog,
   &_swigt__p_wxSizeEvent,
   &_swigt__p_wxSizer,
@@ -7327,6 +8381,7 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxStdDialogButtonSizer,
   &_swigt__p_wxSysColourChangedEvent,
   &_swigt__p_wxSystemOptions,
+  &_swigt__p_wxTGAHandler,
   &_swigt__p_wxTIFFHandler,
   &_swigt__p_wxTaskBarIconEvent,
   &_swigt__p_wxTextEntryDialog,
@@ -7340,9 +8395,6 @@ static swig_type_info *swig_type_initial
   &_swigt__p_wxWindowCreateEvent,
   &_swigt__p_wxWindowDestroyEvent,
   &_swigt__p_wxXPMHandler,
-  &_swigt__ptrdiff_t,
-  &_swigt__std__ptrdiff_t,
-  &_swigt__unsigned_int,
 };
 
 static swig_cast_info _swigc__p_char[] = {  {&_swigt__p_char, 0, 0, 0},{0, 0, 0, 0}};
@@ -7354,6 +8406,7 @@ static swig_cast_info _swigc__p_unsigned
 static swig_cast_info _swigc__p_wxSashEvent[] = {{&_swigt__p_wxSashEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxWindowDestroyEvent[] = {{&_swigt__p_wxWindowDestroyEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxSplitterEvent[] = {{&_swigt__p_wxSplitterEvent, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxClipboardTextEvent[] = {{&_swigt__p_wxClipboardTextEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxScrollEvent[] = {{&_swigt__p_wxScrollEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyCommandEvent[] = {{&_swigt__p_wxPyCommandEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxContextMenuEvent[] = {{&_swigt__p_wxContextMenuEvent, 0, 0, 0},{0, 0, 0, 0}};
@@ -7363,15 +8416,17 @@ static swig_cast_info _swigc__p_wxWindow
 static swig_cast_info _swigc__p_wxNotifyEvent[] = {{&_swigt__p_wxNotifyEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxFindDialogEvent[] = {{&_swigt__p_wxFindDialogEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxUpdateUIEvent[] = {{&_swigt__p_wxUpdateUIEvent, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxCommandEvent[] = {  {&_swigt__p_wxSashEvent, _p_wxSashEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxWindowDestroyEvent, _p_wxWindowDestroyEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxSplitterEvent, _p_wxSplitterEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxScrollEvent, _p_wxScrollEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxPyCommandEvent, _p_wxPyCommandEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxCommandEvent, 0, 0, 0},  {&_swigt__p_wxContextMenuEvent, _p_wxContextMenuEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxChildFocusEvent, _p_wxChildFocusEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaProgressEvent, _p_wxMozillaProgressEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxDateEvent, _p_wxDateEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxWindowCreateEvent, _p_wxWindowCreateEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaLoadCompleteEvent, _p_wxMozillaLoadCompleteEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaLinkChangedEvent, _p_wxMozillaLinkChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaBeforeLoadEvent, _p_wxMozillaBeforeLoadEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaStateChangedEvent, _p_wxMozillaStateChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaSecurityChangedEvent, _p_wxMozillaSecurityChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaStatusChangedEvent, _p_wxMozillaStatusChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaTitleChangedEvent, _p_wxMozillaTitleChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxNotifyEvent, _p_wxNotifyEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxFindDialogEvent, _p_wxFindDialogEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxUpdateUIEvent, _p_wxUpdateUIEventTo_p_wxCommandEvent, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxCommandEvent[] = {  {&_swigt__p_wxSashEvent, _p_wxSashEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxWindowDestroyEvent, _p_wxWindowDestroyEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxSplitterEvent, _p_wxSplitterEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxClipboardTextEvent, _p_wxClipboardTextEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxScrollEvent, _p_wxScrollEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxPyCommandEvent, _p_wxPyCommandEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxCommandEvent, 0, 0, 0},  {&_swigt__p_wxContextMenuEvent, _p_wxContextMenuEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxChildFocusEvent, _p_wxChildFocusEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaProgressEvent, _p_wxMozillaProgressEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxDateEvent, _p_wxDateEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxWindowCreateEvent, _p_wxWindowCreateEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaLoadCompleteEvent, _p_wxMozillaLoadCompleteEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaBeforeLoadEvent, _p_wxMozillaBeforeLoadEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaLinkChangedEvent, _p_wxMozillaLinkChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaStateChangedEvent, _p_wxMozillaStateChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaSecurityChangedEvent, _p_wxMozillaSecurityChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaStatusChangedEvent, _p_wxMozillaStatusChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxMozillaTitleChangedEvent, _p_wxMozillaTitleChangedEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxNotifyEvent, _p_wxNotifyEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxFindDialogEvent, _p_wxFindDialogEventTo_p_wxCommandEvent, 0, 0},  {&_swigt__p_wxUpdateUIEvent, _p_wxUpdateUIEventTo_p_wxCommandEvent, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxDuplexMode[] = {  {&_swigt__p_wxDuplexMode, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMenuEvent[] = {{&_swigt__p_wxMenuEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxCloseEvent[] = {{&_swigt__p_wxCloseEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxEraseEvent[] = {{&_swigt__p_wxEraseEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxSetCursorEvent[] = {{&_swigt__p_wxSetCursorEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxTimerEvent[] = {{&_swigt__p_wxTimerEvent, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxPowerEvent[] = {{&_swigt__p_wxPowerEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxInitDialogEvent[] = {{&_swigt__p_wxInitDialogEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyEvent[] = {{&_swigt__p_wxPyEvent, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxMouseCaptureLostEvent[] = {{&_swigt__p_wxMouseCaptureLostEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxCalculateLayoutEvent[] = {{&_swigt__p_wxCalculateLayoutEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxJoystickEvent[] = {{&_swigt__p_wxJoystickEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxIdleEvent[] = {{&_swigt__p_wxIdleEvent, 0, 0, 0},{0, 0, 0, 0}};
@@ -7396,7 +8451,7 @@ static swig_cast_info _swigc__p_wxNaviga
 static swig_cast_info _swigc__p_wxKeyEvent[] = {{&_swigt__p_wxKeyEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxScrollWinEvent[] = {{&_swigt__p_wxScrollWinEvent, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxTaskBarIconEvent[] = {{&_swigt__p_wxTaskBarIconEvent, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxEvent[] = {  {&_swigt__p_wxContextMenuEvent, _p_wxContextMenuEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMenuEvent, _p_wxMenuEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxCloseEvent, _p_wxCloseEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMouseEvent, _p_wxMouseEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxEraseEvent, _p_wxEraseEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSetCursorEvent, _p_wxSetCursorEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSplitterEvent, _p_wxSplitterEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxTimerEvent, _p_wxTimerEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxInitDialogEvent, _p_wxInitDialogEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxFindDialogEvent, _p_wxFindDialogEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxScrollEvent, _p_wxScrollEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxNotifyEvent, _p_wxNotifyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPyEvent, _p_wxPyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxCalculateLayoutEvent, _p_wxCalculateLayoutEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxJoystickEvent, _p_wxJoystickEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaRightClickEvent, _p_wxMozillaRightClickEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxEvent, 0, 0, 0},  {&_swigt__p_wxIdleEvent, _p_wxIdleEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxWindowCreateEvent, _p_wxWindowCreateEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxQueryNewPaletteEvent, _p_wxQueryNewPaletteEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMaximizeEvent, _p_wxMaximizeEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxIconizeEvent, _p_wxIconizeEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxActivateEvent, _p_wxActivateEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSizeEvent, _p_wxSizeEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMoveEvent, _p_wxMoveEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxDateEvent, _p_wxDateEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaLoadCompleteEvent, _p_wxMozillaLoadCompleteEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPaintEvent, _p_wxPaintEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxNcPaintEvent, _p_wxNcPaintEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxUpdateUIEvent, _p_wxUpdateUIEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPaletteChangedEvent, _p_wxPaletteChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxDisplayChangedEvent, _p_wxDisplayChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMouseCaptureChangedEvent, _p_wxMouseCaptureChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSysColourChangedEvent, _p_wxSysColourChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaBeforeLoadEvent, _p_wxMozillaBeforeLoadEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaLinkChangedEvent, _p_wxMozillaLinkChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaStateChangedEvent, _p_wxMozillaStateChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaSecurityChangedEvent, _p_wxMozillaSecurityChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaStatusChangedEvent, _p_wxMozillaStatusChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaTitleChangedEvent, _p_wxMozillaTitleChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxDropFilesEvent, _p_wxDropFilesEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxFocusEvent, _p_wxFocusEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxChildFocusEvent, _p_wxChildFocusEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxProcessEvent, _p_wxProcessEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaProgressEvent, _p_wxMozillaProgressEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSashEvent, _p_wxSashEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxQueryLayoutInfoEvent, _p_wxQueryLayoutInfoEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxShowEvent, _p_wxShowEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxCommandEvent, _p_wxCommandEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPyCommandEvent, _p_wxPyCommandEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxWindowDestroyEvent, _p_wxWindowDestroyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxNavigationKeyEvent, _p_wxNavigationKeyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxKeyEvent, _p_wxKeyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxScrollWinEvent, _p_wxScrollWinEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxTaskBarIconEvent, _p_wxTaskBarIconEventTo_p_wxEvent, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxEvent[] = {  {&_swigt__p_wxContextMenuEvent, _p_wxContextMenuEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMenuEvent, _p_wxMenuEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxCloseEvent, _p_wxCloseEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMouseEvent, _p_wxMouseEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxEraseEvent, _p_wxEraseEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSetCursorEvent, _p_wxSetCursorEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSplitterEvent, _p_wxSplitterEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxTimerEvent, _p_wxTimerEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPowerEvent, _p_wxPowerEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxInitDialogEvent, _p_wxInitDialogEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxFindDialogEvent, _p_wxFindDialogEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxScrollEvent, _p_wxScrollEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxNotifyEvent, _p_wxNotifyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPyEvent, _p_wxPyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMouseCaptureLostEvent, _p_wxMouseCaptureLostEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxCalculateLayoutEvent, _p_wxCalculateLayoutEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxJoystickEvent, _p_wxJoystickEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaRightClickEvent, _p_wxMozillaRightClickEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxEvent, 0, 0, 0},  {&_swigt__p_wxIdleEvent, _p_wxIdleEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxWindowCreateEvent, _p_wxWindowCreateEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxQueryNewPaletteEvent, _p_wxQueryNewPaletteEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMaximizeEvent, _p_wxMaximizeEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxIconizeEvent, _p_wxIconizeEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxActivateEvent, _p_wxActivateEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSizeEvent, _p_wxSizeEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMoveEvent, _p_wxMoveEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxDateEvent, _p_wxDateEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaLoadCompleteEvent, _p_wxMozillaLoadCompleteEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPaintEvent, _p_wxPaintEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxNcPaintEvent, _p_wxNcPaintEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxClipboardTextEvent, _p_wxClipboardTextEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxUpdateUIEvent, _p_wxUpdateUIEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPaletteChangedEvent, _p_wxPaletteChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxDisplayChangedEvent, _p_wxDisplayChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMouseCaptureChangedEvent, _p_wxMouseCaptureChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSysColourChangedEvent, _p_wxSysColourChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaBeforeLoadEvent, _p_wxMozillaBeforeLoadEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaLinkChangedEvent, _p_wxMozillaLinkChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaStateChangedEvent, _p_wxMozillaStateChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaSecurityChangedEvent, _p_wxMozillaSecurityChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaStatusChangedEvent, _p_wxMozillaStatusChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaTitleChangedEvent, _p_wxMozillaTitleChangedEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxDropFilesEvent, _p_wxDropFilesEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxFocusEvent, _p_wxFocusEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxChildFocusEvent, _p_wxChildFocusEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxProcessEvent, _p_wxProcessEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxMozillaProgressEvent, _p_wxMozillaProgressEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxSashEvent, _p_wxSashEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxQueryLayoutInfoEvent, _p_wxQueryLayoutInfoEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxShowEvent, _p_wxShowEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxCommandEvent, _p_wxCommandEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxPyCommandEvent, _p_wxPyCommandEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxWindowDestroyEvent, _p_wxWindowDestroyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxNavigationKeyEvent, _p_wxNavigationKeyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxKeyEvent, _p_wxKeyEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxScrollWinEvent, _p_wxScrollWinEventTo_p_wxEvent, 0, 0},  {&_swigt__p_wxTaskBarIconEvent, _p_wxTaskBarIconEventTo_p_wxEvent, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxSplashScreen[] = {{&_swigt__p_wxSplashScreen, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMiniFrame[] = {{&_swigt__p_wxMiniFrame, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyPanel[] = {{&_swigt__p_wxPyPanel, 0, 0, 0},{0, 0, 0, 0}};
@@ -7404,13 +8459,14 @@ static swig_cast_info _swigc__p_wxPyTime
 static swig_cast_info _swigc__p_wxMenuBar[] = {{&_swigt__p_wxMenuBar, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxValidator[] = {{&_swigt__p_wxValidator, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyValidator[] = {{&_swigt__p_wxPyValidator, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxFileDialog[] = {{&_swigt__p_wxFileDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMultiChoiceDialog[] = {{&_swigt__p_wxMultiChoiceDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxSingleChoiceDialog[] = {{&_swigt__p_wxSingleChoiceDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxTextEntryDialog[] = {{&_swigt__p_wxTextEntryDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxFindReplaceDialog[] = {{&_swigt__p_wxFindReplaceDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxProgressDialog[] = {{&_swigt__p_wxProgressDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMessageDialog[] = {{&_swigt__p_wxMessageDialog, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxFileDialog[] = {{&_swigt__p_wxFileDialog, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxNumberEntryDialog[] = {{&_swigt__p_wxNumberEntryDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPasswordEntryDialog[] = {{&_swigt__p_wxPasswordEntryDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPanel[] = {{&_swigt__p_wxPanel, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxStatusBar[] = {{&_swigt__p_wxStatusBar, 0, 0, 0},{0, 0, 0, 0}};
@@ -7434,6 +8490,7 @@ static swig_cast_info _swigc__p_wxPyProc
 static swig_cast_info _swigc__p_wxControlWithItems[] = {{&_swigt__p_wxControlWithItems, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyWindow[] = {{&_swigt__p_wxPyWindow, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPreviewCanvas[] = {{&_swigt__p_wxPreviewCanvas, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxSimpleHtmlListBox[] = {{&_swigt__p_wxSimpleHtmlListBox, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyHtmlListBox[] = {{&_swigt__p_wxPyHtmlListBox, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyVListBox[] = {{&_swigt__p_wxPyVListBox, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPreviewControlBar[] = {{&_swigt__p_wxPreviewControlBar, 0, 0, 0},{0, 0, 0, 0}};
@@ -7445,7 +8502,7 @@ static swig_cast_info _swigc__p_wxColour
 static swig_cast_info _swigc__p_wxDialog[] = {{&_swigt__p_wxDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMenu[] = {{&_swigt__p_wxMenu, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMDIParentFrame[] = {{&_swigt__p_wxMDIParentFrame, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxEvtHandler[] = {  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPanel, _p_wxPyPanelTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyTimer, _p_wxPyTimerTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMenuBar, _p_wxMenuBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxValidator, _p_wxValidatorTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyValidator, _p_wxPyValidatorTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMozillaBrowser, _p_wxMozillaBrowserTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPanel, _p_wxPanelTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxStatusBar, _p_wxStatusBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxWindow, _p_wxWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxScrolledWindow, _p_wxScrolledWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxTopLevelWindow, _p_wxTopLevelWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMDIClientWindow, _p_wxMDIClientWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyScrolledWindow, _p_wxPyScrolledWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSashWindow, _p_wxSashWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSplitterWindow, _p_wxSplitterWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSplashScreenWindow, _p_wxSplashScreenWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSashLayoutWindow, _p_wxSashLayoutWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPopupWindow, _p_wxPopupWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPopupTransientWindow, _p_wxPyPopupTransientWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxTipWindow, _p_wxTipWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyVScrolledWindow, _p_wxPyVScrolledWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxControl, _p_wxControlTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyApp, _p_wxPyAppTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyProcess, _p_wxPyProcessTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxControlWithItems, _p_wxControlWithItemsTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxEvtHandler, 0, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyWindow, _p_wxPyWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPreviewCanvas, _p_wxPreviewCanvasTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyHtmlListBox, _p_wxPyHtmlListBoxTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyVListBox, _p_wxPyVListBoxTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPreviewControlBar, _p_wxPreviewControlBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPreviewControlBar, _p_wxPyPreviewControlBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyTaskBarIcon, _p_wxPyTaskBarIconTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMenu, _p_wxMenuTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxEvtHandler, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxEvtHandler[] = {  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPanel, _p_wxPyPanelTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyTimer, _p_wxPyTimerTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMenuBar, _p_wxMenuBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxValidator, _p_wxValidatorTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyValidator, _p_wxPyValidatorTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMozillaBrowser, _p_wxMozillaBrowserTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxNumberEntryDialog, _p_wxNumberEntryDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPanel, _p_wxPanelTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxStatusBar, _p_wxStatusBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxScrolledWindow, _p_wxScrolledWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxTopLevelWindow, _p_wxTopLevelWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMDIClientWindow, _p_wxMDIClientWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyScrolledWindow, _p_wxPyScrolledWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxWindow, _p_wxWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSashWindow, _p_wxSashWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSplitterWindow, _p_wxSplitterWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSplashScreenWindow, _p_wxSplashScreenWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSashLayoutWindow, _p_wxSashLayoutWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPopupWindow, _p_wxPopupWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPopupTransientWindow, _p_wxPyPopupTransientWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxTipWindow, _p_wxTipWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyVScrolledWindow, _p_wxPyVScrolledWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxControl, _p_wxControlTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyApp, _p_wxPyAppTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyProcess, _p_wxPyProcessTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxControlWithItems, _p_wxControlWithItemsTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxEvtHandler, 0, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyWindow, _p_wxPyWindowTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPreviewCanvas, _p_wxPreviewCanvasTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxSimpleHtmlListBox, _p_wxSimpleHtmlListBoxTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyHtmlListBox, _p_wxPyHtmlListBoxTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyVListBox, _p_wxPyVListBoxTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPreviewControlBar, _p_wxPreviewControlBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyPreviewControlBar, _p_wxPyPreviewControlBarTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxPyTaskBarIcon, _p_wxPyTaskBarIconTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMenu, _p_wxMenuTo_p_wxEvtHandler, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxEvtHandler, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxFrame[] = {  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxFrame, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxFrame, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxFrame, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxFrame, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxFrame, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxFrame, 0, 0},  {&_swigt__p_wxFrame, 0, 0, 0},  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxFrame, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxFrame, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMouseEvent[] = {  {&_swigt__p_wxMouseEvent, 0, 0, 0},  {&_swigt__p_wxMozillaRightClickEvent, _p_wxMozillaRightClickEventTo_p_wxMouseEvent, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxMozillaBeforeLoadEvent[] = {  {&_swigt__p_wxMozillaBeforeLoadEvent, 0, 0, 0},{0, 0, 0, 0}};
@@ -7470,8 +8527,8 @@ static swig_cast_info _swigc__p_wxPrintD
 static swig_cast_info _swigc__p_wxPageSetupDialogData[] = {{&_swigt__p_wxPageSetupDialogData, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPrinter[] = {{&_swigt__p_wxPrinter, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxSystemOptions[] = {{&_swigt__p_wxSystemOptions, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxFlexGridSizer[] = {{&_swigt__p_wxFlexGridSizer, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxGridSizer[] = {{&_swigt__p_wxGridSizer, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxFlexGridSizer[] = {{&_swigt__p_wxFlexGridSizer, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxAcceleratorTable[] = {{&_swigt__p_wxAcceleratorTable, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxColourData[] = {{&_swigt__p_wxColourData, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyPrintout[] = {{&_swigt__p_wxPyPrintout, 0, 0, 0},{0, 0, 0, 0}};
@@ -7482,39 +8539,37 @@ static swig_cast_info _swigc__p_wxFileSy
 static swig_cast_info _swigc__p_wxPrintPreview[] = {{&_swigt__p_wxPrintPreview, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPyPrintPreview[] = {{&_swigt__p_wxPyPrintPreview, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxLayoutConstraints[] = {{&_swigt__p_wxLayoutConstraints, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxSizer[] = {{&_swigt__p_wxSizer, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxBoxSizer[] = {{&_swigt__p_wxBoxSizer, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxStaticBoxSizer[] = {{&_swigt__p_wxStaticBoxSizer, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxBoxSizer[] = {{&_swigt__p_wxBoxSizer, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxSizer[] = {{&_swigt__p_wxSizer, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxGridBagSizer[] = {{&_swigt__p_wxGridBagSizer, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxFSFile[] = {{&_swigt__p_wxFSFile, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxClipboard[] = {{&_swigt__p_wxClipboard, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxBusyInfo[] = {{&_swigt__p_wxBusyInfo, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxSizerItem[] = {{&_swigt__p_wxSizerItem, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxGBSizerItem[] = {{&_swigt__p_wxGBSizerItem, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxPageSetupDialog[] = {{&_swigt__p_wxPageSetupDialog, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxSizerItem[] = {{&_swigt__p_wxSizerItem, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPrintDialog[] = {{&_swigt__p_wxPrintDialog, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxPageSetupDialog[] = {{&_swigt__p_wxPageSetupDialog, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxToolTip[] = {{&_swigt__p_wxToolTip, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxPNMHandler[] = {{&_swigt__p_wxPNMHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxJPEGHandler[] = {{&_swigt__p_wxJPEGHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxPCXHandler[] = {{&_swigt__p_wxPCXHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxGIFHandler[] = {{&_swigt__p_wxGIFHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxPNGHandler[] = {{&_swigt__p_wxPNGHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxANIHandler[] = {{&_swigt__p_wxANIHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxCURHandler[] = {{&_swigt__p_wxCURHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxICOHandler[] = {{&_swigt__p_wxICOHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxBMPHandler[] = {{&_swigt__p_wxBMPHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxPyImageHandler[] = {{&_swigt__p_wxPyImageHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxImageHandler[] = {{&_swigt__p_wxImageHandler, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxXPMHandler[] = {{&_swigt__p_wxXPMHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxTGAHandler[] = {{&_swigt__p_wxTGAHandler, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxTIFFHandler[] = {{&_swigt__p_wxTIFFHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxXPMHandler[] = {{&_swigt__p_wxXPMHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxImageHandler[] = {{&_swigt__p_wxImageHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxPyImageHandler[] = {{&_swigt__p_wxPyImageHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxBMPHandler[] = {{&_swigt__p_wxBMPHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxICOHandler[] = {{&_swigt__p_wxICOHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxCURHandler[] = {{&_swigt__p_wxCURHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxANIHandler[] = {{&_swigt__p_wxANIHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxPNGHandler[] = {{&_swigt__p_wxPNGHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxGIFHandler[] = {{&_swigt__p_wxGIFHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxPCXHandler[] = {{&_swigt__p_wxPCXHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxJPEGHandler[] = {{&_swigt__p_wxJPEGHandler, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxPNMHandler[] = {{&_swigt__p_wxPNMHandler, 0, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxFileHistory[] = {{&_swigt__p_wxFileHistory, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxObject[] = {  {&_swigt__p_wxUpdateUIEvent, _p_wxUpdateUIEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPreviewCanvas, _p_wxPreviewCanvasTo_p_wxObject, 0, 0},  {&_swigt__p_wxEvent, _p_wxEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFindDialogEvent, _p_wxFindDialogEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxInitDialogEvent, _p_wxInitDialogEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxIndividualLayoutConstraint, _p_wxIndividualLayoutConstraintTo_p_wxObject, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenuItem, _p_wxMenuItemTo_p_wxObject, 0, 0},  {&_swigt__p_wxImage, _p_wxImageTo_p_wxObject, 0, 0},  {&_swigt__p_wxPySizer, _p_wxPySizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxLayoutAlgorithm, _p_wxLayoutAlgorithmTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyTaskBarIcon, _p_wxPyTaskBarIconTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyApp, _p_wxPyAppTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaBrowser, _p_wxMozillaBrowserTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPreviewControlBar, _p_wxPyPreviewControlBarTo_p_wxObject, 0, 0},  {&_swigt__p_wxPreviewControlBar, _p_wxPreviewControlBarTo_p_wxObject, 0, 0},  {&_swigt__p_wxFindReplaceData, _p_wxFindReplaceDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxValidator, _p_wxValidatorTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyValidator, _p_wxPyValidatorTo_p_wxObject, 0, 0},  {&_swigt__p_wxCloseEvent, _p_wxCloseEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMouseEvent, _p_wxMouseEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxEraseEvent, _p_wxEraseEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxScrollEvent, _p_wxScrollEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintDialogData, _p_wxPrintDialogDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxPageSetupDialogData, _p_wxPageSetupDialogDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrinter, _p_wxPrinterTo_p_wxObject, 0, 0},  {&_swigt__p_wxControlWithItems, _p_wxControlWithItemsTo_p_wxObject, 0, 0},  {&_swigt__p_wxObject, 0, 0, 0},  {&_swigt__p_wxSystemOptions, _p_wxSystemOptionsTo_p_wxObject, 0, 0},  {&_swigt__p_wxFlexGridSizer, _p_wxFlexGridSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxGridSizer, _p_wxGridSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxAcceleratorTable, _p_wxAcceleratorTableTo_p_wxObject, 0, 0},  {&_swigt__p_wxControl, _p_wxControlTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyProcess, _p_wxPyProcessTo_p_wxObject, 0, 0},  {&_swigt__p_wxColourData, _p_wxColourDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxIdleEvent, _p_wxIdleEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxWindowCreateEvent, _p_wxWindowCreateEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxQueryNewPaletteEvent, _p_wxQueryNewPaletteEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMaximizeEvent, _p_wxMaximizeEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxIconizeEvent, _p_wxIconizeEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxActivateEvent, _p_wxActivateEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSizeEvent, _p_wxSizeEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMoveEvent, _p_wxMoveEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxDateEvent, _p_wxDateEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaLoadCompleteEvent, _p_wxMozillaLoadCompleteEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxCalculateLayoutEvent, _p_wxCalculateLayoutEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyTimer, _p_wxPyTimerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPrintout, _p_wxPyPrintoutTo_p_wxObject, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxStdDialogButtonSizer, _p_wxStdDialogButtonSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenu, _p_wxMenuTo_p_wxObject, 0, 0},  {&_swigt__p_wxWindowDestroyEvent, _p_wxWindowDestroyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxNavigationKeyEvent, _p_wxNavigationKeyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxKeyEvent, _p_wxKeyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSashEvent, _p_wxSashEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyVListBox, _p_wxPyVListBoxTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyHtmlListBox, _p_wxPyHtmlListBoxTo_p_wxObject, 0, 0},  {&_swigt__p_wxFontData, _p_wxFontDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintData, _p_wxPrintDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPanel, _p_wxPyPanelTo_p_wxObject, 0, 0},  {&_swigt__p_wxQueryLayoutInfoEvent, _p_wxQueryLayoutInfoEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxObject, 0, 0},  {&_swigt__p_wxFileSystem, _p_wxFileSystemTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintPreview, _p_wxPrintPreviewTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPrintPreview, _p_wxPyPrintPreviewTo_p_wxObject, 0, 0},  {&_swigt__p_wxLayoutConstraints, _p_wxLayoutConstraintsTo_p_wxObject, 0, 0},  {&_swigt__p_wxSizer, _p_wxSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxBoxSizer, _p_wxBoxSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxStaticBoxSizer, _p_wxStaticBoxSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxGridBagSizer, _p_wxGridBagSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPaintEvent, _p_wxPaintEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxNcPaintEvent, _p_wxNcPaintEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFSFile, _p_wxFSFileTo_p_wxObject, 0, 0},  {&_swigt__p_wxClipboard, _p_wxClipboardTo_p_wxObject, 0, 0},  {&_swigt__p_wxSetCursorEvent, _p_wxSetCursorEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplitterEvent, _p_wxSplitterEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxTimerEvent, _p_wxTimerEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxBusyInfo, _p_wxBusyInfoTo_p_wxObject, 0, 0},  {&_swigt__p_wxSizerItem, _p_wxSizerItemTo_p_wxObject, 0, 0},  {&_swigt__p_wxGBSizerItem, _p_wxGBSizerItemTo_p_wxObject, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxPageSetupDialog, _p_wxPageSetupDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintDialog, _p_wxPrintDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxNotifyEvent, _p_wxNotifyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyEvent, _p_wxPyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxToolTip, _p_wxToolTipTo_p_wxObject, 0, 0},  {&_swigt__p_wxPNMHandler, _p_wxPNMHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxJPEGHandler, _p_wxJPEGHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPCXHandler, _p_wxPCXHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxGIFHandler, _p_wxGIFHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPNGHandler, _p_wxPNGHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxANIHandler, _p_wxANIHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxCURHandler, _p_wxCURHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxICOHandler, _p_wxICOHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxBMPHandler, _p_wxBMPHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyImageHandler, _p_wxPyImageHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxImageHandler, _p_wxImageHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxXPMHandler, _p_wxXPMHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxTIFFHandler, _p_wxTIFFHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxEvtHandler, _p_wxEvtHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxShowEvent, _p_wxShowEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyVScrolledWindow, _p_wxPyVScrolledWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxTipWindow, _p_wxTipWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPopupTransientWindow, _p_wxPyPopupTransientWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPopupWindow, _p_wxPopupWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSashLayoutWindow, _p_wxSashLayoutWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplashScreenWindow, _p_wxSplashScreenWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplitterWindow, _p_wxSplitterWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSashWindow, _p_wxSashWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxWindow, _p_wxWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxScrolledWindow, _p_wxScrolledWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxTopLevelWindow, _p_wxTopLevelWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxMDIClientWindow, _p_wxMDIClientWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyScrolledWindow, _p_wxPyScrolledWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxJoystickEvent, _p_wxJoystickEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaRightClickEvent, _p_wxMozillaRightClickEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFileHistory, _p_wxFileHistoryTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyWindow, _p_wxPyWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxMouseCaptureChangedEvent, _p_wxMouseCaptureChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSysColourChangedEvent, _p_wxSysColourChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxDisplayChangedEvent, _p_wxDisplayChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPaletteChangedEvent, _p_wxPaletteChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaBeforeLoadEvent, _p_wxMozillaBeforeLoadEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaLinkChangedEvent, _p_wxMozillaLinkChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaStateChangedEvent, _p_wxMozillaStateChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaSecurityChangedEvent, _p_wxMozillaSecurityChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaStatusChangedEvent, _p_wxMozillaStatusChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaTitleChangedEvent, _p_wxMozillaTitleChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPanel, _p_wxPanelTo_p_wxObject, 0, 0},  {&_swigt__p_wxScrollWinEvent, _p_wxScrollWinEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxTaskBarIconEvent, _p_wxTaskBarIconEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxContextMenuEvent, _p_wxContextMenuEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenuEvent, _p_wxMenuEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxCommandEvent, _p_wxCommandEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyCommandEvent, _p_wxPyCommandEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxStatusBar, _p_wxStatusBarTo_p_wxObject, 0, 0},  {&_swigt__p_wxDropFilesEvent, _p_wxDropFilesEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFocusEvent, _p_wxFocusEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxChildFocusEvent, _p_wxChildFocusEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxProcessEvent, _p_wxProcessEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaProgressEvent, _p_wxMozillaProgressEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenuBar, _p_wxMenuBarTo_p_wxObject, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxObject[] = {  {&_swigt__p_wxUpdateUIEvent, _p_wxUpdateUIEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPreviewCanvas, _p_wxPreviewCanvasTo_p_wxObject, 0, 0},  {&_swigt__p_wxEvent, _p_wxEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFindDialogEvent, _p_wxFindDialogEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxInitDialogEvent, _p_wxInitDialogEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxIndividualLayoutConstraint, _p_wxIndividualLayoutConstraintTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenuItem, _p_wxMenuItemTo_p_wxObject, 0, 0},  {&_swigt__p_wxImage, _p_wxImageTo_p_wxObject, 0, 0},  {&_swigt__p_wxPySizer, _p_wxPySizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxLayoutAlgorithm, _p_wxLayoutAlgorithmTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyTaskBarIcon, _p_wxPyTaskBarIconTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyApp, _p_wxPyAppTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaBrowser, _p_wxMozillaBrowserTo_p_wxObject, 0, 0},  {&_swigt__p_wxPreviewControlBar, _p_wxPreviewControlBarTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPreviewControlBar, _p_wxPyPreviewControlBarTo_p_wxObject, 0, 0},  {&_swigt__p_wxFindReplaceData, _p_wxFindReplaceDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxValidator, _p_wxValidatorTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyValidator, _p_wxPyValidatorTo_p_wxObject, 0, 0},  {&_swigt__p_wxCloseEvent, _p_wxCloseEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMouseEvent, _p_wxMouseEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxEraseEvent, _p_wxEraseEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxScrollEvent, _p_wxScrollEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintDialogData, _p_wxPrintDialogDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxPageSetupDialogData, _p_wxPageSetupDialogDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrinter, _p_wxPrinterTo_p_wxObject, 0, 0},  {&_swigt__p_wxControlWithItems, _p_wxControlWithItemsTo_p_wxObject, 0, 0},  {&_swigt__p_wxObject, 0, 0, 0},  {&_swigt__p_wxSystemOptions, _p_wxSystemOptionsTo_p_wxObject, 0, 0},  {&_swigt__p_wxGridSizer, _p_wxGridSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxFlexGridSizer, _p_wxFlexGridSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxAcceleratorTable, _p_wxAcceleratorTableTo_p_wxObject, 0, 0},  {&_swigt__p_wxControl, _p_wxControlTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyProcess, _p_wxPyProcessTo_p_wxObject, 0, 0},  {&_swigt__p_wxColourData, _p_wxColourDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxIdleEvent, _p_wxIdleEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxWindowCreateEvent, _p_wxWindowCreateEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxQueryNewPaletteEvent, _p_wxQueryNewPaletteEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMaximizeEvent, _p_wxMaximizeEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxIconizeEvent, _p_wxIconizeEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxActivateEvent, _p_wxActivateEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSizeEvent, _p_wxSizeEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMoveEvent, _p_wxMoveEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxDateEvent, _p_wxDateEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaLoadCompleteEvent, _p_wxMozillaLoadCompleteEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMouseCaptureLostEvent, _p_wxMouseCaptureLostEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxCalculateLayoutEvent, _p_wxCalculateLayoutEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyTimer, _p_wxPyTimerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPrintout, _p_wxPyPrintoutTo_p_wxObject, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxStdDialogButtonSizer, _p_wxStdDialogButtonSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenu, _p_wxMenuTo_p_wxObject, 0, 0},  {&_swigt__p_wxWindowDestroyEvent, _p_wxWindowDestroyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxNavigationKeyEvent, _p_wxNavigationKeyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxKeyEvent, _p_wxKeyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSashEvent, _p_wxSashEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyVListBox, _p_wxPyVListBoxTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyHtmlListBox, _p_wxPyHtmlListBoxTo_p_wxObject, 0, 0},  {&_swigt__p_wxSimpleHtmlListBox, _p_wxSimpleHtmlListBoxTo_p_wxObject, 0, 0},  {&_swigt__p_wxFontData, _p_wxFontDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintData, _p_wxPrintDataTo_p_wxObject, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPanel, _p_wxPyPanelTo_p_wxObject, 0, 0},  {&_swigt__p_wxQueryLayoutInfoEvent, _p_wxQueryLayoutInfoEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxObject, 0, 0},  {&_swigt__p_wxFileSystem, _p_wxFileSystemTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintPreview, _p_wxPrintPreviewTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPrintPreview, _p_wxPyPrintPreviewTo_p_wxObject, 0, 0},  {&_swigt__p_wxLayoutConstraints, _p_wxLayoutConstraintsTo_p_wxObject, 0, 0},  {&_swigt__p_wxStaticBoxSizer, _p_wxStaticBoxSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxBoxSizer, _p_wxBoxSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxSizer, _p_wxSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxGridBagSizer, _p_wxGridBagSizerTo_p_wxObject, 0, 0},  {&_swigt__p_wxNcPaintEvent, _p_wxNcPaintEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxClipboardTextEvent, _p_wxClipboardTextEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPaintEvent, _p_wxPaintEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFSFile, _p_wxFSFileTo_p_wxObject, 0, 0},  {&_swigt__p_wxClipboard, _p_wxClipboardTo_p_wxObject, 0, 0},  {&_swigt__p_wxSetCursorEvent, _p_wxSetCursorEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplitterEvent, _p_wxSplitterEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxTimerEvent, _p_wxTimerEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPowerEvent, _p_wxPowerEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxBusyInfo, _p_wxBusyInfoTo_p_wxObject, 0, 0},  {&_swigt__p_wxGBSizerItem, _p_wxGBSizerItemTo_p_wxObject, 0, 0},  {&_swigt__p_wxSizerItem, _p_wxSizerItemTo_p_wxObject, 0, 0},  {&_swigt__p_wxPrintDialog, _p_wxPrintDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxPageSetupDialog, _p_wxPageSetupDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxNotifyEvent, _p_wxNotifyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyEvent, _p_wxPyEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxToolTip, _p_wxToolTipTo_p_wxObject, 0, 0},  {&_swigt__p_wxEvtHandler, _p_wxEvtHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxTGAHandler, _p_wxTGAHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxTIFFHandler, _p_wxTIFFHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxXPMHandler, _p_wxXPMHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxImageHandler, _p_wxImageHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyImageHandler, _p_wxPyImageHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxBMPHandler, _p_wxBMPHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxICOHandler, _p_wxICOHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxCURHandler, _p_wxCURHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxANIHandler, _p_wxANIHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPNGHandler, _p_wxPNGHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxGIFHandler, _p_wxGIFHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPCXHandler, _p_wxPCXHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxJPEGHandler, _p_wxJPEGHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxPNMHandler, _p_wxPNMHandlerTo_p_wxObject, 0, 0},  {&_swigt__p_wxShowEvent, _p_wxShowEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSashLayoutWindow, _p_wxSashLayoutWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplashScreenWindow, _p_wxSplashScreenWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSplitterWindow, _p_wxSplitterWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxSashWindow, _p_wxSashWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxWindow, _p_wxWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxScrolledWindow, _p_wxScrolledWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxTopLevelWindow, _p_wxTopLevelWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxMDIClientWindow, _p_wxMDIClientWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyScrolledWindow, _p_wxPyScrolledWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPopupWindow, _p_wxPopupWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyPopupTransientWindow, _p_wxPyPopupTransientWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxTipWindow, _p_wxTipWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyVScrolledWindow, _p_wxPyVScrolledWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxJoystickEvent, _p_wxJoystickEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaRightClickEvent, _p_wxMozillaRightClickEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxNumberEntryDialog, _p_wxNumberEntryDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxObject, 0, 0},  {&_swigt__p_wxFileHistory, _p_wxFileHistoryTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyWindow, _p_wxPyWindowTo_p_wxObject, 0, 0},  {&_swigt__p_wxPaletteChangedEvent, _p_wxPaletteChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxDisplayChangedEvent, _p_wxDisplayChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMouseCaptureChangedEvent, _p_wxMouseCaptureChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxSysColourChangedEvent, _p_wxSysColourChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaBeforeLoadEvent, _p_wxMozillaBeforeLoadEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaLinkChangedEvent, _p_wxMozillaLinkChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaStateChangedEvent, _p_wxMozillaStateChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaSecurityChangedEvent, _p_wxMozillaSecurityChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaStatusChangedEvent, _p_wxMozillaStatusChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaTitleChangedEvent, _p_wxMozillaTitleChangedEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPanel, _p_wxPanelTo_p_wxObject, 0, 0},  {&_swigt__p_wxScrollWinEvent, _p_wxScrollWinEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxTaskBarIconEvent, _p_wxTaskBarIconEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxContextMenuEvent, _p_wxContextMenuEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenuEvent, _p_wxMenuEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxCommandEvent, _p_wxCommandEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxPyCommandEvent, _p_wxPyCommandEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxStatusBar, _p_wxStatusBarTo_p_wxObject, 0, 0},  {&_swigt__p_wxDropFilesEvent, _p_wxDropFilesEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxFocusEvent, _p_wxFocusEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxChildFocusEvent, _p_wxChildFocusEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxProcessEvent, _p_wxProcessEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMozillaProgressEvent, _p_wxMozillaProgressEventTo_p_wxObject, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxObject, 0, 0},  {&_swigt__p_wxMenuBar, _p_wxMenuBarTo_p_wxObject, 0, 0},{0, 0, 0, 0}};
 static swig_cast_info _swigc__p_wxPaperSize[] = {  {&_swigt__p_wxPaperSize, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxTopLevelWindow[] = {  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxTopLevelWindow, 0, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxTopLevelWindow, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__p_wxWindow[] = {  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPanel, _p_wxPyPanelTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMenuBar, _p_wxMenuBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMozillaBrowser, _p_wxMozillaBrowserTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPanel, _p_wxPanelTo_p_wxWindow, 0, 0},  {&_swigt__p_wxStatusBar, _p_wxStatusBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSashLayoutWindow, _p_wxSashLayoutWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxScrolledWindow, _p_wxScrolledWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxTopLevelWindow, _p_wxTopLevelWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSplashScreenWindow, _p_wxSplashScreenWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSplitterWindow, _p_wxSplitterWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSashWindow, _p_wxSashWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMDIClientWindow, _p_wxMDIClientWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyScrolledWindow, _p_wxPyScrolledWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxWindow, 0, 0, 0},  {&_swigt__p_wxPopupWindow, _p_wxPopupWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPopupTransientWindow, _p_wxPyPopupTransientWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxTipWindow, _p_wxTipWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyVScrolledWindow, _p_wxPyVScrolledWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxControl, _p_wxControlTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxControlWithItems, _p_wxControlWithItemsTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyWindow, _p_wxPyWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPreviewCanvas, _p_wxPreviewCanvasTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyHtmlListBox, _p_wxPyHtmlListBoxTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyVListBox, _p_wxPyVListBoxTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPreviewControlBar, _p_wxPreviewControlBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPreviewControlBar, _p_wxPyPreviewControlBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxWindow, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__ptrdiff_t[] = {  {&_swigt__ptrdiff_t, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__std__ptrdiff_t[] = {  {&_swigt__std__ptrdiff_t, 0, 0, 0},{0, 0, 0, 0}};
-static swig_cast_info _swigc__unsigned_int[] = {  {&_swigt__unsigned_int, 0, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxTopLevelWindow[] = {  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxTopLevelWindow, 0, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxNumberEntryDialog, _p_wxNumberEntryDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxTopLevelWindow, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxTopLevelWindow, 0, 0},{0, 0, 0, 0}};
+static swig_cast_info _swigc__p_wxWindow[] = {  {&_swigt__p_wxSplashScreen, _p_wxSplashScreenTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMiniFrame, _p_wxMiniFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPanel, _p_wxPyPanelTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMenuBar, _p_wxMenuBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMozillaBrowser, _p_wxMozillaBrowserTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMultiChoiceDialog, _p_wxMultiChoiceDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFileDialog, _p_wxFileDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFindReplaceDialog, _p_wxFindReplaceDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxProgressDialog, _p_wxProgressDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMessageDialog, _p_wxMessageDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxNumberEntryDialog, _p_wxNumberEntryDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPasswordEntryDialog, _p_wxPasswordEntryDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxTextEntryDialog, _p_wxTextEntryDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSingleChoiceDialog, _p_wxSingleChoiceDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPanel, _p_wxPanelTo_p_wxWindow, 0, 0},  {&_swigt__p_wxStatusBar, _p_wxStatusBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxScrolledWindow, _p_wxScrolledWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxTopLevelWindow, _p_wxTopLevelWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSplashScreenWindow, _p_wxSplashScreenWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSplitterWindow, _p_wxSplitterWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSashWindow, _p_wxSashWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMDIClientWindow, _p_wxMDIClientWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyScrolledWindow, _p_wxPyScrolledWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxWindow, 0, 0, 0},  {&_swigt__p_wxSashLayoutWindow, _p_wxSashLayoutWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPopupWindow, _p_wxPopupWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPopupTransientWindow, _p_wxPyPopupTransientWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxTipWindow, _p_wxTipWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyVScrolledWindow, _p_wxPyVScrolledWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPreviewFrame, _p_wxPyPreviewFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPreviewFrame, _p_wxPreviewFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxControl, _p_wxControlTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMDIChildFrame, _p_wxMDIChildFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxControlWithItems, _p_wxControlWithItemsTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMozillaWindow, _p_wxMozillaWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyWindow, _p_wxPyWindowTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPreviewCanvas, _p_wxPreviewCanvasTo_p_wxWindow, 0, 0},  {&_swigt__p_wxSimpleHtmlListBox, _p_wxSimpleHtmlListBoxTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyHtmlListBox, _p_wxPyHtmlListBoxTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyVListBox, _p_wxPyVListBoxTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPreviewControlBar, _p_wxPreviewControlBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxPyPreviewControlBar, _p_wxPyPreviewControlBarTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFrame, _p_wxFrameTo_p_wxWindow, 0, 0},  {&_swigt__p_wxFontDialog, _p_wxFontDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxDirDialog, _p_wxDirDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxColourDialog, _p_wxColourDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxDialog, _p_wxDialogTo_p_wxWindow, 0, 0},  {&_swigt__p_wxMDIParentFrame, _p_wxMDIParentFrameTo_p_wxWindow, 0, 0},{0, 0, 0, 0}};
 
 static swig_cast_info *swig_cast_initial[] = {
   _swigc__p_char,
@@ -7533,6 +8588,7 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxCalculateLayoutEvent,
   _swigc__p_wxChildFocusEvent,
   _swigc__p_wxClipboard,
+  _swigc__p_wxClipboardTextEvent,
   _swigc__p_wxCloseEvent,
   _swigc__p_wxColourData,
   _swigc__p_wxColourDialog,
@@ -7588,6 +8644,7 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxMessageDialog,
   _swigc__p_wxMiniFrame,
   _swigc__p_wxMouseCaptureChangedEvent,
+  _swigc__p_wxMouseCaptureLostEvent,
   _swigc__p_wxMouseEvent,
   _swigc__p_wxMoveEvent,
   _swigc__p_wxMozillaBeforeLoadEvent,
@@ -7606,6 +8663,7 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxNavigationKeyEvent,
   _swigc__p_wxNcPaintEvent,
   _swigc__p_wxNotifyEvent,
+  _swigc__p_wxNumberEntryDialog,
   _swigc__p_wxObject,
   _swigc__p_wxPCXHandler,
   _swigc__p_wxPNGHandler,
@@ -7618,6 +8676,7 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxPaperSize,
   _swigc__p_wxPasswordEntryDialog,
   _swigc__p_wxPopupWindow,
+  _swigc__p_wxPowerEvent,
   _swigc__p_wxPreviewCanvas,
   _swigc__p_wxPreviewControlBar,
   _swigc__p_wxPreviewFrame,
@@ -7658,6 +8717,7 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxScrolledWindow,
   _swigc__p_wxSetCursorEvent,
   _swigc__p_wxShowEvent,
+  _swigc__p_wxSimpleHtmlListBox,
   _swigc__p_wxSingleChoiceDialog,
   _swigc__p_wxSizeEvent,
   _swigc__p_wxSizer,
@@ -7671,6 +8731,7 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxStdDialogButtonSizer,
   _swigc__p_wxSysColourChangedEvent,
   _swigc__p_wxSystemOptions,
+  _swigc__p_wxTGAHandler,
   _swigc__p_wxTIFFHandler,
   _swigc__p_wxTaskBarIconEvent,
   _swigc__p_wxTextEntryDialog,
@@ -7684,9 +8745,6 @@ static swig_cast_info *swig_cast_initial
   _swigc__p_wxWindowCreateEvent,
   _swigc__p_wxWindowDestroyEvent,
   _swigc__p_wxXPMHandler,
-  _swigc__ptrdiff_t,
-  _swigc__std__ptrdiff_t,
-  _swigc__unsigned_int,
 };
 
 
@@ -7698,7 +8756,7 @@ static swig_const_info swig_const_table[
 #ifdef __cplusplus
 }
 #endif
-/*************************************************************************
+/* -----------------------------------------------------------------------------
  * Type initialization:
  * This problem is tough by the requirement that no dynamic 
  * memory is used. Also, since swig_type_info structures store pointers to 
@@ -7710,7 +8768,7 @@ static swig_const_info swig_const_table[
  * swig_module, and does all the lookup, filling in the swig_module.types
  * array with the correct data and linking the correct swig_cast_info
  * structures together.
-
+ *
  * The generated swig_type_info structures are assigned staticly to an initial 
  * array. We just loop though that array, and handle each type individually.
  * First we lookup if this type has been already loaded, and if so, use the
@@ -7724,7 +8782,7 @@ static swig_const_info swig_const_table[
  * we find the array of casts associated with the type, and loop through it 
  * adding the casts to the list. The one last trick we need to do is making
  * sure the type pointer in the swig_cast_info struct is correct.
-
+ *
  * First off, we lookup the cast->type name to see if it is already loaded. 
  * There are three cases to handle:
  *  1) If the cast->type has already been loaded AND the type we are adding
@@ -7737,7 +8795,7 @@ static swig_const_info swig_const_table[
  *  3) Finally, if cast->type has not already been loaded, then we add that
  *     swig_cast_info to the linked list (because the cast->type) pointer will
  *     be correct.
-**/
+ * ----------------------------------------------------------------------------- */
 
 #ifdef __cplusplus
 extern "C" {
@@ -7752,124 +8810,124 @@ extern "C" {
 
 SWIGRUNTIME void
 SWIG_InitializeModule(void *clientdata) {
-    size_t i;
-    swig_module_info *module_head;
-    static int init_run = 0;
-    
-    clientdata = clientdata;
-    
-    if (init_run) return;
-    init_run = 1;
-    
-    /* Initialize the swig_module */
-    swig_module.type_initial = swig_type_initial;
-    swig_module.cast_initial = swig_cast_initial;
-    
-    /* Try and load any already created modules */
-    module_head = SWIG_GetModule(clientdata);
-    if (module_head) {
-        swig_module.next = module_head->next;
-        module_head->next = &swig_module;
-    } else {
-        /* This is the first module loaded */
-        swig_module.next = &swig_module;
-        SWIG_SetModule(clientdata, &swig_module);
-    }
-    
-    /* Now work on filling in swig_module.types */
+  size_t i;
+  swig_module_info *module_head;
+  static int init_run = 0;
+  
+  clientdata = clientdata;
+  
+  if (init_run) return;
+  init_run = 1;
+  
+  /* Initialize the swig_module */
+  swig_module.type_initial = swig_type_initial;
+  swig_module.cast_initial = swig_cast_initial;
+  
+  /* Try and load any already created modules */
+  module_head = SWIG_GetModule(clientdata);
+  if (module_head) {
+    swig_module.next = module_head->next;
+    module_head->next = &swig_module;
+  } else {
+    /* This is the first module loaded */
+    swig_module.next = &swig_module;
+    SWIG_SetModule(clientdata, &swig_module);
+  }
+  
+  /* Now work on filling in swig_module.types */
 #ifdef SWIGRUNTIME_DEBUG
-    printf("SWIG_InitializeModule: size %d\n", swig_module.size);
+  printf("SWIG_InitializeModule: size %d\n", swig_module.size);
 #endif
-    for (i = 0; i < swig_module.size; ++i) {
-        swig_type_info *type = 0;
-        swig_type_info *ret;
-        swig_cast_info *cast;
-        
+  for (i = 0; i < swig_module.size; ++i) {
+    swig_type_info *type = 0;
+    swig_type_info *ret;
+    swig_cast_info *cast;
+    
 #ifdef SWIGRUNTIME_DEBUG
-        printf("SWIG_InitializeModule: type %d %s\n", i, swig_module.type_initial[i]->name);
+    printf("SWIG_InitializeModule: type %d %s\n", i, swig_module.type_initial[i]->name);
 #endif
-        
-        /* if there is another module already loaded */
-        if (swig_module.next != &swig_module) {
-            type = SWIG_MangledTypeQueryModule(swig_module.next, &swig_module, swig_module.type_initial[i]->name);
-        }
-        if (type) {
-            /* Overwrite clientdata field */
+    
+    /* if there is another module already loaded */
+    if (swig_module.next != &swig_module) {
+      type = SWIG_MangledTypeQueryModule(swig_module.next, &swig_module, swig_module.type_initial[i]->name);
+    }
+    if (type) {
+      /* Overwrite clientdata field */
 #ifdef SWIGRUNTIME_DEBUG
-            printf("SWIG_InitializeModule: found type %s\n", type->name);
+      printf("SWIG_InitializeModule: found type %s\n", type->name);
 #endif
-            if (swig_module.type_initial[i]->clientdata) {
-                type->clientdata = swig_module.type_initial[i]->clientdata;
+      if (swig_module.type_initial[i]->clientdata) {
+        type->clientdata = swig_module.type_initial[i]->clientdata;
 #ifdef SWIGRUNTIME_DEBUG
-                printf("SWIG_InitializeModule: found and overwrite type %s \n", type->name);
+        printf("SWIG_InitializeModule: found and overwrite type %s \n", type->name);
 #endif
-            }
-        } else {
-            type = swig_module.type_initial[i];
-        }
-        
-        /* Insert casting types */
-        cast = swig_module.cast_initial[i];
-        while (cast->type) {
-            /* Don't need to add information already in the list */
-            ret = 0;
+      }
+    } else {
+      type = swig_module.type_initial[i];
+    }
+    
+    /* Insert casting types */
+    cast = swig_module.cast_initial[i];
+    while (cast->type) {
+      /* Don't need to add information already in the list */
+      ret = 0;
 #ifdef SWIGRUNTIME_DEBUG
-            printf("SWIG_InitializeModule: look cast %s\n", cast->type->name);
+      printf("SWIG_InitializeModule: look cast %s\n", cast->type->name);
 #endif
-            if (swig_module.next != &swig_module) {
-                ret = SWIG_MangledTypeQueryModule(swig_module.next, &swig_module, cast->type->name);
+      if (swig_module.next != &swig_module) {
+        ret = SWIG_MangledTypeQueryModule(swig_module.next, &swig_module, cast->type->name);
 #ifdef SWIGRUNTIME_DEBUG
-                if (ret) printf("SWIG_InitializeModule: found cast %s\n", ret->name);
+        if (ret) printf("SWIG_InitializeModule: found cast %s\n", ret->name);
 #endif
-            }
-            if (ret) {
-                if (type == swig_module.type_initial[i]) {
+      }
+      if (ret) {
+        if (type == swig_module.type_initial[i]) {
 #ifdef SWIGRUNTIME_DEBUG
-                    printf("SWIG_InitializeModule: skip old type %s\n", ret->name);
+          printf("SWIG_InitializeModule: skip old type %s\n", ret->name);
 #endif
-                    cast->type = ret;
-                    ret = 0;
-                } else {
-                    /* Check for casting already in the list */
-                    swig_cast_info *ocast = SWIG_TypeCheck(ret->name, type);
+          cast->type = ret;
+          ret = 0;
+        } else {
+          /* Check for casting already in the list */
+          swig_cast_info *ocast = SWIG_TypeCheck(ret->name, type);
 #ifdef SWIGRUNTIME_DEBUG
-                    if (ocast) printf("SWIG_InitializeModule: skip old cast %s\n", ret->name);
+          if (ocast) printf("SWIG_InitializeModule: skip old cast %s\n", ret->name);
 #endif
-                    if (!ocast) ret = 0;
-                }
-            }
-            
-            if (!ret) {
+          if (!ocast) ret = 0;
+        }
+      }
+      
+      if (!ret) {
 #ifdef SWIGRUNTIME_DEBUG
-                printf("SWIG_InitializeModule: adding cast %s\n", cast->type->name);
+        printf("SWIG_InitializeModule: adding cast %s\n", cast->type->name);
 #endif
-                if (type->cast) {
-                    type->cast->prev = cast;
-                    cast->next = type->cast;
-                }
-                type->cast = cast;
-            }
-            cast++;
+        if (type->cast) {
+          type->cast->prev = cast;
+          cast->next = type->cast;
         }
-        /* Set entry in modules->types array equal to the type */
-        swig_module.types[i] = type;
+        type->cast = cast;
+      }
+      cast++;
     }
-    swig_module.types[i] = 0;
-    
+    /* Set entry in modules->types array equal to the type */
+    swig_module.types[i] = type;
+  }
+  swig_module.types[i] = 0;
+  
 #ifdef SWIGRUNTIME_DEBUG
-    printf("**** SWIG_InitializeModule: Cast List ******\n");
-    for (i = 0; i < swig_module.size; ++i) {
-        int j = 0;
-        swig_cast_info *cast = swig_module.cast_initial[i];
-        printf("SWIG_InitializeModule: type %d %s\n", i, swig_module.type_initial[i]->name);
-        while (cast->type) {
-            printf("SWIG_InitializeModule: cast type %s\n", cast->type->name);
-            cast++;
-            ++j;
-        }
-        printf("---- Total casts: %d\n",j);
+  printf("**** SWIG_InitializeModule: Cast List ******\n");
+  for (i = 0; i < swig_module.size; ++i) {
+    int j = 0;
+    swig_cast_info *cast = swig_module.cast_initial[i];
+    printf("SWIG_InitializeModule: type %d %s\n", i, swig_module.type_initial[i]->name);
+    while (cast->type) {
+      printf("SWIG_InitializeModule: cast type %s\n", cast->type->name);
+      cast++;
+      ++j;
     }
-    printf("**** SWIG_InitializeModule: Cast List ******\n");
+    printf("---- Total casts: %d\n",j);
+  }
+  printf("**** SWIG_InitializeModule: Cast List ******\n");
 #endif
 }
 
@@ -7880,31 +8938,31 @@ SWIG_InitializeModule(void *clientdata) 
 */
 SWIGRUNTIME void
 SWIG_PropagateClientData(void) {
-    size_t i;
-    swig_cast_info *equiv;
-    static int init_run = 0;
-    
-    if (init_run) return;
-    init_run = 1;
-    
-    for (i = 0; i < swig_module.size; i++) {
-        if (swig_module.types[i]->clientdata) {
-            equiv = swig_module.types[i]->cast;
-            while (equiv) {
-                if (!equiv->converter) {
-                    if (equiv->type && !equiv->type->clientdata)
-                    SWIG_TypeClientData(equiv->type, swig_module.types[i]->clientdata);
-                }
-                equiv = equiv->next;
-            }
+  size_t i;
+  swig_cast_info *equiv;
+  static int init_run = 0;
+  
+  if (init_run) return;
+  init_run = 1;
+  
+  for (i = 0; i < swig_module.size; i++) {
+    if (swig_module.types[i]->clientdata) {
+      equiv = swig_module.types[i]->cast;
+      while (equiv) {
+        if (!equiv->converter) {
+          if (equiv->type && !equiv->type->clientdata)
+          SWIG_TypeClientData(equiv->type, swig_module.types[i]->clientdata);
         }
+        equiv = equiv->next;
+      }
     }
+  }
 }
 
 #ifdef __cplusplus
 #if 0
 {
-    /* c-mode */
+  /* c-mode */
 #endif
 }
 #endif
@@ -7914,251 +8972,258 @@ SWIG_PropagateClientData(void) {
 #ifdef __cplusplus
 extern "C" {
 #endif
-    
-    /* Python-specific SWIG API */
+  
+  /* Python-specific SWIG API */
 #define SWIG_newvarlink()                             SWIG_Python_newvarlink()
 #define SWIG_addvarlink(p, name, get_attr, set_attr)  SWIG_Python_addvarlink(p, name, get_attr, set_attr)
 #define SWIG_InstallConstants(d, constants)           SWIG_Python_InstallConstants(d, constants)
-    
-    /* -----------------------------------------------------------------------------
-     * global variable support code.
-     * ----------------------------------------------------------------------------- */
-    
-    typedef struct swig_globalvar {
-        char       *name;                  /* Name of global variable */
-        PyObject *(*get_attr)(void);       /* Return the current value */
-        int       (*set_attr)(PyObject *); /* Set the value */
-        struct swig_globalvar *next;
-    } swig_globalvar;
-    
-    typedef struct swig_varlinkobject {
-        PyObject_HEAD
-        swig_globalvar *vars;
-    } swig_varlinkobject;
-    
-    SWIGINTERN PyObject *
-    swig_varlink_repr(swig_varlinkobject *v) {
-        v = v;
-        return PyString_FromString("<Swig global variables>");
+  
+  /* -----------------------------------------------------------------------------
+   * global variable support code.
+   * ----------------------------------------------------------------------------- */
+  
+  typedef struct swig_globalvar {
+    char       *name;                  /* Name of global variable */
+    PyObject *(*get_attr)(void);       /* Return the current value */
+    int       (*set_attr)(PyObject *); /* Set the value */
+    struct swig_globalvar *next;
+  } swig_globalvar;
+  
+  typedef struct swig_varlinkobject {
+    PyObject_HEAD
+    swig_globalvar *vars;
+  } swig_varlinkobject;
+  
+  SWIGINTERN PyObject *
+  swig_varlink_repr(swig_varlinkobject *SWIGUNUSEDPARM(v)) {
+    return PyString_FromString("<Swig global variables>");
+  }
+  
+  SWIGINTERN PyObject *
+  swig_varlink_str(swig_varlinkobject *v) {
+    PyObject *str = PyString_FromString("(");
+    swig_globalvar  *var;
+    for (var = v->vars; var; var=var->next) {
+      PyString_ConcatAndDel(&str,PyString_FromString(var->name));
+      if (var->next) PyString_ConcatAndDel(&str,PyString_FromString(", "));
     }
-    
-    SWIGINTERN int
-    swig_varlink_print(swig_varlinkobject *v, FILE *fp, int flags) {
-        swig_globalvar  *var;
-        flags = flags;
-        fprintf(fp,"Swig global variables { ");
-        for (var = v->vars; var; var=var->next) {
-            fprintf(fp,"%s", var->name);
-            if (var->next) fprintf(fp,", ");
-        }
-        fprintf(fp," }\n");
-        return 0;
+    PyString_ConcatAndDel(&str,PyString_FromString(")"));
+    return str;
+  }
+  
+  SWIGINTERN int
+  swig_varlink_print(swig_varlinkobject *v, FILE *fp, int SWIGUNUSEDPARM(flags)) {
+    PyObject *str = swig_varlink_str(v);
+    fprintf(fp,"Swig global variables ");
+    fprintf(fp,"%s\n", PyString_AsString(str));
+    Py_DECREF(str);
+    return 0;
+  }
+  
+  SWIGINTERN void
+  swig_varlink_dealloc(swig_varlinkobject *v) {
+    swig_globalvar *var = v->vars;
+    while (var) {
+      swig_globalvar *n = var->next;
+      free(var->name);
+      free(var);
+      var = n;
     }
-    
-    SWIGINTERN PyObject *
-    swig_varlink_getattr(swig_varlinkobject *v, char *n) {
-        swig_globalvar *var = v->vars;
-        while (var) {
-            if (strcmp(var->name,n) == 0) {
-                return (*var->get_attr)();
-            }
-            var = var->next;
-        }
-        PyErr_SetString(PyExc_NameError,"Unknown C global variable");
-        return NULL;
+  }
+  
+  SWIGINTERN PyObject *
+  swig_varlink_getattr(swig_varlinkobject *v, char *n) {
+    PyObject *res = NULL;
+    swig_globalvar *var = v->vars;
+    while (var) {
+      if (strcmp(var->name,n) == 0) {
+        res = (*var->get_attr)();
+        break;
+      }
+      var = var->next;
     }
-    
-    SWIGINTERN int
-    swig_varlink_setattr(swig_varlinkobject *v, char *n, PyObject *p) {
-        swig_globalvar *var = v->vars;
-        while (var) {
-            if (strcmp(var->name,n) == 0) {
-                return (*var->set_attr)(p);
-            }
-            var = var->next;
-        }
-        PyErr_SetString(PyExc_NameError,"Unknown C global variable");
-        return 1;
+    if (res == NULL && !PyErr_Occurred()) {
+      PyErr_SetString(PyExc_NameError,"Unknown C global variable");
     }
-    
-    SWIGINTERN PyTypeObject*
-    swig_varlink_type(void) {
-        static char varlink__doc__[] = "Swig var link object";
-        static PyTypeObject varlink_type
-#if !defined(__cplusplus)
-        ;
-        static int type_init = 0;  
-        if (!type_init) {
-            PyTypeObject tmp
-#endif
-            = {
-                PyObject_HEAD_INIT(&PyType_Type)
-                0,                                  /* Number of items in variable part (ob_size) */
-                (char *)"swigvarlink",              /* Type name (tp_name) */
-                sizeof(swig_varlinkobject),         /* Basic size (tp_basicsize) */
-                0,                                  /* Itemsize (tp_itemsize) */
-                0,                                  /* Deallocator (tp_dealloc) */ 
-                (printfunc) swig_varlink_print,     /* Print (tp_print) */
-                (getattrfunc) swig_varlink_getattr, /* get attr (tp_getattr) */
-                (setattrfunc) swig_varlink_setattr, /* Set attr (tp_setattr) */
-                0,                                  /* tp_compare */
-                (reprfunc) swig_varlink_repr,       /* tp_repr */
-                0,                                  /* tp_as_number */
-                0,                                  /* tp_as_sequence */
-                0,                                  /* tp_as_mapping */
-                0,                                  /* tp_hash */
-                0,                                  /* tp_call */
-                0,                                  /* tp_str */
-                0,                                  /* tp_getattro */
-                0,                                  /* tp_setattro */
-                0,                                  /* tp_as_buffer */
-                0,                                  /* tp_flags */
-                varlink__doc__,                     /* tp_doc */
-#if PY_VERSION_HEX >= 0x02000000
-                0,                                  /* tp_traverse */
-                0,                                  /* tp_clear */
-#endif
-#if PY_VERSION_HEX >= 0x02010000
-                0,                                  /* tp_richcompare */
-                0,                                  /* tp_weaklistoffset */
-#endif
+    return res;
+  }
+  
+  SWIGINTERN int
+  swig_varlink_setattr(swig_varlinkobject *v, char *n, PyObject *p) {
+    int res = 1;
+    swig_globalvar *var = v->vars;
+    while (var) {
+      if (strcmp(var->name,n) == 0) {
+        res = (*var->set_attr)(p);
+        break;
+      }
+      var = var->next;
+    }
+    if (res == 1 && !PyErr_Occurred()) {
+      PyErr_SetString(PyExc_NameError,"Unknown C global variable");
+    }
+    return res;
+  }
+  
+  SWIGINTERN PyTypeObject*
+  swig_varlink_type(void) {
+    static char varlink__doc__[] = "Swig var link object";
+    static PyTypeObject varlink_type;
+    static int type_init = 0;  
+    if (!type_init) {
+      const PyTypeObject tmp
+      = {
+        PyObject_HEAD_INIT(NULL)
+        0,                                  /* Number of items in variable part (ob_size) */
+        (char *)"swigvarlink",              /* Type name (tp_name) */
+        sizeof(swig_varlinkobject),         /* Basic size (tp_basicsize) */
+        0,                                  /* Itemsize (tp_itemsize) */
+        (destructor) swig_varlink_dealloc,   /* Deallocator (tp_dealloc) */ 
+        (printfunc) swig_varlink_print,     /* Print (tp_print) */
+        (getattrfunc) swig_varlink_getattr, /* get attr (tp_getattr) */
+        (setattrfunc) swig_varlink_setattr, /* Set attr (tp_setattr) */
+        0,                                  /* tp_compare */
+        (reprfunc) swig_varlink_repr,       /* tp_repr */
+        0,                                  /* tp_as_number */
+        0,                                  /* tp_as_sequence */
+        0,                                  /* tp_as_mapping */
+        0,                                  /* tp_hash */
+        0,                                  /* tp_call */
+        (reprfunc)swig_varlink_str,        /* tp_str */
+        0,                                  /* tp_getattro */
+        0,                                  /* tp_setattro */
+        0,                                  /* tp_as_buffer */
+        0,                                  /* tp_flags */
+        varlink__doc__,                     /* tp_doc */
+        0,                                  /* tp_traverse */
+        0,                                  /* tp_clear */
+        0,                                  /* tp_richcompare */
+        0,                                  /* tp_weaklistoffset */
 #if PY_VERSION_HEX >= 0x02020000
-                0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* tp_iter -> tp_weaklist */
+        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0, /* tp_iter -> tp_weaklist */
 #endif
 #if PY_VERSION_HEX >= 0x02030000
-                0,                                  /* tp_del */
+        0,                                  /* tp_del */
 #endif
 #ifdef COUNT_ALLOCS
-                0,0,0,0                             /* tp_alloc -> tp_next */
+        0,0,0,0                             /* tp_alloc -> tp_next */
 #endif
-            };
-#if !defined(__cplusplus)
-            varlink_type = tmp;
-            type_init = 1;
-        }
-#endif
-        return &varlink_type;
+      };
+      varlink_type = tmp;
+      varlink_type.ob_type = &PyType_Type;
+      type_init = 1;
     }
-    
-    /* Create a variable linking object for use later */
-    SWIGINTERN PyObject *
-    SWIG_Python_newvarlink(void) {
-        swig_varlinkobject *result = PyObject_NEW(swig_varlinkobject, swig_varlink_type());
-        if (result) {
-            result->vars = 0;
-        }
-        return ((PyObject*) result);
+    return &varlink_type;
+  }
+  
+  /* Create a variable linking object for use later */
+  SWIGINTERN PyObject *
+  SWIG_Python_newvarlink(void) {
+    swig_varlinkobject *result = PyObject_NEW(swig_varlinkobject, swig_varlink_type());
+    if (result) {
+      result->vars = 0;
     }
-    
-    SWIGINTERN void 
-    SWIG_Python_addvarlink(PyObject *p, char *name, PyObject *(*get_attr)(void), int (*set_attr)(PyObject *p)) {
-        swig_varlinkobject *v = (swig_varlinkobject *) p;
-        swig_globalvar *gv = (swig_globalvar *) malloc(sizeof(swig_globalvar));
-        if (gv) {
-            size_t size = strlen(name)+1;
-            gv->name = (char *)malloc(size);
-            if (gv->name) {
-                strncpy(gv->name,name,size);
-                gv->get_attr = get_attr;
-                gv->set_attr = set_attr;
-                gv->next = v->vars;
-            }
-        }
-        v->vars = gv;
+    return ((PyObject*) result);
+  }
+  
+  SWIGINTERN void 
+  SWIG_Python_addvarlink(PyObject *p, char *name, PyObject *(*get_attr)(void), int (*set_attr)(PyObject *p)) {
+    swig_varlinkobject *v = (swig_varlinkobject *) p;
+    swig_globalvar *gv = (swig_globalvar *) malloc(sizeof(swig_globalvar));
+    if (gv) {
+      size_t size = strlen(name)+1;
+      gv->name = (char *)malloc(size);
+      if (gv->name) {
+        strncpy(gv->name,name,size);
+        gv->get_attr = get_attr;
+        gv->set_attr = set_attr;
+        gv->next = v->vars;
+      }
     }
-    
-    /* -----------------------------------------------------------------------------
-     * constants/methods manipulation
-     * ----------------------------------------------------------------------------- */
-    
-    /* Install Constants */
-    SWIGINTERN void
-    SWIG_Python_InstallConstants(PyObject *d, swig_const_info constants[]) {
-        PyObject *obj = 0;
-        size_t i;
-        for (i = 0; constants[i].type; ++i) {
-            switch(constants[i].type) {
-                case SWIG_PY_INT:
-                obj = PyInt_FromLong(constants[i].lvalue);
-                break;
-                case SWIG_PY_FLOAT:
-                obj = PyFloat_FromDouble(constants[i].dvalue);
-                break;
-                case SWIG_PY_STRING:
-                if (constants[i].pvalue) {
-                    obj = PyString_FromString((char *) constants[i].pvalue);
-                } else {
-                    Py_INCREF(Py_None);
-                    obj = Py_None;
-                }
-                break;
-                case SWIG_PY_POINTER:
-                obj = SWIG_NewPointerObj(constants[i].pvalue, *(constants[i]).ptype,0);
-                break;
-                case SWIG_PY_BINARY:
-                obj = SWIG_NewPackedObj(constants[i].pvalue, constants[i].lvalue, *(constants[i].ptype));
-                break;
-                default:
-                obj = 0;
-                break;
-            }
-            if (obj) {
-                PyDict_SetItemString(d,constants[i].name,obj);
-                Py_DECREF(obj);
-            }
-        }
+    v->vars = gv;
+  }
+  
+  SWIGINTERN PyObject *
+  SWIG_globals() {
+    static PyObject *_SWIG_globals = 0; 
+    if (!_SWIG_globals) _SWIG_globals = SWIG_newvarlink();  
+    return _SWIG_globals;
+  }
+  
+  /* -----------------------------------------------------------------------------
+   * constants/methods manipulation
+   * ----------------------------------------------------------------------------- */
+  
+  /* Install Constants */
+  SWIGINTERN void
+  SWIG_Python_InstallConstants(PyObject *d, swig_const_info constants[]) {
+    PyObject *obj = 0;
+    size_t i;
+    for (i = 0; constants[i].type; ++i) {
+      switch(constants[i].type) {
+      case SWIG_PY_POINTER:
+        obj = SWIG_NewPointerObj(constants[i].pvalue, *(constants[i]).ptype,0);
+        break;
+      case SWIG_PY_BINARY:
+        obj = SWIG_NewPackedObj(constants[i].pvalue, constants[i].lvalue, *(constants[i].ptype));
+        break;
+      default:
+        obj = 0;
+        break;
+      }
+      if (obj) {
+        PyDict_SetItemString(d, constants[i].name, obj);
+        Py_DECREF(obj);
+      }
     }
-    
-    /* -----------------------------------------------------------------------------*/
-    /* Fix SwigMethods to carry the callback ptrs when needed */
-    /* -----------------------------------------------------------------------------*/
-    
-    SWIGINTERN void
-    SWIG_Python_FixMethods(PyMethodDef *methods,
+  }
+  
+  /* -----------------------------------------------------------------------------*/
+  /* Fix SwigMethods to carry the callback ptrs when needed */
+  /* -----------------------------------------------------------------------------*/
+  
+  SWIGINTERN void
+  SWIG_Python_FixMethods(PyMethodDef *methods,
     swig_const_info *const_table,
     swig_type_info **types,
     swig_type_info **types_initial) {
-        size_t i;
-        for (i = 0; methods[i].ml_name; ++i) {
-            char *c = methods[i].ml_doc;
-            if (c && (c = strstr(c, "swig_ptr: "))) {
-                int j;
-                swig_const_info *ci = 0;
-                char *name = c + 10;
-                for (j = 0; const_table[j].type; ++j) {
-                    if (strncmp(const_table[j].name, name, 
-                    strlen(const_table[j].name)) == 0) {
-                        ci = &(const_table[j]);
-                        break;
-                    }
-                }
-                if (ci) {
-                    size_t shift = (ci->ptype) - types;
-                    swig_type_info *ty = types_initial[shift];
-                    size_t ldoc = (c - methods[i].ml_doc);
-                    size_t lptr = strlen(ty->name)+2*sizeof(void*)+2;
-                    char *ndoc = (char*)malloc(ldoc + lptr + 10);
-                    if (ndoc) {
-                        char *buff = ndoc;
-                        void *ptr = (ci->type == SWIG_PY_POINTER) ? ci->pvalue : 0;
-                        if (ptr) {
-                            strncpy(buff, methods[i].ml_doc, ldoc);
-                            buff += ldoc;
-                            strncpy(buff, "swig_ptr: ", 10);
-                            buff += 10;
-                            SWIG_PackVoidPtr(buff, ptr, ty->name, lptr);
-                            methods[i].ml_doc = ndoc;
-                        }
-                    }
-                }
+    size_t i;
+    for (i = 0; methods[i].ml_name; ++i) {
+      const char *c = methods[i].ml_doc;
+      if (c && (c = strstr(c, "swig_ptr: "))) {
+        int j;
+        swig_const_info *ci = 0;
+        const char *name = c + 10;
+        for (j = 0; const_table[j].type; ++j) {
+          if (strncmp(const_table[j].name, name, 
+              strlen(const_table[j].name)) == 0) {
+            ci = &(const_table[j]);
+            break;
+          }
+        }
+        if (ci) {
+          size_t shift = (ci->ptype) - types;
+          swig_type_info *ty = types_initial[shift];
+          size_t ldoc = (c - methods[i].ml_doc);
+          size_t lptr = strlen(ty->name)+2*sizeof(void*)+2;
+          char *ndoc = (char*)malloc(ldoc + lptr + 10);
+          if (ndoc) {
+            char *buff = ndoc;
+            void *ptr = (ci->type == SWIG_PY_POINTER) ? ci->pvalue : 0;
+            if (ptr) {
+              strncpy(buff, methods[i].ml_doc, ldoc);
+              buff += ldoc;
+              strncpy(buff, "swig_ptr: ", 10);
+              buff += 10;
+              SWIG_PackVoidPtr(buff, ptr, ty->name, lptr);
+              methods[i].ml_doc = ndoc;
             }
+          }
         }
+      }
     }
-    
-    /* -----------------------------------------------------------------------------*
-     *  Initialize type list
-     * -----------------------------------------------------------------------------*/
-    
+  } 
+  
 #ifdef __cplusplus
 }
 #endif
@@ -8171,109 +9236,50 @@ extern "C" {
 extern "C"
 #endif
 SWIGEXPORT void SWIG_init(void) {
-    static PyObject *SWIG_globals = 0; 
-    PyObject *m, *d;
-    if (!SWIG_globals) SWIG_globals = SWIG_newvarlink();
-    
-    /* Fix SwigMethods to carry the callback ptrs when needed */
-    SWIG_Python_FixMethods(SwigMethods, swig_const_table, swig_types, swig_type_initial);
-    
-    m = Py_InitModule((char *) SWIG_name, SwigMethods);
-    d = PyModule_GetDict(m);
-    
-    SWIG_InitializeModule(0);
-    SWIG_InstallConstants(d,swig_const_table);
-    
-    PyDict_SetItemString(d,(char*)"cvar", SWIG_globals);
-    SWIG_addvarlink(SWIG_globals,(char*)"MOZ_MAJOR_VERSION",_wrap_MOZ_MAJOR_VERSION_get, _wrap_MOZ_MAJOR_VERSION_set);
-    SWIG_addvarlink(SWIG_globals,(char*)"MOZ_MINOR_VERSION",_wrap_MOZ_MINOR_VERSION_get, _wrap_MOZ_MINOR_VERSION_set);
-    SWIG_addvarlink(SWIG_globals,(char*)"MOZ_RELEASE_NUMBER",_wrap_MOZ_RELEASE_NUMBER_get, _wrap_MOZ_RELEASE_NUMBER_set);
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_START", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_START))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_NEGOTIATING", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_NEGOTIATING))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_REDIRECTING", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_REDIRECTING))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_TRANSFERRING", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_TRANSFERRING))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_STOP", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_STOP))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_IS_REQUEST", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_IS_REQUEST))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_IS_DOCUMENT", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_IS_DOCUMENT))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_IS_NETWORK", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_IS_NETWORK))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_STATE_IS_WINDOW", SWIG_From_int(static_cast<int >(wxMOZILLA_STATE_IS_WINDOW))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_IS_INSECURE", SWIG_From_int(static_cast<int >(wxMOZILLA_IS_INSECURE))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_IS_BROKEN", SWIG_From_int(static_cast<int >(wxMOZILLA_IS_BROKEN))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_IS_SECURE", SWIG_From_int(static_cast<int >(wxMOZILLA_IS_SECURE))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_SECURE_HIGH", SWIG_From_int(static_cast<int >(wxMOZILLA_SECURE_HIGH))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_SECURE_MED", SWIG_From_int(static_cast<int >(wxMOZILLA_SECURE_MED))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_SECURE_LOW", SWIG_From_int(static_cast<int >(wxMOZILLA_SECURE_LOW))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_CONTEXT_DOCUMENT", SWIG_From_int(static_cast<int >(wxMOZILLA_CONTEXT_DOCUMENT))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_CONTEXT_LINK", SWIG_From_int(static_cast<int >(wxMOZILLA_CONTEXT_LINK))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_CONTEXT_TEXT", SWIG_From_int(static_cast<int >(wxMOZILLA_CONTEXT_TEXT))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_CONTEXT_BACKGROUND_IMAGE", SWIG_From_int(static_cast<int >(wxMOZILLA_CONTEXT_BACKGROUND_IMAGE))); 
-    }
-    {
-        PyDict_SetItemString(d,"MOZILLA_CONTEXT_IMAGE", SWIG_From_int(static_cast<int >(wxMOZILLA_CONTEXT_IMAGE))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_BEFORE_LOAD", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_BEFORE_LOAD))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_URL_CHANGED", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_URL_CHANGED))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_STATE_CHANGED", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_STATE_CHANGED))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_SECURITY_CHANGED", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_SECURITY_CHANGED))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_STATUS_CHANGED", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_STATUS_CHANGED))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_TITLE_CHANGED", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_TITLE_CHANGED))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_LOAD_COMPLETE", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_LOAD_COMPLETE))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_PROGRESS", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_PROGRESS))); 
-    }
-    {
-        PyDict_SetItemString(d,"wxEVT_MOZILLA_RIGHT_CLICK", SWIG_From_int(static_cast<int >(wxEVT_MOZILLA_RIGHT_CLICK))); 
-    }
+  PyObject *m, *d;
+  
+  /* Fix SwigMethods to carry the callback ptrs when needed */
+  SWIG_Python_FixMethods(SwigMethods, swig_const_table, swig_types, swig_type_initial);
+  
+  m = Py_InitModule((char *) SWIG_name, SwigMethods);
+  d = PyModule_GetDict(m);
+  
+  SWIG_InitializeModule(0);
+  SWIG_InstallConstants(d,swig_const_table);
+  
+  
+  PyDict_SetItemString(d,(char*)"cvar", SWIG_globals());
+  SWIG_addvarlink(SWIG_globals(),(char*)"MOZ_MAJOR_VERSION",MOZ_MAJOR_VERSION_get, MOZ_MAJOR_VERSION_set);
+  SWIG_addvarlink(SWIG_globals(),(char*)"MOZ_MINOR_VERSION",MOZ_MINOR_VERSION_get, MOZ_MINOR_VERSION_set);
+  SWIG_addvarlink(SWIG_globals(),(char*)"MOZ_RELEASE_NUMBER",MOZ_RELEASE_NUMBER_get, MOZ_RELEASE_NUMBER_set);
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_START",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_START)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_NEGOTIATING",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_NEGOTIATING)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_REDIRECTING",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_REDIRECTING)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_TRANSFERRING",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_TRANSFERRING)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_STOP",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_STOP)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_IS_REQUEST",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_IS_REQUEST)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_IS_DOCUMENT",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_IS_DOCUMENT)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_IS_NETWORK",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_IS_NETWORK)));
+  SWIG_Python_SetConstant(d, "MOZILLA_STATE_IS_WINDOW",SWIG_From_int(static_cast< int >(wxMOZILLA_STATE_IS_WINDOW)));
+  SWIG_Python_SetConstant(d, "MOZILLA_IS_INSECURE",SWIG_From_int(static_cast< int >(wxMOZILLA_IS_INSECURE)));
+  SWIG_Python_SetConstant(d, "MOZILLA_IS_BROKEN",SWIG_From_int(static_cast< int >(wxMOZILLA_IS_BROKEN)));
+  SWIG_Python_SetConstant(d, "MOZILLA_IS_SECURE",SWIG_From_int(static_cast< int >(wxMOZILLA_IS_SECURE)));
+  SWIG_Python_SetConstant(d, "MOZILLA_SECURE_HIGH",SWIG_From_int(static_cast< int >(wxMOZILLA_SECURE_HIGH)));
+  SWIG_Python_SetConstant(d, "MOZILLA_SECURE_MED",SWIG_From_int(static_cast< int >(wxMOZILLA_SECURE_MED)));
+  SWIG_Python_SetConstant(d, "MOZILLA_SECURE_LOW",SWIG_From_int(static_cast< int >(wxMOZILLA_SECURE_LOW)));
+  SWIG_Python_SetConstant(d, "MOZILLA_CONTEXT_DOCUMENT",SWIG_From_int(static_cast< int >(wxMOZILLA_CONTEXT_DOCUMENT)));
+  SWIG_Python_SetConstant(d, "MOZILLA_CONTEXT_LINK",SWIG_From_int(static_cast< int >(wxMOZILLA_CONTEXT_LINK)));
+  SWIG_Python_SetConstant(d, "MOZILLA_CONTEXT_TEXT",SWIG_From_int(static_cast< int >(wxMOZILLA_CONTEXT_TEXT)));
+  SWIG_Python_SetConstant(d, "MOZILLA_CONTEXT_BACKGROUND_IMAGE",SWIG_From_int(static_cast< int >(wxMOZILLA_CONTEXT_BACKGROUND_IMAGE)));
+  SWIG_Python_SetConstant(d, "MOZILLA_CONTEXT_IMAGE",SWIG_From_int(static_cast< int >(wxMOZILLA_CONTEXT_IMAGE)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_BEFORE_LOAD",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_BEFORE_LOAD)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_URL_CHANGED",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_URL_CHANGED)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_STATE_CHANGED",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_STATE_CHANGED)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_SECURITY_CHANGED",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_SECURITY_CHANGED)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_STATUS_CHANGED",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_STATUS_CHANGED)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_TITLE_CHANGED",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_TITLE_CHANGED)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_LOAD_COMPLETE",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_LOAD_COMPLETE)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_PROGRESS",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_PROGRESS)));
+  SWIG_Python_SetConstant(d, "wxEVT_MOZILLA_RIGHT_CLICK",SWIG_From_int(static_cast< int >(wxEVT_MOZILLA_RIGHT_CLICK)));
 }
 
--- wxPython/contrib/mozilla25/wxPython/mozilla.py.wxPython28	2005-05-07 04:41:53.000000000 +1000
+++ wxPython/contrib/mozilla25/wxPython/mozilla.py	2007-05-22 12:25:34.000000000 +1000
@@ -23,11 +23,8 @@ wxMOZ_MAJOR_VERSION = wx.mozilla.MOZ_MAJ
 wxMOZ_MINOR_VERSION = wx.mozilla.MOZ_MINOR_VERSION
 wxMOZ_RELEASE_NUMBER = wx.mozilla.MOZ_RELEASE_NUMBER
 wxMozillaBrowser = wx.mozilla.MozillaBrowser
-wxMozillaBrowserPtr = wx.mozilla.MozillaBrowserPtr
 wxMozillaWindow = wx.mozilla.MozillaWindow
-wxMozillaWindowPtr = wx.mozilla.MozillaWindowPtr
 wxMozillaSettings = wx.mozilla.MozillaSettings
-wxMozillaSettingsPtr = wx.mozilla.MozillaSettingsPtr
 wxMozillaSettings_SetProfilePath = wx.mozilla.MozillaSettings_SetProfilePath
 wxMozillaSettings_GetProfilePath = wx.mozilla.MozillaSettings_GetProfilePath
 wxMozillaSettings_SetMozillaPath = wx.mozilla.MozillaSettings_SetMozillaPath
@@ -60,23 +57,14 @@ wxMOZILLA_CONTEXT_TEXT = wx.mozilla.MOZI
 wxMOZILLA_CONTEXT_BACKGROUND_IMAGE = wx.mozilla.MOZILLA_CONTEXT_BACKGROUND_IMAGE
 wxMOZILLA_CONTEXT_IMAGE = wx.mozilla.MOZILLA_CONTEXT_IMAGE
 wxMozillaBeforeLoadEvent = wx.mozilla.MozillaBeforeLoadEvent
-wxMozillaBeforeLoadEventPtr = wx.mozilla.MozillaBeforeLoadEventPtr
 wxMozillaLinkChangedEvent = wx.mozilla.MozillaLinkChangedEvent
-wxMozillaLinkChangedEventPtr = wx.mozilla.MozillaLinkChangedEventPtr
 wxMozillaStateChangedEvent = wx.mozilla.MozillaStateChangedEvent
-wxMozillaStateChangedEventPtr = wx.mozilla.MozillaStateChangedEventPtr
 wxMozillaSecurityChangedEvent = wx.mozilla.MozillaSecurityChangedEvent
-wxMozillaSecurityChangedEventPtr = wx.mozilla.MozillaSecurityChangedEventPtr
 wxMozillaLoadCompleteEvent = wx.mozilla.MozillaLoadCompleteEvent
-wxMozillaLoadCompleteEventPtr = wx.mozilla.MozillaLoadCompleteEventPtr
 wxMozillaStatusChangedEvent = wx.mozilla.MozillaStatusChangedEvent
-wxMozillaStatusChangedEventPtr = wx.mozilla.MozillaStatusChangedEventPtr
 wxMozillaTitleChangedEvent = wx.mozilla.MozillaTitleChangedEvent
-wxMozillaTitleChangedEventPtr = wx.mozilla.MozillaTitleChangedEventPtr
 wxMozillaProgressEvent = wx.mozilla.MozillaProgressEvent
-wxMozillaProgressEventPtr = wx.mozilla.MozillaProgressEventPtr
 wxMozillaRightClickEvent = wx.mozilla.MozillaRightClickEvent
-wxMozillaRightClickEventPtr = wx.mozilla.MozillaRightClickEventPtr
 wxEVT_MOZILLA_BEFORE_LOAD = wx.mozilla.wxEVT_MOZILLA_BEFORE_LOAD
 wxEVT_MOZILLA_URL_CHANGED = wx.mozilla.wxEVT_MOZILLA_URL_CHANGED
 wxEVT_MOZILLA_STATE_CHANGED = wx.mozilla.wxEVT_MOZILLA_STATE_CHANGED
