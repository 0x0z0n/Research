# 
# slave makefile
# --------------
#
# Copyright (C) 2018 by Adrian Brzezinski <adrian.brzezinski at adrb.pl>
#

CC=gcc
OBJS = $(shell find . -iname "*.c" -type f -print | sed -e "/xdr\// d; s/.//;s/\///")

RPCGEN = rpcgen
RPCGEN_FLAGS = -C
RPCGEN_MOUNT = xdr/mount_clnt.c xdr/mount.h xdr/mount_svc.c xdr/mount_xdr.c
RPCGEN_NFS3 = xdr/nfsv3_clnt.c xdr/nfsv3.h xdr/nfsv3_svc.c xdr/nfsv3_xdr.c
RPCGEN_OBJS = xdr/mount_clnt.c xdr/mount_xdr.c xdr/nfsv3_clnt.c xdr/nfsv3_xdr.c

all: $(RPCGEN_OBJS) $(OBJS)
	$(CC) ${CFLAGS} ${RPCGEN_OBJS} ${OBJS} -o ${OUT_NAME}
	mv ${OUT_NAME} ../

$(RPCGEN_MOUNT):
	$(RPCGEN) $(RPCGEN_FLAGS) xdr/mount.x

$(RPCGEN_NFS3):
	$(RPCGEN) $(RPCGEN_FLAGS) xdr/nfsv3.x

clean:
	-rm ${RPCGEN_MOUNT} ${RPCGEN_NFS3} *.o

