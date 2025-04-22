#!/usr/bin/make
# Needs GTK and GLX

# apt update
# apt install -y gcc binutils pkgconf libgtk-3-dev
# Change gtk+-3.0 to the name of the .pc used in your system
# gtk+-3.0.pc is used for GTK 3 on Debian 11 and similar systems
GTK_FLAGS=`pkg-config --cflags --libs gtk+-3.0`
GLX_LIB=-lGL

all: libinterposer.so

libinterposer.so: interposer.c
	gcc -D_GNU_SOURCE -fpic -shared -o $@ $(GTK_FLAGS) $< -ldl $(GLX_LIB)

clean:
	@-rm libinterposer.so
