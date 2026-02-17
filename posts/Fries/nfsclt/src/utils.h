/*
 * 
 * Adrian Brzezinski (2018) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#ifndef __UTILS_H__
#define __UTILS_H__

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <math.h>

#include <sys/capability.h>
#include <sys/types.h>
#include <sys/stat.h>

// split path to file and directory part
// you need deallocate dir and path with free()
int pathsplit( char *path, char **dir, char **file );

char *stat_ftype( mode_t mode );

cap_flag_value_t cap_flag(pid_t pid, cap_value_t cap);

char *hrbytes(char *buf, unsigned int buflen, long long bytes);

#endif // __UTILS_H__
