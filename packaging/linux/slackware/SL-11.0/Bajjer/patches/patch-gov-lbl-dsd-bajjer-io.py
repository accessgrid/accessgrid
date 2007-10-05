--- gov/lbl/dsd/bajjer/io.py.orig	2007-01-18 07:23:14.000000000 +1000
+++ gov/lbl/dsd/bajjer/io.py	2007-10-06 00:30:45.442402000 +1000
@@ -50,10 +50,12 @@
         messages.  
         """ 
         while True: 
+            gotData = 0
             for conn, cbq in self._cb_queue_dict.items(): 
                 for stanza_type, func_tuple in cbq.cb_dict.items(): 
                     stanza_obj = conn.read(expected=stanza_type, blocking=False)
                     if stanza_obj is not None:
+                        gotData = 1
                         func = func_tuple[0] 
                         arg_tuple  = func_tuple[1]
                         if arg_tuple is None:
@@ -64,7 +66,8 @@
                             for obj in arg_tuple:
                                 arg_list.append(obj)
                             func(*arg_list) 
-            time.sleep(0.1)
+            if not gotData:
+                time.sleep(0.1)
 
 class CallbackQueue:
     """
