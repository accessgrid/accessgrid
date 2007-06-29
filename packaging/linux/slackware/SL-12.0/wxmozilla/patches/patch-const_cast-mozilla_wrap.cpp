--- wxPython/contrib/mozilla25/gtk/mozilla_wrap.cpp.orig	2007-04-02 15:36:55.000000000 +1000
+++ wxPython/contrib/mozilla25/gtk/mozilla_wrap.cpp	2007-06-20 12:39:28.328805115 +1000
@@ -1228,7 +1228,7 @@
     obj = pyobj;
     if (PyCFunction_Check(obj)) {
       /* here we get the method pointer for callbacks */
-      char *doc = (((PyCFunctionObject *)obj) -> m_ml -> ml_doc);
+      char *doc = const_cast<char*>(((PyCFunctionObject *)obj) -> m_ml -> ml_doc);
       c = doc ? strstr(doc, "swig_ptr: ") : 0;
       if (c) {
 	c = ty ? SWIG_UnpackVoidPtr(c + 10, &vptr, ty->name) : 0;
@@ -8120,7 +8120,7 @@
     swig_type_info **types_initial) {
         size_t i;
         for (i = 0; methods[i].ml_name; ++i) {
-            char *c = methods[i].ml_doc;
+            char *c = const_cast<char*>(methods[i].ml_doc);
             if (c && (c = strstr(c, "swig_ptr: "))) {
                 int j;
                 swig_const_info *ci = 0;
