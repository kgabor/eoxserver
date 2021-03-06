#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------
#
# NOTE: To compile the version for extended GDAL beside the baseline run: 
#
# $ make baseline extended clean 
#

CC= gcc
LD= gcc
LD_SHARED = $(LD) -shared 

INCS=$(shell gdal-config --cflags)
LIBS=$(shell gdal-config --libs)

#CFLAGS=-g -DDEBUG=1 -Wall -fPIC $(INCS)
#CFLAGS=-O2 -g -DDEBUG=1 -Wall -fPIC $(INCS)
CFLAGS=-O2 -Wall -fPIC $(INCS)
LFLAGS=$(LIBS)

OBJ1=reftools.o
OBJ2=reftools_ext.o

TARGET1=_reftools.so
TARGET2=_reftools_ext.so

# --------------------------------------------

all: baseline clean

baseline: $(TARGET1)
extended: $(TARGET2)   

%.o: %.c
	$(CC) -c $< -o $@ $(CFLAGS) 

$(TARGET1): $(OBJ1)
	$(LD_SHARED) -o $(TARGET1) $(OBJ1) $(LFLAGS) 

$(TARGET2): $(OBJ2)
	$(LD_SHARED) -o $(TARGET2) $(OBJ2) $(LFLAGS) 

reftools_ext.o:
	$(CC) -c reftools.c -o reftools_ext.o -DUSE_GDAL_EOX_EXTENSIONS=1 $(CFLAGS)

clean:
	-rm -fv *.o

