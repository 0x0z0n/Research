/*
 * 
 * Adrian Brzezinski (2018) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#include "utils.h"

int pathsplit( char *path, char **dir, char **file ) {

  char *p, *pend, *d, *f;

  p = strdup(path);
  if ( p == NULL ) return -1;

  pend = p+(strlen(p)-1);

  // search for filename
  for ( f = pend; f != p && *f != '/' ; f-- ) ;

  if ( f == p ) {
    // we reached beginning of the path

    if ( *f == '/' ) {
      // path like "/file", use root
      d = strdup("/");
      f++; // omit '/'
    } else {
      // no path at all, use current directory
      d = strdup(".");
    }
  } else {
    // searching stopped by '/'

    if ( f == pend ) {
      // no file name, path like "/dir/dir2/"
      f = NULL;
    } else {
      *f++ = '\0';   // overwrite '/'
    }

    d = strdup(p);
  }

  if ( f ) f = strdup(f);

  free(p);

  // overwrite passed pointers
  *dir = d;
  *file = f;

return 0;
}

char *stat_ftype( mode_t mode ) {
  switch ( mode & S_IFMT ) {
  case S_IFSOCK:
    return "socket";
  case S_IFLNK:
    return "symbolic link";
  case S_IFREG:
    return "regular file";
  case S_IFBLK:
    return "block device";
  case S_IFDIR:
    return "directory";
  case S_IFCHR:
    return "character device";
  case S_IFIFO:
    return "FIFO";
  }

return "unknown";
}

cap_flag_value_t cap_flag(pid_t pid, cap_value_t cap) {
  
  cap_flag_value_t flag_value = CAP_CLEAR;

  if ( pid == 0 ) pid = getpid();

  cap_t cap_p = cap_get_pid(pid);

  cap_get_flag(cap_p, cap, CAP_EFFECTIVE, &flag_value);

  cap_free(cap_p);

return flag_value;
}

char *hrbytes(char *buf, unsigned int buflen, long long bytes) {

  double unit = 1024;
  char *units = { "KMGTPE" };

  if ( bytes < unit ) {
    snprintf(buf, buflen, "%lld B", bytes);
    return buf;
  }

  int exp = (int)(logl(bytes) / logl(unit));

  if ( exp > strlen(units) ) {
    snprintf(buf, buflen, "(too big value)");
  } else {
    snprintf(buf, buflen, "%.1f %ciB", (float)(bytes / powl(unit, exp)), units[exp-1]);
  }

return buf;
}

