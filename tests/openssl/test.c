#include <stdio.h>
#include <string.h>

#include "openssl/md5.h"


int main() {
    unsigned char digest[16];
    const char* string = "test";

    printf("string: %s (%lu)\n", string, strlen(string));

    MD5_CTX ctx;
    MD5_Init(&ctx);
    MD5_Update(&ctx, string, strlen(string));
    MD5_Final(digest, &ctx);

    char mdString[33];
    for (int i = 0; i < 16; i++)
        sprintf(&mdString[i*2], "%02x", (unsigned int)digest[i]);

    printf("md5 digest: %s\n", mdString);

    return 0;
}