# 
# master makefile
# ---------------
#
# Copyright (C) 2018 by Adrian Brzezinski <adrian.brzezinski at adrb.pl>
#  

OUT_NAME=nfsclt

TOPDIR = $(shell if [ "$$pwd" != "" ]; then echo $$PWD; else pwd; fi)

INCLUDE = -I${TOPDIR}/src
SOURCE = ${TOPDIR}/src

BASE_CFLAGS = ${INCLUDE} -Wall -Wno-unused-variable -lreadline -lhistory -lcap -lm
RELEASE_CFLAGS=${BASE_CFLAGS} -O2
DEBUG_CFLAGS=${BASE_CFLAGS} -g -DDEBUG

all: release

release:
	$(MAKE) CFLAGS="${RELEASE_CFLAGS}" OUT_NAME="${OUT_NAME}" -C ${SOURCE}

debug:
	$(MAKE) CFLAGS="${DEBUG_CFLAGS}" OUT_NAME="${OUT_NAME}" -C ${SOURCE}

clean:
	$(MAKE) clean -C ${SOURCE}
	-rm ${OUT_NAME}

