
/*
 * 
 * Adrian Brzezinski (2005) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#include "netsocket.h"

int sockaddrsetup(
    struct sockaddr_in *addr, socklen_t addrlen,
    char *host, int port
    ) {

  struct hostent *he;

  memset(addr, 0, sizeof(addrlen));

  addr->sin_family = AF_INET;
  addr->sin_port = htons(port);

  // is it IP address?
  if ( !inet_aton(host, &addr->sin_addr) ) {

    // no, try to resolve name
    if ( !(he = gethostbyname(host)) ) {
      perror("gethostbyname()");
      return -1;
    }

    memcpy((char*)&addr->sin_addr, he->h_addr, he->h_length);
    addr->sin_family = he->h_addrtype;
  }

return 0;
}

void socksdsetup( int sd ) {

  int opt = 1;

  if ( setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, (void*)&opt, sizeof(int)) < 0 )
    perror("setsockopt(REUSEADDR)");

  opt = 1;
  if ( setsockopt(sd, SOL_SOCKET, SO_KEEPALIVE, (void*)&opt, sizeof(int)) < 0 )
    perror("setsockopt(KEEPALIVE)");

  // disable Nagle
  socknagle(sd, 0);

#ifndef _WIN32
  fcntl(sd, F_SETFD, FD_CLOEXEC);
#endif
}

int sockconnect( char *host, int port ) {

  struct sockaddr_in addr;
  socklen_t addrlen = sizeof(addr);

  int sd;

  if ( !host || port <= 0 ) return -1;

  if ( sockaddrsetup(&addr, addrlen, host, port) < 0 )
    return -1;

  if ( (sd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == -1 ) {
    perror("socket()");
    return -1;
  }

  socksdsetup(sd);

  if ( connect(sd, (struct sockaddr*)&addr, addrlen) != -1 )
    return sd;

  perror("connect()");
  sockclose(sd);

return -1;
}

// connect using specified source IP address or port
int sockconnectsrc(
    char *host, int port,
    char *srchost, int srcport
    ) {

  struct sockaddr_in addr;
  socklen_t addrlen = sizeof(addr);

  struct sockaddr_in srcaddr;
  socklen_t srcaddrlen = sizeof(srcaddr);

  int sd;

  if ( !host || port <= 0 ) return -1;

  if ( sockaddrsetup(&addr, addrlen, host, port) < 0 )
    return -1;

  if ( sockaddrsetup(&srcaddr, srcaddrlen, srchost, srcport) < 0 ) {
    return -1;
//    srcaddr.sin_addr.s_addr = htonl(INADDR_ANY);
  }

  if ( (sd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == -1 ) {
    perror("socket()");
    return -1;
  }

  socksdsetup(sd);

  // bind connection to source IP:PORT
  if ( bind(sd, (struct sockaddr*)&srcaddr, srcaddrlen) == -1 ) {
    perror("bind()");
    goto ERR;
  }

  if ( connect(sd, (struct sockaddr*)&addr, addrlen) != -1 )
    return sd;

  // omit perror, so in case where we searching for privileged port,
  // we aren't spammed with error messages
  //perror("connect()");

ERR:
  sockclose(sd);

return -1;
}

int sockbind( char *host, int port, int listnum ) {

  struct sockaddr_in addr;
  socklen_t addrlen = sizeof(addr);

  int sd;

  if ( !host || port <= 0 || listnum <= 0 ) return 1;

  if ( sockaddrsetup(&addr, addrlen, host, port) < 0 )
    return -1;

  if ( (sd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)) == -1)
    return -1;

  socksdsetup(sd);

  if ( bind(sd, (struct sockaddr*)&addr, addrlen) == -1 ) {
    perror("bind()");
    goto ERR;
  }

  if ( listen(sd, listnum) == -1 ) {
    perror("listen()");
    goto ERR;
  }

return sd;

ERR:
  sockclose(sd);

return -1;
}

int sockaccept( int sd ) {

  struct sockaddr_in sckadr;
  socklen_t size_sckadr = sizeof(sckadr);
  int asd;

  if ( sd < 0 ) return -1;

  memset(&sckadr, 0, sizeof(sckadr));

  if ( (asd = accept(sd, (struct sockaddr*)&sckadr, &size_sckadr)) == -1) {
    perror("accept()");
    return -1;
  }

return asd;
}

int sockpending( int sd ) {

  int rlen = 0;

  ioctl(sd, FIONREAD, &rlen);

return rlen;
}

int sockread( int sd, char *data, int data_len ) {

  int n;

  if ( !data || data_len <= 0 ) return -1;

  do {
    n = read(sd, data, sizeof(char)*data_len);
  } while ( n < 0 && errno == EINTR );

return n;
}

int sockwrite( int sd, char *data, int data_len ) {

  int n;

  if ( !data ) return -1;

  // assume it's ascii string
  if ( data_len == 0 )
    data_len = strlen(data);

  do {
    n = write(sd, data, sizeof(char)*data_len);
  } while ( n < 0 && errno == EINTR );

return n;
}

int sockwritef( int sd, char *format, ... ) {

  va_list vl;
  static char string[BUFSIZE];

  va_start( vl, format );
  vsnprintf( string, sizeof(string), format, vl);
  va_end( vl );

return sockwrite(sd, string, 0);
}


void sockclose( int sd ) {

  if ( sd > 0 )
    close(sd);
}

// is connection established?
int sockisconnected( int sd ) {

  struct sockaddr_in sckadr;
  socklen_t size_sckadr = sizeof(sckadr);

  if ( !getpeername(sd, (struct sockaddr*)&sckadr, &size_sckadr) )
    return 1;

return 0;
}

int sockport( int sd ) {

  struct sockaddr_in sckadr;
  socklen_t size_sckadr = sizeof(sckadr);

  if ( getsockname(sd, (struct sockaddr*)&sckadr, &size_sckadr) < 0 ) {
    perror("getsockname()");
    return 0;
  }

return ntohs(sckadr.sin_port);
}

int sockpeerport( int sd ) {

  struct sockaddr_in sckadr;
  socklen_t size_sckadr = sizeof(sckadr);

  if ( getpeername(sd, (struct sockaddr*)&sckadr, &size_sckadr) < 0 ) {
    perror("getpeername()");
    return 0;
  }

return ntohs(sckadr.sin_port);
}

// get socket name
char* sockname( int sd ) {

  struct sockaddr_in sckadr;
  socklen_t size_sckadr = sizeof(sckadr);

  if ( getsockname(sd, (struct sockaddr*)&sckadr, &size_sckadr) < 0 ) {
    perror("getsockname()");
    return 0;
  }

return inet_ntoa(sckadr.sin_addr);
}

// get name of connected peer socket
char* sockpeername( int sd ) {

  struct sockaddr_in sckadr;
  socklen_t size_sckadr = sizeof(sckadr);

  if ( getpeername(sd, (struct sockaddr*)&sckadr, &size_sckadr) < 0 ) {
    perror("getpeername()");
    return 0;
  }

return inet_ntoa(sckadr.sin_addr);
}

// Nagle Algorithm tries to gather data into one packet
// It save bandwith, but introduces short delay
int socknagle( int sd, int set ) {

  if ( setsockopt(sd, IPPROTO_TCP, TCP_NODELAY, (void*)&set, sizeof(int)) < 0 ) {
    perror("setsockopt(NODELAY)");
    return -1;
  }

return 0;
}

int socktimeout( int sd, long timeout ) {

  struct timeval tv;

  tv.tv_sec = timeout;
  tv.tv_usec = 0L;

  if ( (setsockopt(sd, SOL_SOCKET, SO_RCVTIMEO, (void*)&tv, sizeof(tv))) < 0 ||
        (setsockopt(sd, SOL_SOCKET, SO_SNDTIMEO, (void*)&tv, sizeof(tv))) < 0 ) {
    return -1;
  }

return 0;
}

// returns number of bytes transferred from one socket
// to another or error number
int sockpipe( int sdread, int sdwrite ) {

  char buf[BUFSIZE];
  char *bseek = 0;
  int blen;
  int wlen;

  if ( (blen = sockread(sdread, buf, sizeof(buf))) < 1 ) return blen;

  for ( bseek = buf; bseek < buf+blen ; bseek += wlen ) {
    if ( (wlen = sockwrite(sdwrite, bseek, buf+blen-bseek)) < 1 )
      return wlen;
  }

return blen;
}

