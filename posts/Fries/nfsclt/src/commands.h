/*
 * 
 * Adrian Brzezinski (2018) <adrbxx at gmail.com>
 * License: GPLv2+
 *
 */

#ifndef __COMMANDS_H__
#define __COMMANDS_H__

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <sys/stat.h>

#include "nfsclt.h"

typedef int (tf_command) ( int, char** );

typedef struct {
  tf_command *cmd;      // Function to call to do the job
  char *name;           // User printable name of the function
  char *desc;           // Short description for this function
} t_command;

int cmd_quit( int argc, char **argv);   // exported for main()

// defined at the end of commands.c file
extern t_nfsclt nfsclt;
extern t_command commands[];

#endif // __COMMANDS_H__
