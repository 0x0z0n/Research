/*
 * 
 * Adrian Brzezinski (2018) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#ifndef __NFSCLT_H__
#define __NFSCLT_H__

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <libgen.h>
#include <sys/stat.h>

#include <rpc/rpc.h>
#include <rpc/pmap_clnt.h>

#include "netsocket.h"
#include "utils.h"
#include "xdr/mount.h"
#include "xdr/nfsv3.h"

// Limit total NFS lookups when resolving path name.
// Just in case if we hit symlinks loop
#define MAX_PATH_DEPTH 2000

typedef struct {

  int socket;
  CLIENT *client;

} t_nfsconnection;

typedef union {

  mountres3 *nfs3;    // pointer to static value

} tp_nfsmountres;

typedef union {

  nfs_fh3 nfs3;

} t_nfsfh;

typedef union {

  READDIR3res *nfs3;

} tp_nfsdir;

typedef struct {

  unsigned long version;
  int authtype;

  int uid;
  int gid;
  int mode;

  char *hostname;
  t_nfsconnection mount;    // connection to mount daemon
  t_nfsconnection nfs;      // connection to nfs daemon

  char *mountpath;
  tp_nfsmountres mountres;

  t_nfsfh currentdir;

} t_nfsclt;

extern t_nfsclt nfsclt;

void nfshandleprint( t_nfsfh *nfsfh, unsigned long version );
int nfshandleset_str( t_nfsfh *nfsfh, unsigned long version, char *handle );

int nfsconnect( t_nfsclt *nfsclt, unsigned long prognum );
void nfsdisconnect( t_nfsconnection *nfsconn );

exports nfsexports( t_nfsclt *nfsclt );

int nfsmount( t_nfsclt *nfsclt, char *path );
void nfsumount( t_nfsclt *nfsclt );

int nfsfilecreate( t_nfsclt *nfsclt, char *path, struct stat *fstat );
int nfsfilestat( t_nfsclt *nfsclt, char *path, struct stat *fstat );
int nfsfileattr( t_nfsclt *nfsclt, char *filename, struct stat *fstat);
int nfsfilerm( t_nfsclt *nfsclt, char *path );

int nfsfilepread( t_nfsclt *nfsclt, char *path, long offset, char *data, int datalen );
int nfsfilepwrite( t_nfsclt *nfsclt, char *file, long offset, char *data, int datalen );

// nfsdir - structure with directory files, prepared by nfsdirread()
// Path is only needed when it needs to lookup for file attributes (printattrs=1)
// and we do'nt list current catalog
int nfsdirprint( t_nfsclt *nfsclt, tp_nfsdir *nfsdir, int printattrs, char *path );
int nfsdirread( t_nfsclt *nfsclt, tp_nfsdir *nfsdir, char *path );
int nfsdirmk( t_nfsclt *nfsclt, char *path, struct stat *fstat );
int nfsdirrm( t_nfsclt *nfsclt, char *path);
int nfscd( t_nfsclt *nfsclt, char *path );

int nfsmove( t_nfsclt *nfsclt, char *src, char *dst);
int nfslink( t_nfsclt *nfsclt, char *target, char *linkname);
int nfssymlink( t_nfsclt *nfsclt, char *target, char *linkname, struct stat *fstat);
int nfsmknod( t_nfsclt *nfsclt, char *path, struct stat *fstat, dev_t dev);

int nfsprintstat(t_nfsclt *nfsclt);

#endif // __NFSCLT_H__
