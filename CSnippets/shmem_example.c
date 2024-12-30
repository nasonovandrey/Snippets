#include <errno.h>
#include <fcntl.h>
#include <semaphore.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int *setup_shared_memory() {
    int fd = shm_open("/myshm", O_CREAT | O_RDWR, 0666);
    ftruncate(fd, sizeof(int));
    int *data = mmap(NULL, sizeof(int), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);

    return data;
}

void cleanup_shared_memopy(int *data) {
    munmap(data, sizeof(int));
    shm_unlink("/myshm");
}

int main() {
    // int *shint = (int *)malloc(sizeof(int));
    int *shint = setup_shared_memory();
    *shint = 1;

    pid_t pid = fork();
    if (pid == 0) {
        *shint = 10;
    } else {
        sleep(5);
        printf("%d\n", *shint);
    }
    cleanup_shared_memopy(shint);
}
