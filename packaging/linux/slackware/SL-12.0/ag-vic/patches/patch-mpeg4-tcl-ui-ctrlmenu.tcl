--- mpeg4/tcl/ui-ctrlmenu.tcl.orig	2007-06-06 09:48:39.000000000 +1000
+++ mpeg4/tcl/ui-ctrlmenu.tcl	2007-06-06 13:53:55.659211618 +1000
@@ -176,12 +176,12 @@
 			return
 		}
 	}
-	if { [string equal -nocase -length 5 $d "V4L2:"] } {
+	if { [string toupper [string range $d 0 4]] == "V4L2:" } {
         	set d [string range $d 5 end]
         	set k [string length $d]
         	incr k -1
 		foreach v $inputDeviceList {
-	   		if { [string equal -length 5 [$v nickname] "V4L2-"] && \
+	   		if { [string range [$v nickname] 0 4] == "V4L2-" && \
 				[string range [$v nickname] end-$k end] == "$d" && \
 				[$v attributes] != "disabled" } {
 				set videoDevice $v
@@ -190,12 +190,12 @@
 			}
 		}
 	}
-	if { [string equal -nocase -length 4 $d "V4L:"] } {
+	if { [string toupper [string range $d 0 3]] == "V4L:" } {
         	set d [string range $d 4 end]
         	set k [string length $d]
         	incr k -1
 		foreach v $inputDeviceList {
-	   		if { [string equal -length 4 [$v nickname] "V4L-"] && \
+	   		if { [string range [$v nickname] 0 3] == "V4L-" && \
 				[string range [$v nickname] end-$k end] == "$d" && \
 				[$v attributes] != "disabled" } {
 				set videoDevice $v
