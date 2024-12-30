
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

int main() {
    pid_t pid = 27085;
    while (1) {
        printf("Polling process");
        if (waitpid(pid, NULL, WNOHANG) > 0) {
            printf("Process finished");
        }
        sleep(5);
    }
}
