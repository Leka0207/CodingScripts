#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main()
{
    // Seed the random number generator with the current time
    srand(time(NULL));

    int lowerBound, upperBound;

    // Get the range of numbers from the user
    printf("Enter the lower bound of the range: ");
    scanf("%d", &lowerBound);
    printf("\nEnter the upper bound of the range: ");
    scanf("%d", &upperBound);

    if (upperBound < lowerBound)
    {
        printf("\nINVALID RANGE! The upper bound should be greater than or equal to the lower bound.\n");
        return 1;
    }

    // Generate 5 random numbers within the user-specified range
    const int numRandomNumbers = 5;

    printf("\nThe generated values are shown below:");

    for (int i = 0; i < numRandomNumbers; ++i)
    {
        int randomNumber = (rand() % (upperBound - lowerBound + 1)) + lowerBound;
        printf("\n%d", randomNumber);
    }

    printf("\n");
    return 0;
}
