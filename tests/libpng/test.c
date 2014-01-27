#include <stdio.h>

#include "libpng/png.h"


int main(int argc, char **argv) {
  png_uint_32 libpng_vn = png_access_version_number();
  printf("png_access_version_number(): %d\n", png_access_version_number());
  return 0;
}
