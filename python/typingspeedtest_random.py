import time
import random

# List of sample sentences
sample_sentences = [
    "Python is an interpreted, high-level programming language.",
    "Artificial intelligence is transforming the world.",
    "The quick brown fox jumps over the lazy dog.",
    "Machine learning is a subset of artificial intelligence.",
    "OpenAI creates state-of-the-art AI models.",
    "Data science is a field that combines statistics and computer science.",
    "Deep learning uses neural networks for various applications.",
    "Software engineering involves the design and development of software.",
    "Natural language processing enables computers to understand human language.",
    "The future of technology is exciting and unpredictable."
]

border = '-+-' * 10

def createbox():
    print(border)
    print()
    print('Enter the phrase as fast as possible and with accuracy')
    print()

while True:
    # Select a random sentence from the list
    string = random.choice(sample_sentences)
    word_count = len(string.split())
    
    t0 = time.time()
    createbox()
    print(string, '\n')
    inputText = str(input())
    t1 = time.time()
    
    input_words = inputText.split()
    lengthOfInput = len(input_words)
    
    correct_words = len([word for word in input_words if word in string.split()])
    accuracy = correct_words / word_count
    timeTaken = t1 - t0
    wordsperminute = (lengthOfInput / timeTaken) * 60
    
    # Showing results now
    print('Total words \t :', lengthOfInput)
    print('Time used \t :', round(timeTaken, 2), 'seconds')
    print('Your accuracy \t :', round(accuracy * 100, 2), '%')
    print('Speed is \t :', round(wordsperminute, 2), 'words per minute')
    
    print("Do you want to retry? (yes/no): ", end='')
    retry = input().strip().lower()
    if retry != 'yes':
        print('Thank you, bye bye.')
        time.sleep(1.5)
        break
