import tkinter as tk
from flashcard_functions import save_flashcard, load_flashcards

def create_flashcard_inputs(root, flashcards):
    # Create input fields and save button directly in the main window
    question_label = tk.Label(root, text="Question:")
    question_label.pack(pady=5)

    question_entry = tk.Entry(root)
    question_entry.pack(pady=5)

    answer_label = tk.Label(root, text="Answer:")
    answer_label.pack(pady=5)

    answer_entry = tk.Entry(root)
    answer_entry.pack(pady=5)

    save_button = tk.Button(root, text="Save", command=lambda: save_flashcard(question_entry.get(), answer_entry.get(), flashcards))
    save_button.pack(pady=10)

root = tk.Tk()
root.geometry("500x450")
root.title("EZFlash")

flashcards = load_flashcards()  # Load existing flashcards

menu = tk.Menu(root)
file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label='File', menu=file_menu)
root.configure(menu=menu)

# Main button to create flashcard inputs
main_button = tk.Button(root, text="Add New Flashcard", command=lambda: create_flashcard_inputs(root, flashcards))
main_button.pack(pady=20)

root.mainloop()
