import tkinter as tk
import os
import sqlite3
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from PIL import Image, ImageTk
import threading

# function to create database
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_sets(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                    )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    image_path TEXT,
                    FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)
                    )
    ''')

def update_table_schema(conn):
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = OFF;')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards_new(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    image_path TEXT,
                    FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)
                    )
    ''')

    cursor.execute('''
        INSERT INTO flashcards_new (id, set_id, word, definition, image_path)
        SELECT id, set_id, word, definition, image_path FROM flashcards
    ''')

    cursor.execute('DROP TABLE flashcards')
    cursor.execute('ALTER TABLE flashcards_new RENAME TO flashcards')

    cursor.execute('PRAGMA foreign_keys = ON;')
    conn.commit()

# function to add new flashcards
def add_set(conn, name):
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO flashcard_sets (name)
        VALUES(?)
    ''', (name,))

    set_id = cursor.lastrowid
    conn.commit()

    return set_id

# Function to add flashcard to database
def add_card(conn, set_id, word, definition, image_path=None):
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO flashcards (set_id, word, definition, image_path)
        VALUES(?, ?, ?, ?)
    ''', (set_id, word, definition, image_path))

    card_id = cursor.lastrowid
    conn.commit()

    return card_id

# function to retrieve all card from database
def get_sets(conn):
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name FROM flashcard_sets
    ''')

    rows = cursor.fetchall()
    sets = {row[1]: row[0] for row in rows}

    return sets

# Function to get all flashcards of a specific set
def get_cards(conn, set_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT word, definition, image_path FROM flashcards
        WHERE set_id = ?
    ''', (set_id,))
    rows = cursor.fetchall()
    cards = [(row[0], row[1], row[2] if row[2] else '') for row in rows]
    return cards

# Function to delete set from database
def delete_set(conn, set_id):
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM flashcard_sets
        WHERE id = ?
    ''', (set_id,))

    conn.commit()
    sets_combobox.set('')
    clear_flashcard_display()
    populate_sets_combobox()

    global current_cards, card_index
    current_cards = []
    card_index = 0

# Function to create new set
def create_set():
    set_name = set_name_var.get()
    if set_name:
        if set_name not in get_sets(conn):
            set_id = add_set(conn, set_name)
            populate_sets_combobox()
            set_name_var.set('')

            # Clear input fields
            set_name_var.set('')
            word_var.set('')
            definition_var.set('')
            image_path_var.set('')

def add_word():
    set_name = set_name_var.get()
    word = word_var.get()
    definition = definition_var.get()
    image_path = image_path_var.get() if image_path_var.get() else None

    if set_name and word and definition:
        if set_name not in get_sets(conn):
            set_id = add_set(conn, set_name)
        else:
            set_id = get_sets(conn)[set_name]

        add_card(conn, set_id, word, definition, image_path)

        word_var.set('')
        definition_var.set('')
        image_path_var.set('')

        populate_sets_combobox()

def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn).keys())

# function to delete selected flashcard set
def delete_selected_set():
    set_name = sets_combobox.get()

    if set_name:
        result = messagebox.askyesno(
            'Confirmation', f'Are you sure you want to delete the "{set_name}" set?'
        )

        if result == tk.YES:
            set_id = get_sets(conn)[set_name]
            delete_set(conn, set_id)
            populate_sets_combobox()
            clear_flashcard_display()

def select_set():
    set_name = sets_combobox.get()

    if set_name:
        set_id = get_sets(conn)[set_name]
        cards = get_cards(conn, set_id)

        if cards:
            display_flashcards(cards)
        else:
            word_label.config(text="No cards in this set")
            answer_label.config(text='')
    else:
        global current_cards, card_index
        current_cards = []
        card_index = 0
        clear_flashcard_display()

def display_flashcards(cards):
    global card_index
    global current_cards

    card_index = 0
    current_cards = cards

    if not cards:
        clear_flashcard_display()
    else:
        show_card()

def clear_flashcard_display():
    word_label.config(text='')
    answer_label.config(text='')
    image_label.config(image='')
    image_label.image = None

def show_card():
    global card_index
    global current_cards

    if current_cards:
        if 0 <= card_index < len(current_cards):
            word, definition, image_path = current_cards[card_index]
            word_label.config(text=word)
            answer_label.config(text='')

            if image_path:
                try:
                    image = Image.open(image_path)
                    image = image.resize((200, 200), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    image_label.config(image=photo)
                    image_label.image = photo
                except Exception as e:
                    image_label.config(text='Error loading image')
            else:
                image_label.config(image='')
                image_label.image = None
        else:
            clear_flashcard_display()
    else:
        clear_flashcard_display()

# Function to flip the current card and display its definition
def flip_card():
    global card_index
    global current_cards

    if current_cards:
        word, definition, image_path = current_cards[card_index]
        answer_label.config(text=definition)

# Function to move to the next card
def next_card():
    global card_index
    global current_cards

    if current_cards:
        card_index = min(card_index + 1, len(current_cards) - 1)
        show_card()

# Function to move to the previous card
def prev_card():
    global card_index
    global current_cards

    if current_cards:
        card_index = max(card_index - 1, 0)
        show_card()

def browse_file(path_var, video=False):
    filetypes = [('Image files', '*.png;*.jpg;*.jpeg;*.gif')]
    file_path = filedialog.askopenfilename(filetypes=filetypes)
    if file_path:
        absolute_path = os.path.abspath(file_path)
        path_var.set(absolute_path)

if __name__ == '__main__':
    # connect to sqlite database
    conn = sqlite3.connect('ezflash.db')
    create_tables(conn)
    update_table_schema(conn)

    root = tk.Tk()
    root.title('EZFlip')
    root.geometry('500x700')

    style = Style(theme='solar')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Variable for storing inputs
    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()
    image_path_var = tk.StringVar()

    # Notebook widget
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Create set frame
    create_set_frame = ttk.Frame(notebook)
    notebook.add(create_set_frame, text='Create Set')

    # Label and entry widget for inputs of word and answer
    ttk.Label(create_set_frame, text='Set Name: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Word: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=word_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Answer: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=definition_var, width=30).pack(padx=5, pady=5)

    # Add widgets to input image paths
    ttk.Label(create_set_frame, text='Image Path: ').pack(padx=5, pady=5)
    image_path_entry = ttk.Entry(create_set_frame, textvariable=image_path_var, width=30)
    image_path_entry.pack(padx=5, pady=5)
    ttk.Button(create_set_frame, text='Browse Image', command=lambda: browse_file(image_path_var)).pack(padx=5, pady=5)

    # Button to add to the set
    ttk.Button(create_set_frame, text='Add Word', command=add_word).pack(padx=5, pady=10)

    # Button for saving the set
    ttk.Button(create_set_frame, text='Save Set', command=create_set).pack(padx=5, pady=10)

    # Select set page
    select_set_frame = ttk.Frame(notebook)
    notebook.add(select_set_frame, text='Select Set')

    # Combobox widget for selecting set
    sets_combobox = ttk.Combobox(select_set_frame, state='readonly')
    sets_combobox.pack(padx=5, pady=40)

    # Delete and add button
    ttk.Button(select_set_frame, text='Select Set', command=select_set).pack(padx=5, pady=5)
    ttk.Button(select_set_frame, text='Delete Set', command=delete_selected_set).pack(padx=5, pady=5)

    # Learn mode tab
    flashcards_frame = ttk.Frame(notebook)
    notebook.add(flashcards_frame, text='Learning Mode ')

    # Initialize variable for tracking card index
    card_index = 0
    current_tabs = []

    # Label to display word on card
    word_label = ttk.Label(flashcards_frame, text='', font=('TkDefaultFont', 24))
    word_label.pack(padx=5, pady=10)

    # Label to display answer
    answer_label = ttk.Label(flashcards_frame, text='')
    answer_label.pack(padx=5, pady=10)

    # Label to display image
    image_label = ttk.Label(flashcards_frame)
    image_label.pack(padx=5, pady=10)

    # Flip button
    ttk.Button(flashcards_frame, text='Flip', command=flip_card).pack(side='left', padx=5, pady=5)

    # Next button
    ttk.Button(flashcards_frame, text='Next', command=next_card).pack(side='left', padx=5, pady=5)

    # Previous button
    ttk.Button(flashcards_frame, text='Previous', command=prev_card).pack(side='left', padx=5, pady=5)

    populate_sets_combobox()

    root.mainloop()
