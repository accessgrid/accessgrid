%module common
%{
#undef socklen_t
#ifdef WIN32
#include "../../src/config_win32.h"
#else
#include "../../src/config_unix.h"
#endif
#include "../../src/rtp.h"
#include "../../src/rijndael-api-fst.h"
#include "../../src/net_udp.h"
#include "../../src/mbus.h"
#include "Rtp.h"
#include "Mbus.h"
%}

%include "typemaps.i"
%include "carrays.i"
%include "cstring.i"
%include "cpointer.i"

%typemap(python, in) timeval * (timeval tv_temp) {
    tv_temp.tv_sec = PyLong_AsLong(PyTuple_GET_ITEM($input, 0));
    tv_temp.tv_usec = PyLong_AsLong(PyTuple_GET_ITEM($input, 1));
    $1 = &tv_temp;
}

%typemap(python, out) timeval * {
	if(!($result = PyTuple_New(2))) {
		PyErr_SetString(PyExc_RuntimeError, 
	                        "timevalToTuple:: PyTuple_New()");
		return NULL;
	}
	PyTuple_SET_ITEM($result, 0, Py_BuildValue("l", $1->tv_sec));
	PyTuple_SET_ITEM($result, 1, Py_BuildValue("l", $1->tv_usec));
}

%typemap(python, in) uint32_t {
   $1 = (uint32_t)PyLong_AsLong($input);
}

%typemap(python, out) uint32_t {
   $result = PyLong_FromLong($1);
}

%typemap(python, in) uint16_t {
   $1 = (uint16_t)PyInt_AsLong($input);
}

%typemap(python, out) uint16_t {
   $result = PyInt_FromLong($1);
}

%typemap(python, in) uint8_t {
   $1 = (uint8_t)PyInt_AsLong($input);
}

%typemap(python, out) uint8_t {
   $result = PyInt_FromLong($1);
}


#ifdef SWIGWIN
%include "../../src/config_win32.h"
#else
%include "../../src/config_unix.h"
#endif

%include "../../src/rtp.h"
%include "../../src/mbus.h"

%include "Rtp.h"
%include "Mbus.h"

