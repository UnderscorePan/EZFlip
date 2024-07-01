import csv
from tkinter import messagebox
## test comment
def save_flashcard(question, answer, flashcards, filename="flashcards.csv"):
    # Add flashcard to the list
    flashcards.append((question, answer))

    # Save to CSV file
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([question, answer])

    messagebox.showinfo("Saved", f"Flashcard Saved!\nQuestion: {question}\nAnswer: {answer}")

def load_flashcards(filename="flashcards.csv"):
    flashcards = []
    try:
        with open(filename, mode='r') as file:
            reader = csv.reader(file)
            flashcards = [(row[0], row[1]) for row in reader]
    except FileNotFoundError:
        pass  # If file does not exist, return an empty list
    return flashcards
