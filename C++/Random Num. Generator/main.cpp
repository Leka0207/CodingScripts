#include <iostream>
#include <random>

int main()
{
    int lowerBound, upperBound;

    // Get the range of numbers from the user
    std::cout << "Enter the lower bound of the range: ";
    std::cin >> lowerBound;
    std::cout << "Enter the upper bound of the range: ";
    std::cin >> upperBound;

    if (upperBound < lowerBound) {
        std::cout << "Invalid range! The upper bound should be greater than or equal to the lower bound." << std::endl;
        return 1;
    }

    // Create a random device to seed the random number generator
    std::random_device rd;

    // Initialize the random number generator with the random device's seed
    std::mt19937 gen(rd());

    // Define the range of random numbers based on user input
    std::uniform_int_distribution<> distribution(lowerBound, upperBound);

    // Generate set number of random numbers within the user-specified range
    const int numRandomNumbers = 1;
    for (int i = 0; i < numRandomNumbers; ++i) {
        int randomNumber = distribution(gen);
        std::cout << randomNumber << " ";
    }

    std::cout << std::endl;

    return 0;
}




