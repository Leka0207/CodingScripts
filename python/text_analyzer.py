import sys
import nltk
from nltk.corpus import stopwords
from gensim.summarization import summarize

def load_text_from_file(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def preprocess_text(text):
    # Tokenize the text
    words = nltk.word_tokenize(text)

    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalnum() and word not in stop_words]

    return words

def generate_summary(text, ratio=0.1):
    summary = summarize(text, ratio=ratio)
    return summary

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python text_analyzer.py [text|file_path]")
        sys.exit(1)

    input_type = sys.argv[1]

    if input_type == "text":
        text = input("Enter the text: ")
    elif input_type == "file":
        if len(sys.argv) != 3:
            print("Usage: python text_analyzer.py file_path")
            sys.exit(1)

        file_path = sys.argv[2]
        text = load_text_from_file(file_path)
    else:
        print("Invalid input type. Use 'text' or 'file'.")
        sys.exit(1)

    # Preprocess the text
    words = preprocess_text(text)

    # Generate the summary
    summary = generate_summary(' '.join(words))
    print("\nSummary:\n")
    print(summary)