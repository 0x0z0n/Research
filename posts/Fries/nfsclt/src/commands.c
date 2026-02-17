/*
 * 
 * Adrian Brzezinski (2018) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#include "commands.h"

#define CHECK_ARGS_NUM(num) \
  { \
    if ( argc != (num+1) ) { \
      fprintf(stderr,"%s: Wrong arguments number\n", argv[0]); \
      return -1; \
    } \
  }

#define CHECK_ARGS_MAXNUM(num) \
  { \
    if ( argc > (num+1) ) { \
      fprintf(stderr,"%s: Too many arguments\n", argv[0]); \
      return -1; \
    } \
  }

#define CHECK_HOSTNAME \
  { \
    if ( nfsclt.hostname == NULL ) { \
      fprintf(stderr, "%s: Hostname not set\n", argv[0]); \
      return -1; \
    } \
  }

int cmd_help( int argc, char **argv) {
  int i, col;

  CHECK_ARGS_MAXNUM(1);

  if ( argc == 1 ) {
    printf("List of available commands printed below.\n" \
        "Use 'help command' to display detailed description\n\n");
  }

  for (i = 0, col = 0; commands[i].name; i++) {

    if ( argc > 1 ) {
      if ( strcmp(argv[1], commands[i].name) == 0 ) {
        printf("%s\t%s", commands[i].name, commands[i].desc);
        break;
      }
    } else {
      printf("%s\t\t", commands[i].name);
      
      col++;
      if ( !(col % 5) ) printf("\n");
    }
  }

  printf("\n");
return 0;
}

int cmd_exports( int argc, char **argv) {

  exports exp;
  groups grp;

  CHECK_ARGS_MAXNUM(0);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, MOUNT_PROGRAM ) == -1 )
    return -1;

  for ( exp = nfsexports( &nfsclt ); exp != NULL ; exp = exp->ex_next ) {

    printf("%s ", exp->ex_dir);

    if ((grp = exp->ex_groups) == NULL)
      printf("everyone");

    for ( ; grp != NULL ; grp = grp->gr_next )
      printf("%s ", grp->gr_name);

    printf("\n");
  }

return 0;
}

int cmd_mount( int argc, char **argv) {

  char *path = NULL;

  CHECK_ARGS_MAXNUM(1);

  if ( argc == 2 )
    path = argv[1];

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, MOUNT_PROGRAM ) == -1 )
    return -1;

  if ( path == NULL ) {
    printf("No path given, please set file handle manually\n");
    return 0;
  }

return nfsmount(&nfsclt, path);
}

int cmd_umount( int argc, char **argv) {

  CHECK_ARGS_MAXNUM(0);

  nfsumount( &nfsclt );
  nfsdisconnect( &nfsclt.nfs );
  nfsdisconnect( &nfsclt.mount );

return 0;
}

int cmd_quit( int argc, char **argv) {

  char *args[2] = {"umount", "" };
  cmd_umount(1, args );
  exit(0);
}

int cmd_ls( int argc, char **argv) {

  tp_nfsdir nfsdir;
  char *path = NULL;
  int ret, i, printattrs = 0;

  CHECK_ARGS_MAXNUM(2);

  CHECK_HOSTNAME;

  for ( i=1; i < argc ; i++ ) {

    if ( !strcmp(argv[i], "-l") ) {
      printattrs = 1;
      continue;
    } else {
      path = argv[i];
    }
  }

  // connecting to nfs daemon
  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  memset(&nfsdir, 0, sizeof(nfsdir));

  do {

    ret = nfsdirread( &nfsclt, &nfsdir, path);
    if ( ret == -1 ) return -1;

    if ( nfsdirprint( &nfsclt, &nfsdir, printattrs, path) == -1 )
      return -1;

  } while ( ret > 0 );

return 0;
}

int cmd_cd( int argc, char **argv ) {

  char *path = NULL;

  CHECK_ARGS_MAXNUM(1);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  if ( argc == 2 )
    path = argv[1];

return nfscd( &nfsclt, path );
}

int cmd_cat( int argc, char **argv) {

  char filedata[8192];
  char *file = NULL;
  long offset = 0;
  int rlen = 0;

  CHECK_ARGS_NUM(1);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  if ( argc == 2 )
    file = argv[1];

  while ( (rlen = nfsfilepread( &nfsclt, file, offset, filedata, sizeof(filedata))) > 0 ) {

    if ( rlen == -1 ) return -1;

    fwrite(filedata, rlen, sizeof(char), stdout);

    offset += rlen;
  }

return 0;
}

int cmd_handle( int argc, char **argv) {

  char *handle = NULL;

  CHECK_ARGS_MAXNUM(1);

  if ( argc == 1 ) {
    nfshandleprint(&nfsclt.currentdir, nfsclt.version);
    return 0;
  }

  handle = argv[1];
  nfshandleset_str(&nfsclt.currentdir, nfsclt.version, handle);

return 0;
}

int cmd_set( int argc, char **argv) {

  int i;

  if ( argc == 1 ) {

    if ( nfsclt.hostname )
      printf("host: %s\n", nfsclt.hostname);
    else
      printf("host: <not set>\n");

    printf("uid:\t%d\n", nfsclt.uid);
    printf("gid:\t%d\n", nfsclt.gid);
    printf("mode:\t%o\n", nfsclt.mode);

    return 0;
  }

  if ( argc < 3 ) {
    fprintf(stderr,"%s: Too less arguments\n", argv[0]);
    return -1;
  }

  for ( i=1; i < argc ; i++ ) {

    if ( !strcmp(argv[i], "host") ) {
      if ( nfsclt.hostname ) free(nfsclt.hostname);
      nfsclt.hostname = strdup(argv[i+1]);
      break;
    }

    if ( !strcmp(argv[i], "uid") ) {
      nfsclt.uid = atoi(argv[i+1]);
      break;
    }

    if ( !strcmp(argv[i], "gid") ) {
      nfsclt.gid = atoi(argv[i+1]);
      break;
    }

    if ( !strcmp(argv[i], "mode") ) {
      if (sscanf(argv[i+1], "%o", &nfsclt.mode) != 1) {
        fprintf(stderr, "%s: invalid mode\n", argv[0]);
        return -1;
      }
      break;
    }
  }

  if ( i == argc ) {
    fprintf(stderr,"%s: not recognized arguments\n", argv[0]);
    return -1;
  }

return 0;
}

int cmd_lcd( int argc, char **argv) {

  char *path = NULL;

  CHECK_ARGS_MAXNUM(1);

  if ( argc == 2 ) {
    path = argv[1];
  } else {
    path = getenv("HOME");
  }

  if ( chdir(path) == -1 ) {
    perror(path);
    return -1;
  }

return 0;
}

int cmd_lpwd( int argc, char **argv) {

  char *path = NULL;
  int pathlen = 0;

  CHECK_ARGS_MAXNUM(0);

  // alloc buffer for path
  do {
    if ( path ) free(path);

    pathlen += PATH_MAX;
    path = calloc( pathlen, sizeof(char));

  } while( getcwd( path, pathlen-1) == NULL && errno == ERANGE);

  if ( path ) {
    printf("%s\n", path);
    free(path);
  } else {
    perror(path);
    return -1;
  }

return 0;
}

int cmd_get( int argc, char **argv) {

  char filedata[16384];
  char *rfile = NULL; // remote file
  char *lfile = NULL; // local file
  FILE *lf;
  long offset = 0;
  int rlen = 0;

  CHECK_ARGS_MAXNUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  if ( argc >= 2 )
    rfile = argv[1];

  if ( argc == 3 )
    lfile = argv[2];
  else
    lfile = rfile;

  if ( rfile == NULL ) {
    fprintf(stderr, "Remote file not specified\n");
    return -1;
  }

  struct stat filestat;
  if ( !stat(lfile, &filestat) ) {

    printf("Overwrite local file '%s'? [Y]: ", lfile);

    filedata[0] = '\0';
    if ( fgets(filedata, sizeof(filedata), stdin) != NULL) {
      if (filedata[0] != 'y' && filedata[0] != 'Y') {
        printf("Bailing out!\n");
        return 0;
      }
    }
  }

  if ((lf = fopen(lfile, "w")) == NULL) {
    perror("fopen");
    return -1;
  }
  
  while ( (rlen = nfsfilepread( &nfsclt, rfile, offset, filedata, sizeof(filedata))) > 0 ) {

    if ( rlen == -1 ) break;

    fwrite(filedata, sizeof(char), rlen, lf);

    offset += rlen;
  }

  fclose(lf);

return 0;
}

int cmd_put( int argc, char **argv) {

  char filedata[16384];
  char *rfile = NULL; // remote file
  char *lfile = NULL; // local file
  FILE *lf;   // local file handle
  long offset = 0;
  int rlen = 0, wlen = 0;
  struct stat filestat;

  CHECK_ARGS_MAXNUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  if ( argc >= 2 )
    lfile = argv[1];

  if ( argc == 3 )
    rfile = argv[2];
  else
    rfile = lfile;

  if ( rfile == NULL ) {
    fprintf(stderr, "Local file not specified\n");
    return -1;
  }

  if ((lf = fopen(lfile, "r")) == NULL) {
    perror("fopen");
    return -1;
  }

  printf("Checking whatever remote file exists...\n");
  if ( nfsfilestat( &nfsclt, rfile, &filestat ) != -1 ) {

    printf("Overwrite remote file '%s'? [Y]: ", rfile);

    filedata[0] = '\0';
    if ( fgets(filedata, sizeof(filedata), stdin) != NULL) {
      if (filedata[0] != 'y' && filedata[0] != 'Y') {
        printf("Bailing out!\n");
        return 0;
      }
    }
  } else {
    // create nfs file, copy stats from local file

    if ( stat(lfile, &filestat) ) {
      perror("stat()");
      return -1;
    }

    filestat.st_dev = 0;  // don't try to create device
    filestat.st_uid = nfsclt.uid;
    filestat.st_gid = nfsclt.gid;

    if ( nfsfilecreate( &nfsclt, rfile, &filestat ) == -1 )
      return -1;
  }

  do {
    rlen = fread(filedata, sizeof(char), sizeof(filedata), lf);
    if ( rlen == -1 ) break;

    wlen = nfsfilepwrite( &nfsclt, rfile, offset, filedata, rlen);
    if ( wlen == -1 ) break;
    if ( wlen != rlen ) {
      fprintf(stderr, "%s - %i bytes written but %i requested!\n",
          rfile, wlen, rlen);
      break;
    }

    offset += wlen;

  } while ( !feof(lf) );

  fclose(lf);

return 0;
}

int cmd_rm( int argc, char **argv) {

  char answer[10];
  char *file = NULL;
  int i, force = 0;

  CHECK_ARGS_MAXNUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  for ( i=1; i < argc ; i++ ) {

    if ( !strcmp(argv[i], "-f") ) {
      force = 1;
      continue;
    } else {
      file = argv[i];
    }
  }

  if ( file == NULL ) {
    fprintf(stderr,"%s: missing operand\n", argv[0]);
    return -1;
  }

  if ( !force ) {
    printf("Remove remote file '%s'? [Y]: ", file);

    answer[0] = '\0';
    if ( fgets(answer, sizeof(answer), stdin) != NULL) {
      if (answer[0] != 'y' && answer[0] != 'Y') {
        printf("Bailing out!\n");
        return 0;
      }
    }
  }

return nfsfilerm( &nfsclt, file );
}

int cmd_chmod( int argc, char **argv) {

  char *file;
  struct stat filestat;
  unsigned int mode;

  CHECK_ARGS_NUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  file = argv[2];

  if (sscanf(argv[1], "%o", &mode) != 1) {
    fprintf(stderr, "%s: invalid mode\n", argv[0]);
    return -1;
  }

  memset(&filestat, 0, sizeof(filestat));
  if ( nfsfilestat( &nfsclt, file, &filestat ) == -1 )
    return -1;

  filestat.st_mode = mode;

return nfsfileattr( &nfsclt, file, &filestat);
}

int cmd_chown( int argc, char **argv) {

  char *file;
  struct stat filestat;
  int uid, gid;

  CHECK_ARGS_NUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  file = argv[2];

  if (sscanf(argv[1], "%i:%i", &uid, &gid) != 2) {
    if (sscanf(argv[1], "%i", &uid) != 1) {

      fprintf(stderr, "%s: invalid owner or group\n", argv[0]);
      return -1;
    }
    gid = -1;
  }

  memset(&filestat, 0, sizeof(filestat));
  if ( nfsfilestat( &nfsclt, file, &filestat ) == -1 )
    return -1;

  filestat.st_uid = uid;
  if ( gid != -1 ) filestat.st_gid = gid;

return nfsfileattr( &nfsclt, file, &filestat);
}

int cmd_mkdir( int argc, char **argv) {

  char *dir;
  struct stat dirstat;

  CHECK_ARGS_NUM(1);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  dir = argv[1];

  memset(&dirstat, 0, sizeof(dirstat));
  dirstat.st_mode = nfsclt.mode;
  dirstat.st_uid = nfsclt.uid;
  dirstat.st_gid = nfsclt.gid;

return nfsdirmk( &nfsclt, dir, &dirstat);
}

int cmd_rmdir( int argc, char **argv) {

  char answer[10];
  char *dir = NULL;
  int i, force = 0;

  CHECK_ARGS_MAXNUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  for ( i=1; i < argc ; i++ ) {

    if ( !strcmp(argv[i], "-f") ) {
      force = 1;
      continue;
    } else {
      dir = argv[i];
    }
  }

  if ( dir == NULL ) {
    fprintf(stderr,"%s: missing operand\n", argv[0]);
    return -1;
  }

  if ( !force ) {
    printf("Remove remote directory '%s'? [Y]: ", dir);

    answer[0] = '\0';
    if ( fgets(answer, sizeof(answer), stdin) != NULL) {
      if (answer[0] != 'y' && answer[0] != 'Y') {
        printf("Bailing out!\n");
        return 0;
      }
    }
  }

return nfsdirrm( &nfsclt, dir );
}

int cmd_mv( int argc, char **argv) {

  char *src = NULL, *dst = NULL;
  struct stat dirstat;

  CHECK_ARGS_NUM(2);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  src = argv[1];
  dst = argv[2];

return nfsmove( &nfsclt, src, dst);
}

int cmd_ln( int argc, char **argv) {

  char *dir;
  char *target = NULL, *linkname = NULL;
  struct stat lstat;
  int symbolic = 0, i;

  CHECK_ARGS_MAXNUM(3);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  for ( i=1; i < argc ; i++ ) {

    if ( !strcmp(argv[i], "-s") ) {
      symbolic = 1;
      continue;
    } else if ( target == NULL ) {
      target = argv[i];
    } else {
      linkname = argv[i];
    }
  }

  if ( target == NULL || linkname == NULL ) {
    fprintf(stderr, "%s: Target or link name not set\n", argv[0]);
    return -1;
  }

  if ( symbolic ) {
    memset(&lstat, 0, sizeof(lstat));
    lstat.st_mode = nfsclt.mode;
    lstat.st_uid = nfsclt.uid;
    lstat.st_gid = nfsclt.gid;

    return nfssymlink( &nfsclt, target, linkname, &lstat);
  } 

return nfslink(&nfsclt, target, linkname);
}

int cmd_mknod( int argc, char **argv) {

  char *name = NULL, *type = NULL;
  int major, minor;
  dev_t dev = 0;
  struct stat fstat;

  CHECK_ARGS_MAXNUM(4);

  if ( argc < 3 ) {
    fprintf(stderr, "%s: Too few arguments\n", argv[0]);
    return -1;
  }

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  name = argv[1];
  type = argv[2];

  memset(&fstat, 0, sizeof(fstat));
  fstat.st_mode = nfsclt.mode;
  fstat.st_uid = nfsclt.uid;
  fstat.st_gid = nfsclt.gid;

  switch ( *type ) {
  case 's':
    CHECK_ARGS_NUM(2);

    fstat.st_mode |= S_IFSOCK;
  break;
  case 'p':
    CHECK_ARGS_NUM(2);

    fstat.st_mode |= S_IFIFO;
  break;

  case 'b':
    CHECK_ARGS_NUM(4);

    major = atoi(argv[3]);
    minor = atoi(argv[4]);
    dev = makedev(major, minor);
    fstat.st_mode |= S_IFBLK;
  break;

  case 'c':
    CHECK_ARGS_NUM(4);

    major = atoi(argv[3]);
    minor = atoi(argv[4]);
    dev = makedev(major, minor);
    fstat.st_mode |= S_IFCHR;
  break;

  default:
    fprintf(stderr, "%s: Unsupported type: '%s'\n", argv[0], type);
    return -1;
  }

return nfsmknod( &nfsclt, name, &fstat, dev);
}

int cmd_stat( int argc, char **argv) {

  char *file = NULL;
  struct stat fstat;

  CHECK_ARGS_NUM(1);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM) == -1 )
    return -1;

  file = argv[1];

  if ( nfsfilestat( &nfsclt, file, &fstat ) == -1 )
    return -1;

  printf("File: %s\t%s\n", file, stat_ftype(fstat.st_mode));
  printf("Size: %ld\n", fstat.st_size);
  printf("Device: %lx\tInode: %ld\tLinks: %ld\n",
    fstat.st_dev, fstat.st_ino, fstat.st_nlink);
  printf("Access: 0%o\tUid: %i\tGid: %i\n",
    fstat.st_mode&0777, fstat.st_uid, fstat.st_gid);
  printf ("Inode Last Change at: %s", ctime (&fstat.st_ctime));
  printf ("      Last access at: %s", ctime (&fstat.st_atime));
  printf ("    Last modified at: %s", ctime (&fstat.st_mtime));

return 0;
}

int cmd_df( int argc, char **argv) {

  CHECK_ARGS_MAXNUM(0);

  CHECK_HOSTNAME;

  if ( nfsconnect( &nfsclt, NFS_PROGRAM ) == -1 )
    return -1;

return nfsprintstat(&nfsclt);
}

t_command commands[] = {
  { cmd_exports, "exports",
    "\n\n\tShow the NFS server's export list\n" \
  },
  { cmd_mount, "mount",
    "[PATH]\n\n" \
    "\tMount exported PATH from NFS server\n" \
  },
  { cmd_umount, "umount",
    "\n\n\tUnmount NFS and close connections\n"
  },
  { cmd_ls, "ls",
    "[-l] [PATH]\n\n" \
    "\tPrint current directory entries\n\n" \
    "\t-l\tprint also file atributes\n" \
    "\tPATH\toptional path to directory\n"
  },
  { cmd_cd, "cd",
    "<PATH>\n\n" \
    "\tChange current directory to PATH\n" \
  },
  { cmd_lcd, "lcd",
    "<PATH>\n\n" \
    "\tChange local working directory to PATH\n" \
  },
  { cmd_lpwd, "lpwd",
    "\n\n" \
    "\tPrint out the current working directory\n"
  },

  { cmd_cat, "cat",
    "<FILE>\n\n" \
    "\tDisplay content of the file FILE\n" \
  },
  { cmd_get, "get",
    "<RFILE> [LFILE]\n\n" \
    "\tGet remote file RFILE\n\n" \
    "\tLFILE\toptional local file name to save to\n"
  },
  { cmd_put, "put",
    "<LFILE> [RFILE]\n\n" \
    "\tPut local file LFILE to remote server\n\n" \
    "\tRFILE\toptional remote file name to save to\n"
  },
  { cmd_rm, "rm",
    "[-f] <FILE>\n\n" \
    "\tDelete file FILE from remote server\n\n" \
    "\t-f\tnever prompt before removal\n" \
  },
  { cmd_chmod, "chmod",
    "<MODE> <FILE>\n\n" \
    "\tChange mode on obcject FILE\n\n" \
    "\tMODE\tmode as octal number\n"
  },
  { cmd_chown, "chown",
    "<UID>[:GID] <FILE>\n\n" \
    "\tChange owner or group on FILE\n\n" \
    "\tuid[:gid]\tnumeric user id and optional group id\n"
  },
  { cmd_mkdir, "mkdir",
    "<DIR>\n\n" \
    "\tCreate directory with name DIR\n\n" \
  },
  { cmd_rmdir, "rmdir",
    "[-f] <DIR>\n\n" \
    "\tDelete directory DIR from remote server\n\n" \
    "\t-f\tnever prompt before removal\n" \
  },
  { cmd_mv, "mv",
    "<FROM> <TO>\n\n" \
    "\tMove or rename object from FROM to TO\n\n" \
  },
  { cmd_ln, "ln",
    "[-s] <TARGET> <LINK_NAME>\n\n" \
    "\tCreate link to TARGET with the name LINK_NAME\n\n" \
    "\t-s\tmake symbolic links instead of hard links\n" \
  },

  { cmd_mknod, "mknod",
    "<NAME> <TYPE> [MAJOR MINOR]\n\n" \
    "\tCreate the special file NAME of the given TYPE\n\n" \
    "\tTYPE is one of:\n"
    "\tp\tFIFO pipe\n" \
    "\ts\tsocket\n" \
    "\tb\tblock device with MAJOR MINOR\n" \
    "\tc\tchar device with MAJOR MINOR\n" \
  },
  { cmd_stat, "stat",
    "<FILE>\n\n" \
    "\tDisplay file status\n" \
  },
  { cmd_df, "df",
    "\n\n\tShow information about the file system\n" \
  },

  { cmd_handle, "handle",
    "[HANDLE]\n\n" \
    "\tDisplay or set current directory file handle\n\n" \
    "\tHANDLE\tdirectory file handle to set (string with hex numbers)\n"
  },
  { cmd_set, "set",
    "[PROPERTY] [VALUE]\n\n" \
    "\tSet one of client PROPERTY\n\n" \
    "\tSupported properties:\n"
    "\thost\thost name to connect to\n"
    "\tuid\tremote user id\n"
    "\tgid\tremote group id\n"
    "\tmode\toctal mode for newly created files and etc.\n"
  },

  { cmd_help, "help",
    "[COMMAND]\n\n" \
    "\tList available commands\n\n" \
    "\tCOMMAND\tprint detailed description about COMMAND\n"
  },
  { cmd_help, "?", "Synonym for 'help'" },
  { cmd_quit, "quit", "Exit the program" },
  { (tf_command *)NULL, (char *)NULL, (char *)NULL }
};

t_nfsclt nfsclt = {
  .version = 30,          // defaults to NFSv3
  .authtype = AUTH_UNIX,

  .uid = 65534, // nobody
  .gid = 65534,
  .mode = 0755
};

