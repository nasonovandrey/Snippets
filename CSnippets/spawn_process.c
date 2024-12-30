void spawn_process(Work *candidate) {
    bool pid_set = false;
    for (int i = 0; ((i < MAX_PROCS) && (!pid_set)); ++i) {
        if (pid_table->pids[i] == 0) {
            pid_t pid = fork();
            if (pid == 0) { // Child process
                setup_signal_handling();
                atexit(cleanup_pid);

                execlp("sh", "sh", "-c", candidate->command, NULL);
                perror("Failed to execute command");
                exit(EXIT_FAILURE);
            } else if (pid > 0) { // Parent process
                printf("Started a new process with pid %d\n", pid);
                sem_wait(&pid_table->mutex);
                pid_table->pids[i] = pid;
                sem_post(&pid_table->mutex);
                pid_set = true;
            } else {
                perror("Failed to fork");
            }
        }
    }
    if (!pid_set) {
        printf("All available processes are busy, try again later\n");
    }
}

