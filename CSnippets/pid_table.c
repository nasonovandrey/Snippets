#include "headers/pid_table.h"

PidTable *pid_table;

PidTable *setup_pid_table() {
    int fd = shm_open("/myshm", O_CREAT | O_RDWR, 0666);
    ftruncate(fd, sizeof(PidTable));
    PidTable *data = mmap(NULL, sizeof(PidTable), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);

    // Initialize semaphore
    sem_init(&data->mutex, 1, 1);

    // Initialize PID array
    for (int i = 0; i < MAX_PROCS; i++) {
        data->pids[i] = 0;
    }

    return data;
}

void cleanup_shared_memory(PidTable *data) {
    sem_destroy(&data->mutex);
    munmap(data, sizeof(PidTable));
    shm_unlink("/myshm");
}

void cleanup_deactivated_pids() {
    pid_t pid = getpid();
    sem_wait(&pid_table->mutex);
    for (int i = 0; i < MAX_PROCS; i++) {
        if (pid_table->pids[i] == pid) {
            pid_table->pids[i] = 0;
            printf("Cleaned up pid %d\n", pid);
            break;
        }
    }
    sem_post(&pid_table->mutex);
}
