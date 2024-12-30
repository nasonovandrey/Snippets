#include <stdio.h>

#define ARRSIZE 8
#define CONVERT (VAR, NEWVAR, TYPE)(TYPE)(NEWVAR) = ((TYPE))(VAR)

void capitalize(void *sym) { *sym = *sym - 32; }

void mutate(void *sym, int size, void (*funcPtr)(void *)) {
    for (int i = 0; i < size; ++i) {
        funcPtr(&sym[i]);
    }
}

int main() {
    char array[ARRSIZE] = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'};
    for (int i = 0; i < ARRSIZE; ++i) {
        printf("%c", array[i]);
    }
    mutate(array, ARRSIZE, capitalize);
    for (int i = 0; i < ARRSIZE; ++i) {
        printf("%c", array[i]);
    }

    return 0;
}
