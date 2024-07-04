import random

# List of simple yes/no questions
questions = [
    "Do you like pizza?",
    "Is it raining outside?",
    "Do you enjoy playing video games?",
    "Is the sky blue?",
    "Have you ever been to a concert?",
    "Do you like reading books?",
    "Is summer your favorite season?",
    "Do you have a pet?",
    "Have you ever traveled by plane?",
    "Do you like watching movies?"
]

# Function to generate a random yes/no answer
def generate_answer():
    return random.choice(["Yes", "No"])

# Function to ask questions and generate answers
def chat_with_bot():
    asked_questions = random.sample(questions, 10)  # Randomly select 10 questions
    for question in asked_questions:
        answer = generate_answer()
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        print()

# Start the chatbot
if __name__ == "__main__":
    chat_with_bot()
