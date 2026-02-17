/*
 * 
 * Adrian Brzezinski (2018) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#include "nfsclt.h"

const char *nfs3_error(enum nfsstat3 stat) {

  switch (stat) {
  case NFS3_OK:
    return "No error";
  case NFS3ERR_PERM:
    return "Not owner. Caller is either not a privileged user (root) or not the owner";
  case NFS3ERR_NOENT:
    return "No such file or directory";
  case NFS3ERR_IO:
    return "I/O error";
  case NFS3ERR_NXIO:
    return "No such device or address";
  case NFS3ERR_ACCES:
    return "Permission denied";
  case NFS3ERR_EXIST:
    return "File exists";
  case NFS3ERR_XDEV:
    return "Attempt to do a cross-device hard link";
  case NFS3ERR_NODEV:
    return "No such device";
  case NFS3ERR_NOTDIR:
    return "Not a directory";
  case NFS3ERR_ISDIR:
    return "Is a directory";
  case NFS3ERR_INVAL:
    return "Invalid or unsupported argument for an operation";
  case NFS3ERR_FBIG:
    return "File too large";
  case NFS3ERR_NOSPC:
    return "No space left on device";
  case NFS3ERR_ROFS:
    return "Read-only file system";
  case NFS3ERR_MLINK:
    return "Too many hard links";
  case NFS3ERR_NAMETOOLONG:
    return "File name too long";
  case NFS3ERR_NOTEMPTY:
    return "Directory not empty";
  case NFS3ERR_DQUOT:
    return "Disc quota exceeded";
  case NFS3ERR_STALE:
    return "Stale NFS file handle";
  case NFS3ERR_REMOTE:
    return "Too many levels of remote in path";
  case NFS3ERR_BADHANDLE:
    return "Illegal NFS file handle";
  case NFS3ERR_NOT_SYNC:
    return "Update synchronization mismatch";
  case NFS3ERR_BAD_COOKIE:
    return "READDIR or READDIRPLUS cookie is stale";
  case NFS3ERR_NOTSUPP:
    return "Operation is not supported";
  case NFS3ERR_TOOSMALL:
    return "Buffer or request is too small";
  case NFS3ERR_SERVERFAULT:
    return "Other server error";
  case NFS3ERR_BADTYPE:
    return "Type not supported by server";
  case NFS3ERR_JUKEBOX:
    return "Retrieval pending";
  default:
    return "UKNOWN NFS ERROR";
  }

return NULL;
}

void nfs_fh3free( nfs_fh3 *fh ) {

  if ( fh->data.data_val )
    free(fh->data.data_val);

  fh->data.data_val = NULL;
  fh->data.data_len = 0;
}

int nfs_fh3alloc( nfs_fh3 *fh, unsigned int data_len ) {

  nfs_fh3free(fh);

  fh->data.data_len = data_len;
  fh->data.data_val = calloc( data_len, sizeof(char));

  if ( fh->data.data_val )
    return 0;

  fh->data.data_len = 0;

return -1;
}

void *fhandle3_to_nfs_fh3(nfs_fh3 *dest, const fhandle3 *src) {

  nfs_fh3alloc(dest, src->fhandle3_len);

return memcpy(dest->data.data_val, src->fhandle3_val, src->fhandle3_len);
}

void *nfs_fh3copy( nfs_fh3 *dest, nfs_fh3 *src ) {

  nfs_fh3alloc(dest, src->data.data_len);

return memcpy(dest->data.data_val, src->data.data_val, src->data.data_len);
}

void stat_to_sattr3( sattr3 *sattr, struct stat *fstat) {

  memset(sattr, 0, sizeof(sattr3));

  if ( fstat->st_mode ) {
    sattr->mode = (set_mode3) {
      .set_it = TRUE,
      .set_mode3_u.mode = (fstat->st_mode & 0777)
    };
  } else {
    sattr->mode.set_it = FALSE;
  }

  // NFSv2 style overload for mknod with nfsproc3_create_3
  // Do we really need this?
  if ( fstat->st_dev ) {
    sattr->size = (set_size3) {
      .set_it = TRUE,
      .set_size3_u.size = fstat->st_dev
    };
  } else {
    sattr->size.set_it = FALSE;
  }

  sattr->uid = (set_uid3) {
    .set_it = TRUE,
    .set_uid3_u.uid = fstat->st_uid
  };
  sattr->gid = (set_gid3) {
    .set_it = TRUE,
    .set_gid3_u.gid = fstat->st_gid
  };

  if ( fstat->st_atim.tv_sec ) {
    sattr->atime = (set_atime) {
      .set_it = TRUE,
      .set_atime_u.atime.seconds = fstat->st_atim.tv_sec,
      .set_atime_u.atime.nseconds = fstat->st_atim.tv_nsec
    };
  } else {
    sattr->atime.set_it = SET_TO_SERVER_TIME;
  }

  if ( fstat->st_mtim.tv_sec ) {
    sattr->mtime = (set_mtime) {
      .set_it = TRUE,
      .set_mtime_u.mtime.seconds = fstat->st_mtim.tv_sec,
      .set_mtime_u.mtime.nseconds = fstat->st_mtim.tv_nsec
    };
  } else {
    sattr->mtime.set_it = SET_TO_SERVER_TIME;
  }

}

int nfsauthenticator(t_nfsclt *nfsclt, t_nfsconnection *nfsconn) {
  char machname[MAX_MACHINE_NAME + 1];
  gid_t gids[1];

  memset(&machname, 0, sizeof(machname));
  gids[0] = nfsclt->gid;

  switch (nfsclt->authtype) {
  case AUTH_UNIX:

    if (gethostname(machname, MAX_MACHINE_NAME) == -1) {
      perror("gethostname()");
      return -1;
    }

    nfsconn->client->cl_auth = authunix_create(
      machname, nfsclt->uid, nfsclt->gid, 1, gids);

  break;

  default:
    return -1;
  }

return 0;
}

void nfsdisconnect( t_nfsconnection *nfsconn ) {

  if ( nfsconn->client ) {
    auth_destroy(nfsconn->client->cl_auth);
    clnt_destroy(nfsconn->client);

    nfsconn->client = NULL;
  }

  if ( nfsconn->socket > 0 ) {
    sockclose(nfsconn->socket);
  }
  nfsconn->socket = -1;

}

int nfsconnect( t_nfsclt *nfsclt, unsigned long prognum ) {

  int srcport, dstport;
  struct sockaddr_in srvaddr;
  struct timeval timeout = { 60, 0 };
  unsigned long versnum;

  t_nfsconnection *nfsconn;

  switch ( nfsclt->version ) {
    case 30:  // NFSv3

      switch ( prognum ) {
        case MOUNT_PROGRAM:
          versnum = MOUNT_V3;
          nfsconn = &nfsclt->mount;
        break;
        case NFS_PROGRAM:
          versnum = NFS_V3;
          nfsconn = &nfsclt->nfs;
        break;
        default:
          fprintf(stderr,"Not supported program\n");
          return -1;
      }

    break;

    default:
      fprintf(stderr,"Not supported NFS version\n");
      return -1;
  }

  if ( sockisconnected(nfsconn->socket) )
    return 0;

  // clean up in case that connection was interrupted
  nfsdisconnect(nfsconn);

  printf("Establishing new TCP connection.");
  fflush(stdout);

  if ( sockaddrsetup(&srvaddr, sizeof(srvaddr), nfsclt->hostname, 0) == -1 )
    return -1;

  dstport = pmap_getport(&srvaddr, prognum, versnum, IPPROTO_TCP);
  if ( dstport == 0 ) {
    perror("\npmap_getport()");
    return -1;
  }

  printf("."); fflush(stdout);

  // Check whatever we actually have permission to open privileged port
  if ( cap_flag(0, CAP_NET_BIND_SERVICE) == CAP_SET ) {

    // search for available priviledged port
    for ( srcport = IPPORT_RESERVED - 1 ; srcport > 0 ; srcport-- ) {
      nfsconn->socket = sockconnectsrc(nfsclt->hostname, dstport, "0.0.0.0", srcport);

      if ( nfsconn->socket != -1 ) break;
    }
  }

  if ( nfsconn->socket <= 0 ) {
    nfsconn->socket = sockconnect(nfsclt->hostname, dstport); 
  }

  if ( nfsconn->socket <= 0 ) {
    fprintf(stderr,"\nconnection failed.");
    return -1;
  }

  printf("."); fflush(stdout);

  // Creating RPC client
  nfsconn->client = clnttcp_create(&srvaddr, prognum, versnum,
      &nfsconn->socket, 0, 0);

  if ( nfsconn->client == NULL ) {
    clnt_pcreateerror("\nclnttcp_create()");
    sockclose(nfsconn->socket);
    nfsconn->socket = -1;
    return -1;
  }

  clnt_control(nfsconn->client, CLSET_TIMEOUT, (char *)&timeout);
  clnt_control(nfsconn->client, CLSET_FD_CLOSE, (char *)NULL);

  if ( nfsauthenticator(nfsclt, nfsconn) == -1 )
    return -1;

  printf(" connected (%s:%d --> %s:%d)\n",
    sockname(nfsconn->socket), sockport(nfsconn->socket),
    sockpeername(nfsconn->socket), sockpeerport(nfsconn->socket));
  
return 0;
}

exports nfsexports( t_nfsclt *nfsclt ) {

  if ( nfsclt->mount.client == NULL )
    return NULL;

  switch ( nfsclt->version ) {
    case 30:
      return *mount3_export_3(NULL, nfsclt->mount.client);
    break;
  }

return NULL;
}

void nfshandleprint( t_nfsfh *nfsfh, unsigned long version ) {
  int i;

  switch ( version ) {
    case 30:

      if ( nfsfh->nfs3.data.data_len == 0 ) {
        printf("Handle not set\n");
      }

      printf("nfs3 fh: (%d) ", nfsfh->nfs3.data.data_len);

      for ( i = 0; i < nfsfh->nfs3.data.data_len ; i++ )
        printf("%02x", nfsfh->nfs3.data.data_val[i] & 0xff);
      printf("\n");

    break;
  }
}

int nfshandleset_str( t_nfsfh *nfsfh, unsigned long version, char *handle ) {

  t_nfsfh tmpfh;
  int i, hlen;
  unsigned int val;

  memset(&tmpfh, 0, sizeof(tmpfh));

  switch ( version ) {
    case 30:

      hlen = strlen(handle);

      if ( hlen & 1 ) {
        fprintf(stderr,"Wrong format\n");
        return -1;
      }

      nfs_fh3alloc( &tmpfh.nfs3, hlen >> 1 );

      for ( i = 0; i < hlen ; i += 2 ) {
        sscanf(handle+i, "%02x", &val);
        tmpfh.nfs3.data.data_val[i >> 1] = val & 0xff;
      }

      //nfshandleprint(&tmpfh, version);

      nfs_fh3copy(&nfsfh->nfs3, &tmpfh.nfs3);
      nfs_fh3free(&tmpfh.nfs3);
    break;
  }

return 0;
}

void nfsumount( t_nfsclt *nfsclt ) {

  switch ( nfsclt->version ) {
  case 30:

    if ( nfsclt->mount.client == NULL ) {

      fprintf(stderr,"\nNothing mounted\n");
      return;
    }

    if ( nfsclt->mountpath ) {
      printf("\nUmounting '%s'... ", nfsclt->mountpath);
      fflush(stdout);

      mount3_umnt_3(&nfsclt->mountpath, nfsclt->mount.client);

    } else {
      printf("\nNothing mounted, disconnecting... ");
      fflush(stdout);
    }

    nfsdisconnect( &nfsclt->mount );
    nfsdisconnect( &nfsclt->nfs );

    if ( nfsclt->mountpath ) {
      free( nfsclt->mountpath );
      nfsclt->mountpath = NULL;
    }

    // static resource don't need free()
    if ( nfsclt->mountres.nfs3 )
      nfsclt->mountres.nfs3 = NULL;

    printf("done\n");

  break;
  }
}

// In order to mount, we need to get file handle for given path.
// Thre are two ways of getting FH:
//  - through portmapper
//  - directly from mount/nfs daemon
// As of NFSv4 portmapper is being abandoned, so we
// only try directly with daemon (even for NFSv3)
int nfsmount( t_nfsclt *nfsclt, char *path ) {

  switch ( nfsclt->version ) {
    case 30:

      nfsclt->mountres.nfs3 = mount3_mnt_3(&path, nfsclt->mount.client);
      if ( nfsclt->mountres.nfs3 == NULL) {
        clnt_perror(nfsclt->mount.client, "mount3_mnt_3()");
        return -1;
      }

      if (nfsclt->mountres.nfs3->fhs_status != MNT3_OK) {
        fprintf(stderr,"Mount failed: (%d) %s\n", nfsclt->mountres.nfs3->fhs_status,
          nfs3_error(nfsclt->mountres.nfs3->fhs_status));
        return -1;
      }

      if ( nfsclt->mountpath ) free(nfsclt->mountpath);
      nfsclt->mountpath = strdup(path);

      fhandle3_to_nfs_fh3(&nfsclt->currentdir.nfs3,
          &nfsclt->mountres.nfs3->mountres3_u.mountinfo.fhandle);

      nfshandleprint(&nfsclt->currentdir, nfsclt->version);

    break;
  }

return -1;
}

LOOKUP3res* nfs3filelookup( CLIENT *client, nfs_fh3 *directoryfh, char *filename) {

  LOOKUP3args args;
  LOOKUP3res *res;

  memset(&args, 0, sizeof(args));

  nfs_fh3copy(&args.what.dir, directoryfh);
  args.what.name = filename;

  res = nfsproc3_lookup_3(&args, client);
  nfs_fh3free( &args.what.dir );

  if ( res == NULL ) {
    clnt_perror(client, "nfsproc3_lookup_3()");
    return NULL;
  }

  if ( res->status != NFS3_OK ) {
    fprintf(stderr, "Failed to lookup: %s - (%d) %s\n", filename,
        res->status, nfs3_error(res->status));
    return NULL;
  }

return res;
}

// lookup for link target
READLINK3res* nfs3linklookup( CLIENT *client, nfs_fh3 *filefh) {
 
  READLINK3args largs;
  READLINK3res *lres;

  memset(&largs, 0, sizeof(largs));

  nfs_fh3copy(&largs.symlink, filefh);

  lres = nfsproc3_readlink_3(&largs, client);
  nfs_fh3free( &largs.symlink );

  if ( lres == NULL ) {
    clnt_perror(client, "nfsproc3_readlink_3()");
    return NULL;
  }

  if (lres->status != NFS3_OK) {
    fprintf(stderr, "Link lookup failed: (%d) %s\n",
        lres->status, nfs3_error(lres->status));
    return NULL;
  }

return lres;
}

// lookup file with path
LOOKUP3res* nfs3pathlookup( t_nfsclt *nfsclt, char *path, int follow ) {

  LOOKUP3res *res = NULL;
  READLINK3res* lres;
  nfs_fh3 fh;
  char *dirname, *p, *path_malloc;
  int d = 0, maxdepth = MAX_PATH_DEPTH;

  memset(&fh, 0, sizeof(fh));

  if ( path == NULL ) return NULL;

  if ( nfsclt->currentdir.nfs3.data.data_val == NULL ) {
    fprintf(stderr, "Please set file handle\n");
    return NULL;
  }

  // start path resolving relatively to current directory
  nfs_fh3copy(&fh, &nfsclt->currentdir.nfs3);

  path_malloc = strdup(path); // holds pointer to allocated path buffer

  for ( p = path_malloc; *p != '\0' && d < maxdepth ; ) {

    // start from mount root?
    if ( *p == '/' && nfsclt->mountres.nfs3 ) {

      while ( *p == '/' ) p++;

      fhandle3_to_nfs_fh3(&fh, &nfsclt->mountres.nfs3->mountres3_u.mountinfo.fhandle);

      // path is equal to '/', set dirname to '.' so we can
      // lookup root dir
      if ( *p == '\0' ) {
        *(--p) = '.';
      }
    }

    // search for end of dirname
    for ( dirname = p; *p && *p != '/' ; p++ ) ;

    // mark dirname end with zero, in case that it's
    // not final object
    while ( *p == '/' ) *p++ = '\0';

    res = nfs3filelookup( nfsclt->nfs.client, &fh, dirname);
    if ( res == NULL ) break;

    d++;  // increase depth counter

    if ( res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
          == NF3LNK ) {

      // don't follow links
      if ( !follow ) {
        nfs_fh3copy(&fh, &res->LOOKUP3res_u.resok.object);
        break;
      }

      lres = nfs3linklookup( nfsclt->nfs.client, &res->LOOKUP3res_u.resok.object );
      if ( lres == NULL ) {
        res = NULL;
        break;
      }

      // insert link into our path
      char *tmp = calloc(
          strlen(p) + strlen(lres->READLINK3res_u.resok.data),
          sizeof(char));

      strcat(tmp, lres->READLINK3res_u.resok.data);
      if ( *p ) {
        strcat(tmp, "/");
        strcat(tmp, p);
      }

      free(path_malloc);
      path_malloc = tmp;
      p = tmp;
      continue;   // start from scratch
    }

    // we accept files only as a final object
    if ( res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
        != NF3DIR && *p ) {

      fprintf(stderr, "%s: is not a directory\n", dirname);

      res = NULL;
      break;
    }

    nfs_fh3copy(&fh, &res->LOOKUP3res_u.resok.object);
  }

  nfs_fh3free(&fh);
  free(path_malloc);

return res;
}

// Returns 1 if there are more entries to read
int nfs3dirread( t_nfsclt *nfsclt, tp_nfsdir *nfsdir, char *path ) {

  READDIR3args args;
  READDIR3res *res;
  entry3 *ep = NULL;

  memset(&args, 0, sizeof(args));

  // get directory FH
  if ( path == NULL ) {

    // current directory
    nfs_fh3copy(&args.dir, &nfsclt->currentdir.nfs3);
  } else {

    // resolve path
    LOOKUP3res *dres = nfs3pathlookup( nfsclt, path, 1 );
    if ( dres == NULL ) return -1;

    if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
        != NF3DIR ) {

      fprintf(stderr, "%s: is not a directory\n", path);
      return -1;
    }

    nfs_fh3copy(&args.dir, &dres->LOOKUP3res_u.resok.object);
  }

  // Find last entry and copy it's cookie.
  // Cookies identify point in directory, where we
  // finished reading entries in previous call.
  if ( nfsdir->nfs3 && nfsdir->nfs3->status == NFS3_OK ) {

    res = nfsdir->nfs3;

    for ( ep = res->READDIR3res_u.resok.reply.entries ;
          ep && ep->nextentry != NULL; ep = ep->nextentry ) ;
  }

  if ( ep ) {
    memcpy( &args.cookie, &ep->cookie, sizeof(args.cookie));
  } else {

    // We hadn't read that directory before
    memset(&args.cookie, 0, sizeof(args.cookie));
    args.count = 8192;
  }

  // read directory entries
  res = nfsproc3_readdir_3(&args, nfsclt->nfs.client);
  nfs_fh3free( &args.dir );

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_readdir_3()");
    return -1;
  }

  if (res->status == NFS3_OK) {
    nfsdir->nfs3 = res;

    if ( res->READDIR3res_u.resok.reply.eof )
      return 0;

    return 1;
  }

  fprintf(stderr, "Readdir failed: (%d) %s\n", res->status, nfs3_error(res->status));

return -1;
}

int nfsdirread( t_nfsclt *nfsclt, tp_nfsdir *nfsdir, char *path ) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3dirread( nfsclt, nfsdir, path );
    break;
  }

return -1;
}

int nfs3fileprint( t_nfsclt *nfsclt, nfs_fh3 *dirfh, char *name ) {

  LOOKUP3res *res;
  int mode;

  res = nfs3filelookup( nfsclt->nfs.client, dirfh, name);
  if ( res == NULL ) return -1;

  switch (res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type) {
  case NF3SOCK:
    putchar('s');
  break;
  case NF3FIFO:
    putchar('p');
  break;
  case NF3REG:
    putchar('-');
  break;
  case NF3DIR:
    putchar('d');
  break;
  case NF3BLK:
    putchar('b');
  break;
  case NF3CHR:
    putchar('c');
  break;
  case NF3LNK:
    putchar('l');
    break;
  default:
    putchar('?');
    break;
  }

  // now print file mode
  mode = res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.mode;

  // owner
  if (mode & 0400) putchar('r'); else putchar('-');
  if (mode & 0200) putchar('w'); else putchar('-');
  if (mode & 0100) {
    if (mode & 04000) putchar('s'); else putchar('x');
  } else {
    if (mode & 04000) putchar('S'); else putchar('-');
  }

  // group
  if (mode & 040) putchar('r'); else putchar('-');
  if (mode & 020) putchar('w'); else putchar('-');
  if (mode & 010) {
    if (mode & 02000) putchar('s'); else putchar('x');
  } else {
    if (mode & 02000) putchar('S'); else putchar('-');
  }

  // others
  if (mode & 04) putchar('r'); else putchar('-');
  if (mode & 02) putchar('w'); else putchar('-');
  if (mode & 01) {
    if (mode & 01000) putchar('t'); else putchar('x');
  } else {
    if (mode & 01000) putchar('T'); else putchar('-');
  }

  // other details
  printf("%3d%9d%6d%10ld ",
    res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.nlink,
    res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.uid,
    res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.gid,
    res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.size);

  time_t t_mtime = res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.mtime.seconds;
  char *smtime = ctime(&t_mtime);
  if ( smtime ) {
    smtime[ strlen(smtime) -1 ] = '\0';   // clear \n at the end
    printf(" %s", smtime);
  }

  if (res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type != NF3LNK) {
    printf(" %s\n", name);
    return 0;
  }

  // lookup for link target
  READLINK3res* lres = nfs3linklookup( nfsclt->nfs.client,
      &res->LOOKUP3res_u.resok.object );

  if ( lres == NULL ) return -1;

  printf(" %s -> %s\n", name, lres->READLINK3res_u.resok.data);

return 0;
}

int nfs3dirprint( t_nfsclt *nfsclt, READDIR3res *res, int printattrs, char *path ) {

  nfs_fh3 dirfh;
  entry3 *ep = NULL;

  if ( !res || res->status != NFS3_OK )
    return -1;

  if ( printattrs ) {
    memset(&dirfh, 0, sizeof(dirfh));

    if ( path == NULL ) {
      nfs_fh3copy(&dirfh, &nfsclt->currentdir.nfs3);
    } else {

      LOOKUP3res *dres = nfs3pathlookup( nfsclt, path, 1 );
      if ( dres == NULL ) return -1;

      if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
          != NF3DIR ) {

        fprintf(stderr, "%s: is not a directory\n", path);
        return -1;
      }

      nfs_fh3copy(&dirfh, &dres->LOOKUP3res_u.resok.object);
    }
  }

  for ( ep = res->READDIR3res_u.resok.reply.entries ;
        ep != NULL ; ep = ep->nextentry ) {

    if ( printattrs ) {
      nfs3fileprint( nfsclt, &dirfh, ep->name );
    } else {
      printf("%s\n", ep->name);
    }
  }

  if ( printattrs ) nfs_fh3free(&dirfh);

return 0;
}

int nfsdirprint( t_nfsclt *nfsclt, tp_nfsdir *nfsdir, int printattrs, char *path ) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3dirprint( nfsclt, nfsdir->nfs3, printattrs, path );
    break;
  }

return -1;
}

int nfs3cd( t_nfsclt *nfsclt, char *path ) {

  LOOKUP3res* res;

  // cd to root
  if ( path == NULL && nfsclt->mountres.nfs3 ) {

    fhandle3_to_nfs_fh3(&nfsclt->currentdir.nfs3,
      &nfsclt->mountres.nfs3->mountres3_u.mountinfo.fhandle);

    return 0;
  }

  res = nfs3pathlookup( nfsclt, path, 1 );
  if ( res == NULL ) return -1;

  nfs_fh3copy(&nfsclt->currentdir.nfs3, &res->LOOKUP3res_u.resok.object);

return 0;
}

int nfscd( t_nfsclt *nfsclt, char *path ) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3cd( nfsclt, path );
    break;
  }

return -1;
}

// returns number of read bytes
int nfs3filepread(
    t_nfsclt *nfsclt, char *path, long offset,
    char *data, int datalen ) {

  LOOKUP3res *fres;
  READ3args rargs;
  READ3res *rres;
  unsigned long filesize;

  memset( &rargs, 0, sizeof(rargs));

  fres = nfs3pathlookup( nfsclt, path, 1 );
  if ( fres == NULL ) return -1;

  // 'if' instead of 'case' to avoid compiler warnnings
  ftype3 type = fres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type;
  if ( type == NF3DIR ) {
    fprintf(stderr, "%s: is a directory\n", path);
    return -1;
  }
  if ( type == NF3LNK) {
    fprintf(stderr, "%s: is a symbolic link\n", path);
    return -1;
  }

  filesize = fres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.size;

  // nothing to read
  if ( offset >= filesize ) return 0;

  // clamp bytes to read
  if ( offset+datalen > filesize ) {
    rargs.count = filesize - offset;
  } else {
    rargs.count = datalen;
  }

  rargs.offset = offset;
  nfs_fh3copy(&rargs.file, &fres->LOOKUP3res_u.resok.object);

  // read file content
  rres = nfsproc3_read_3(&rargs, nfsclt->nfs.client);
  nfs_fh3free( &rargs.file );

  if ( rres == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_read_3()");
    return -1;
  }

  if (rres->status != NFS3_OK) {
    fprintf(stderr, "Read failed: %s - (%d) %s\n", path,
        rres->status, nfs3_error(rres->status));
    return -1;
  }

  memcpy(data, rres->READ3res_u.resok.data.data_val,
    rres->READ3res_u.resok.data.data_len);

//      fwrite(rres->READ3res_u.resok.data.data_val,
//        rres->READ3res_u.resok.data.data_len, 1, stdout);

return rres->READ3res_u.resok.data.data_len;
}

// returns number of write bytes
int nfs3filepwrite(
    t_nfsclt *nfsclt, char *path, long offset,
    char *data, int datalen ) {

  LOOKUP3res *fres;
  WRITE3args wargs;
  WRITE3res *wres;

  memset( &wargs, 0, sizeof(wargs));

  fres = nfs3pathlookup( nfsclt, path, 0 );
  if ( fres == NULL ) return -1;

  if (fres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type != NF3REG) {
    fprintf(stderr, "%s: is not a regular file\n", path);
    return -1;
  }

  nfs_fh3copy(&wargs.file, &fres->LOOKUP3res_u.resok.object);
  wargs.offset = offset;
  wargs.count = datalen;
  wargs.stable = FILE_SYNC;
  wargs.data.data_len = datalen;
  wargs.data.data_val = data;

  // write data to file
  wres = nfsproc3_write_3(&wargs, nfsclt->nfs.client);
  nfs_fh3free( &wargs.file );

  if ( wres == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_write_3()");
    return -1;
  }

  if (wres->status != NFS3_OK) {
    fprintf(stderr, "Write failed: %s - (%d) %s\n", path,
        wres->status, nfs3_error(wres->status));
    return -1;
  }

return wres->WRITE3res_u.resok.count;
}

int nfsfilepwrite(
    t_nfsclt *nfsclt, char *file, long offset,
    char *data, int datalen ) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3filepwrite( nfsclt, file, offset, data, datalen );
    break;
  }

return -1;
}

int nfsfilepread(
    t_nfsclt *nfsclt, char *file, long offset,
    char *data, int datalen ) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3filepread( nfsclt, file, offset, data, datalen );
    break;
  }

return -1;
}

int nfs3filestat( t_nfsclt *nfsclt, char *path, struct stat *fstat ) {

  LOOKUP3res *res;
  fattr3 *attr;

  res = nfs3pathlookup( nfsclt, path, 0); // don't follow links
  if ( res == NULL ) return -1;

  attr = &res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes;
  memset(fstat, 0, sizeof(stat));

  fstat->st_mode = attr->mode;

  // set file type
  switch (attr->type) {
  case NF3SOCK:
    fstat->st_mode |= S_IFSOCK;
  break;
  case NF3FIFO:
    fstat->st_mode |= S_IFIFO;
  break;
  case NF3REG:
    fstat->st_mode |= S_IFREG;
  break;
  case NF3DIR:
    fstat->st_mode |= S_IFDIR;
  break;
  case NF3BLK:
    fstat->st_mode |= S_IFBLK;
  break;
  case NF3CHR:
    fstat->st_mode |= S_IFCHR;
  break;
  case NF3LNK:
    fstat->st_mode |= S_IFLNK;
  break;
  }

  fstat->st_ino = attr->fileid;
//  fstat->st_rdev = ((attr->rdev.specdata1&0xff)<<8) | (attr->rdev.specdata2&0xff);
  fstat->st_rdev = makedev(attr->rdev.specdata1, attr->rdev.specdata2);
  fstat->st_size = attr->size;
  fstat->st_nlink = attr->nlink;
  fstat->st_uid = attr->uid;
  fstat->st_gid = attr->gid;

  fstat->st_atim.tv_sec = attr->atime.seconds;
  fstat->st_mtim.tv_sec = attr->mtime.seconds;
  fstat->st_ctim.tv_sec = attr->ctime.seconds;

  fstat->st_atim.tv_nsec = attr->atime.nseconds;
  fstat->st_mtim.tv_nsec = attr->mtime.nseconds;
  fstat->st_ctim.tv_nsec = attr->ctime.nseconds;

return 0;
}

int nfsfilestat( t_nfsclt *nfsclt, char *path, struct stat *fstat ) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3filestat( nfsclt, path, fstat );
    break;
  }

return -1;
}

int nfs3filecreate( t_nfsclt *nfsclt, char *dir, char *file, struct stat *fstat ) {

  CREATE3args cargs;
  CREATE3res *cres;

  // lookup directory handle
  LOOKUP3res *res;
  res = nfs3pathlookup( nfsclt, dir, 0);
  if ( res == NULL ) return -1;

  if ( res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  // set new file attributes
  memset(&cargs, 0, sizeof(cargs));
  nfs_fh3copy(&cargs.where.dir, &res->LOOKUP3res_u.resok.object);
  cargs.where.name = file;

  // one of UNCHECKED GUARDED EXCLUSIVE
  // UNCHECKED - without checking for the existence of a duplicate file
  cargs.how.mode = GUARDED; 

  stat_to_sattr3(&cargs.how.createhow3_u.obj_attributes, fstat);

  cres = nfsproc3_create_3(&cargs, nfsclt->nfs.client);
  nfs_fh3free(&cargs.where.dir); 

  if ( cres == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_create_3()");
    return -1;
  }

  if (cres->status != NFS3_OK) {
    fprintf(stderr, "Creating file: %s - (%d) %s\n", file,
        res->status, nfs3_error(cres->status));
    return -1;
  }

return 0;
}

int nfsfilecreate( t_nfsclt *nfsclt, char *path, struct stat *fstat ) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  if ( pathsplit(path, &dir, &file ) == -1 )
    return -1;

//  printf("dir: %s, file: %s\n", dir, file);

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3filecreate( nfsclt, dir, file, fstat );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3filerm( t_nfsclt *nfsclt, char *dir, char *file) {

  REMOVE3args rargs;
  REMOVE3res *rres;

  // lookup directory handle
  LOOKUP3res *res;
  res = nfs3pathlookup( nfsclt, dir, 0);
  if ( res == NULL ) return -1;

  if ( res->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  // set new file attributes
  memset(&rargs, 0, sizeof(rargs));
  nfs_fh3copy(&rargs.object.dir, &res->LOOKUP3res_u.resok.object);
  rargs.object.name = file;

  rres = nfsproc3_remove_3(&rargs, nfsclt->nfs.client);
  nfs_fh3free(&rargs.object.dir); 

  if ( rres == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_remove_3()");
    return -1;
  }

  if (rres->status != NFS3_OK) {
    fprintf(stderr, "Removing file: %s - (%d) %s\n", file,
        res->status, nfs3_error(rres->status));
    return -1;
  }

return 0;
}

int nfsfilerm( t_nfsclt *nfsclt, char *path) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  if ( pathsplit(path, &dir, &file ) == -1 )
    return -1;

//  printf("dir: %s, file: %s\n", dir, file);

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3filerm( nfsclt, dir, file );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3fileattr( t_nfsclt *nfsclt, char *filename, struct stat *fstat) {

  SETATTR3args sargs;
  SETATTR3res *sres;
  sattr3 *sattr;

  // lookup file handle
  LOOKUP3res *res;
  res = nfs3pathlookup( nfsclt, filename, 0);
  if ( res == NULL ) return -1;

  // set new attributes
  memset(&sargs, 0, sizeof(sargs));
  nfs_fh3copy(&sargs.object, &res->LOOKUP3res_u.resok.object);

  stat_to_sattr3(&sargs.new_attributes, fstat);

  sres = nfsproc3_setattr_3(&sargs, nfsclt->nfs.client);
  nfs_fh3free(&sargs.object); 

  if ( sres == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_setattr_3()");
    return -1;
  }

  if (sres->status != NFS3_OK) {
    fprintf(stderr, "Setting attributes: %s - (%d) %s\n", filename,
        res->status, nfs3_error(sres->status));
    return -1;
  }

return 0;
}

int nfsfileattr( t_nfsclt *nfsclt, char *path, struct stat *fstat ) {

  fstat->st_dev = 0;  // don't try to create device

  switch ( nfsclt->version ) {
    case 30:
      return nfs3fileattr( nfsclt, path, fstat );
    break;
  }

return -1;
}

int nfs3dirmk( t_nfsclt *nfsclt, char *dir, char *file, struct stat *fstat ) {

  MKDIR3args args;
  MKDIR3res *res;

  // lookup directory handle
  LOOKUP3res *lres;
  lres = nfs3pathlookup( nfsclt, dir, 0);
  if ( lres == NULL ) return -1;

  if ( lres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  // set new file attributes
  memset(&args, 0, sizeof(args));
  nfs_fh3copy(&args.where.dir, &lres->LOOKUP3res_u.resok.object);
  args.where.name = file;

  stat_to_sattr3(&args.attributes, fstat);

  res = nfsproc3_mkdir_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.where.dir); 

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_mkdir_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "Creating directory: %s - (%d) %s\n", file,
        res->status, nfs3_error(res->status));
    return -1;
  }

return 0;
}

int nfsdirmk( t_nfsclt *nfsclt, char *path, struct stat *fstat ) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  fstat->st_dev = 0;  // don't try to create device

  if ( pathsplit(path, &dir, &file ) == -1 )
    return -1;

//  printf("dir: %s, file: %s\n", dir, file);

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3dirmk( nfsclt, dir, file, fstat );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3dirrm( t_nfsclt *nfsclt, char *dir, char *file) {

  RMDIR3args args;
  RMDIR3res *res;

  // lookup directory handle
  LOOKUP3res *dres;
  dres = nfs3pathlookup( nfsclt, dir, 0);
  if ( dres == NULL ) return -1;

  if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  memset(&args, 0, sizeof(args));
  nfs_fh3copy(&args.object.dir, &dres->LOOKUP3res_u.resok.object);
  args.object.name = file;

  res = nfsproc3_rmdir_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.object.dir); 

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_rmdir_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "Removing directory: %s - (%d) %s\n", file,
        res->status, nfs3_error(res->status));
    return -1;
  }

return 0;
}

int nfsdirrm( t_nfsclt *nfsclt, char *path) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  if ( pathsplit(path, &dir, &file ) == -1 )
    return -1;

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3dirrm( nfsclt, dir, file );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3move(
    t_nfsclt *nfsclt,
    char *srcdir, char *srcfile,
    char *dstdir, char *dstfile ) {

  RENAME3args args;
  RENAME3res *res;

  memset(&args, 0, sizeof(args));

  // lookup src directory
  LOOKUP3res *dres;
  dres = nfs3pathlookup( nfsclt, srcdir, 0);
  if ( dres == NULL ) return -1;

  if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", srcdir);
    return -1;
  }

  nfs_fh3copy(&args.from.dir, &dres->LOOKUP3res_u.resok.object);
  args.from.name = srcfile;

  // lookup dst directory
  dres = nfs3pathlookup( nfsclt, dstdir, 0);
  if ( dres == NULL ) return -1;

  if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dstdir);
    return -1;
  }

  nfs_fh3copy(&args.to.dir, &dres->LOOKUP3res_u.resok.object);
  if ( dstfile == NULL ) {
    args.to.name = srcfile;
  } else {
    args.to.name = dstfile;
  }

  res = nfsproc3_rename_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.from.dir); 
  nfs_fh3free(&args.to.dir); 

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_rename_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "Moving to %s: (%d) %s\n", args.to.name,
        res->status, nfs3_error(res->status));
    return -1;
  }

return 0;
}

int nfsmove( t_nfsclt *nfsclt, char *src, char *dst) {

  char *srcdir = NULL, *srcfile = NULL;
  char *dstdir = NULL, *dstfile = NULL;
  int ret = -1;

  if ( pathsplit(src, &srcdir, &srcfile ) == -1 )
    return -1;

  if ( pathsplit(dst, &dstdir, &dstfile ) == -1 )
    return -1;

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3move( nfsclt, srcdir, srcfile, dstdir, dstfile );
    break;
  }

  if ( srcdir ) free(srcdir);
  if ( srcfile ) free(srcfile);
  if ( dstdir ) free(dstdir);
  if ( dstfile ) free(dstfile);

return ret;
}

int nfs3link( t_nfsclt *nfsclt, char *target, char *dir, char *file) {

  LINK3args args;
  LINK3res *res;

  // lookup handle for the directory in which the link is to be created
  LOOKUP3res *dres;
  dres = nfs3pathlookup( nfsclt, dir, 0);
  if ( dres == NULL ) return -1;

  if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  memset(&args, 0, sizeof(args));
  nfs_fh3copy(&args.link.dir, &dres->LOOKUP3res_u.resok.object);
  args.link.name = file;

  // lookup file handle for the existing file system object
  dres = nfs3pathlookup( nfsclt, target, 0);
  if ( dres == NULL ) return -1;

  nfs_fh3copy(&args.file, &dres->LOOKUP3res_u.resok.object);

  res = nfsproc3_link_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.link.dir); 
  nfs_fh3free(&args.link.dir); 

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_link_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "Creating link: %s - (%d) %s\n", file,
        res->status, nfs3_error(res->status));
    return -1;
  }

return 0;
}

int nfslink( t_nfsclt *nfsclt, char *target, char *linkname) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  if ( pathsplit(linkname, &dir, &file ) == -1 )
    return -1;

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3link( nfsclt, target, dir, file );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3symlink(
    t_nfsclt *nfsclt, char *target,
    char *dir, char *file, struct stat *fstat) {

  SYMLINK3args args;
  SYMLINK3res *res;

  // lookup handle for the directory in which the link is to be created
  LOOKUP3res *dres;
  dres = nfs3pathlookup( nfsclt, dir, 0);
  if ( dres == NULL ) return -1;

  if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  memset(&args, 0, sizeof(args));
  nfs_fh3copy(&args.where.dir, &dres->LOOKUP3res_u.resok.object);
  args.where.name = file;

  stat_to_sattr3(&args.symlink.symlink_attributes, fstat);
  args.symlink.symlink_data = target;

  res = nfsproc3_symlink_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.where.dir); 

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_symlink_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "Creating symbolic link: %s - (%d) %s\n", file,
        res->status, nfs3_error(res->status));
    return -1;
  }

return 0;
}

int nfssymlink( t_nfsclt *nfsclt, char *target, char *linkname, struct stat *fstat) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  fstat->st_dev = 0;  // don't try to create device

  if ( pathsplit(linkname, &dir, &file ) == -1 )
    return -1;

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3symlink( nfsclt, target, dir, file, fstat );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3mknod(
    t_nfsclt *nfsclt, char *dir, char *file,
    struct stat *fstat, dev_t dev) {

  MKNOD3args args;
  MKNOD3res *res;

  // lookup handle for the directory
  LOOKUP3res *dres;
  dres = nfs3pathlookup( nfsclt, dir, 0);
  if ( dres == NULL ) return -1;

  if ( dres->LOOKUP3res_u.resok.obj_attributes.post_op_attr_u.attributes.type
      != NF3DIR ) {

    fprintf(stderr, "%s: is not a directory\n", dir);
    return -1;
  }

  memset(&args, 0, sizeof(args));
  nfs_fh3copy(&args.where.dir, &dres->LOOKUP3res_u.resok.object);
  args.where.name = file;

  switch ( fstat->st_mode & ~0777) {
  case S_IFSOCK:
    args.what.type = NF3SOCK;
    stat_to_sattr3(&args.what.mknoddata3_u.pipe_attributes, fstat);
  break;
  case S_IFIFO:
    args.what.type = NF3FIFO;
    stat_to_sattr3(&args.what.mknoddata3_u.pipe_attributes, fstat);
  break;
  case S_IFBLK:
    args.what.type = NF3BLK;
    args.what.mknoddata3_u.device.spec.specdata1 = major(dev);
    args.what.mknoddata3_u.device.spec.specdata2 = minor(dev);
    stat_to_sattr3(&args.what.mknoddata3_u.device.dev_attributes, fstat);
  break;
  case S_IFCHR:
    args.what.type = NF3CHR;
    args.what.mknoddata3_u.device.spec.specdata1 = major(dev);
    args.what.mknoddata3_u.device.spec.specdata2 = minor(dev);
    stat_to_sattr3(&args.what.mknoddata3_u.device.dev_attributes, fstat);
  break;
  }

  res = nfsproc3_mknod_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.where.dir); 

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_mknod_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "Creating node: %s - (%d) %s\n", file,
        res->status, nfs3_error(res->status));
    return -1;
  }

return 0;
}

int nfsmknod( t_nfsclt *nfsclt, char *path, struct stat *fstat, dev_t dev) {

  char *dir = NULL, *file = NULL;
  int ret = -1;

  if ( pathsplit(path, &dir, &file ) == -1 )
    return -1;

  switch ( nfsclt->version ) {
    case 30:
      ret = nfs3mknod( nfsclt, dir, file, fstat, dev );
    break;
  }

  if ( dir ) free(dir);
  if ( file ) free(file);

return ret;
}

int nfs3printstat( t_nfsclt *nfsclt) {

  FSSTAT3args args;
  FSSTAT3res *res;
  
  memset(&args, 0, sizeof(args));

  if ( nfsclt->mountres.nfs3 != NULL ) {
    fhandle3_to_nfs_fh3(&args.fsroot,
      &nfsclt->mountres.nfs3->mountres3_u.mountinfo.fhandle);
  } else {
    nfs_fh3copy(&args.fsroot, &nfsclt->currentdir.nfs3);
  }
  
  res = nfsproc3_fsstat_3(&args, nfsclt->nfs.client);
  nfs_fh3free(&args.fsroot);

  if ( res == NULL ) {
    clnt_perror(nfsclt->nfs.client, "nfsproc3_fsstat_3()");
    return -1;
  }

  if (res->status != NFS3_OK) {
    fprintf(stderr, "File system state information: (%d) %s\n",
        res->status, nfs3_error(res->status));
    return -1;
  }

  char buf[128];
  FSSTAT3resok *fsres = &res->FSSTAT3res_u.resok;
  printf("%s:%s    size: %s,", nfsclt->hostname, nfsclt->mountpath,
    hrbytes(buf, sizeof(buf), fsres->tbytes));
  printf(" used: %s,", hrbytes(buf, sizeof(buf), (fsres->tbytes - fsres->fbytes)));
  printf(" free: %s", hrbytes(buf, sizeof(buf), fsres->fbytes));
  printf(" (%s useable)\n", hrbytes(buf, sizeof(buf), fsres->abytes));

return 0;
}

int nfsprintstat(t_nfsclt *nfsclt) {

  switch ( nfsclt->version ) {
    case 30:
      return nfs3printstat( nfsclt );
    break;
  }

return -1;
}

