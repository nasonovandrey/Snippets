#ifndef IGNUTIL_H
#define IGNUTIL_H

#include <errno.h>
#include <fcntl.h>
#include <semaphore.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAX_PROCS 4
#define STRING_SIZE 1024
#define POLL_INTERVAL 1

// Define structures
typedef struct {
    pid_t pids[MAX_PROCS];
    sem_t mutex;
} PidTable;

// Declare the global variable
extern PidTable *pid_table;

// Function prototypes
PidTable *setup_shared_memory(void);
void cleanup_shared_memory(PidTable *data);
void cleanup_deactivated_pids();

#endif // IGNUTIL_H
