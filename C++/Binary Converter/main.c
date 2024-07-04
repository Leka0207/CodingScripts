#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int main()
{
    int b1, b2, b3, b4, v1, v2, v3, v4;
    int d1;

    printf("\nPlease input b1: ");
    scanf("%d", &b1);

    printf("\nPlease input b2: ");
    scanf("%d", &b2);

    printf("\nPlease input b3: ");
    scanf("%d", &b3);

    printf("\nPlease input b4: ");
    scanf("%d", &b4);

    v1 = b1 * 8;
    v2 = b2 * 4;
    v3 = b3 * 2;
    v4 = b4 * 1;
    d1 = v1 + v2 + v3 + v4;

    printf("\nThe decimal value of the binary number is: %d", d1);
    printf("\n");

    return 0;
}
