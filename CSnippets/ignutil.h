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
} PidMemoryView;

typedef struct {
    char command[STRING_SIZE];
    char filename[STRING_SIZE];
} Work;

// Declare the global variable
extern PidMemoryView *pid_table;

// Function prototypes
PidMemoryView *setup_shared_memory(void);
void cleanup_shared_memory(PidMemoryView *data);
void spawn_process(Work *new_process);
void monitor_children(PidMemoryView *pid_table);

#endif // IGNUTIL_H
