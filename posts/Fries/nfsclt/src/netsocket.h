
/*
 * 
 * Adrian Brzezinski (2005) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#ifndef __NETSOCKET_H__
#define __NETSOCKET_H__

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>

#ifndef BUFSIZE
#define BUFSIZE 4096
#endif

int sockconnect( char *host, int port );
int sockconnectsrc( char *host, int port, char *srchost, int srcport ); // connect using specified source IP address or port

int sockbind( char *host, int port, int listnum );
int sockaccept( int sd );

int sockaddrsetup(
    struct sockaddr_in *addr, socklen_t addrlen,
    char *host, int port);

// how many bytes are pending in stream to read?
int sockpending( int sd );

int sockread( int sd, char *data, int data_len );
int sockwrite( int sd, char *data, int data_len );
int sockwritef( int sd, char *format, ... );

void sockclose( int sd );

int sockisconnected( int sd );  // is connection established?
int sockport( int sd );
int sockpeerport( int sd );
char* sockname( int sd );
char* sockpeername( int sd );

int socknagle( int sd, int set ); // enable or disable nagle algorithm
int socktimeout( int sd, long timeout ); // set read&write timeout in seconds

// copy data from sdread to sdwrite
int sockpipe( int sdread, int sdwrite );

#endif /* __NETSOCKET_H__ */
