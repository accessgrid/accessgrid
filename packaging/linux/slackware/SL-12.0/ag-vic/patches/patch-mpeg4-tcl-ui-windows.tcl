--- mpeg4/tcl/ui-windows.tcl.orig	2007-06-06 09:48:39.000000000 +1000
+++ mpeg4/tcl/ui-windows.tcl	2007-06-06 14:06:53.941673985 +1000
@@ -189,13 +189,13 @@
 	}
 	set w .vw$uid
 	toplevel $w -class Vic \
-		-visual "[winfo visual .top] [winfo depth .top]" -padx 0 -pady 0
+		-visual "[winfo visual .top] [winfo depth .top]"
 	catch "wm resizable $w false false"
 	#
 	# make windows become x-y resizeable
 	#
 	#catch "wm resizable $w true false"
-	frame $w.frame -padx 0 -pady 0 
+	frame $w.frame
 
 
 	global size$w userwin_x userwin_y userwin_size
