#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#include "ignutil.h"

int main() {
    pid_table = setup_shared_memory();

    Work *work = (Work *)malloc(sizeof(Work));
    while (1) {
        printf("Enter a command (Ctrl+C to quit): ");

        if (fgets(work->command, sizeof(work->command),
                  stdin)) { // This is very stupid and non-extendable, please change
            work->command[strcspn(work->command, "\n")] = 0;
            spawn_process(work);
        }
    }

    cleanup_shared_memory(pid_table);

    return 0;
}
