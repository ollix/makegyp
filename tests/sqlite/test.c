#include <stdio.h>

#include "sqlite3.h"


int main(int argc, char **argv) {
  printf("sqlite3_libversion(): %s\n", sqlite3_libversion());
  return 0;
}
