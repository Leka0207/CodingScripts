def quiz_game():
    # List of questions and answers
    questions = [
        {
            "question": "What is the capital of France?",
            "choices": ["A) Berlin", "B) Madrid", "C) Paris", "D) Rome"],
            "answer": "C"
        },
        {
            "question": "What is the largest planet in our solar system?",
            "choices": ["A) Earth", "B) Jupiter", "C) Mars", "D) Saturn"],
            "answer": "B"
        },
        {
            "question": "Which element has the chemical symbol 'O'?",
            "choices": ["A) Oxygen", "B) Gold", "C) Silver", "D) Helium"],
            "answer": "A"
        },
        {
            "question": "What is the smallest prime number?",
            "choices": ["A) 0", "B) 1", "C) 2", "D) 3"],
            "answer": "C"
        },
        {
            "question": "Who wrote 'To Kill a Mockingbird'?",
            "choices": ["A) Harper Lee", "B) J.K. Rowling", "C) Jane Austen", "D) Mark Twain"],
            "answer": "A"
        }
    ]

    score = 0

    for q in questions:
        print(q["question"])
        for choice in q["choices"]:
            print(choice)
        
        answer = input("Enter your answer (A/B/C/D): ").upper()

        if answer == q["answer"]:
            print("Correct!\n")
            score += 1
        else:
            print(f"Wrong! The correct answer is {q['answer']}.\n")
    
    print(f"Your final score is: {score}/{len(questions)}")

if __name__ == "__main__":
    quiz_game()
