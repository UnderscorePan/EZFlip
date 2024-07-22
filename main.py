import threading
import tkinter as tk
import os
import sqlite3
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from PIL import Image, ImageTk
import cv2
import ffmpeg
import tempfile
import pygame  # New import

# Initialize Pygame mixer
pygame.mixer.init()

# Initialize variables for threading
playing_video = False
current_video_path = ""
audio_thread = None
current_cards = []
card_index = 0

# Function to create database
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
                    video_path TEXT,
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
                    video_path TEXT,
                    FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)
                    )
    ''')

    cursor.execute('''
        INSERT INTO flashcards_new (id, set_id, word, definition, image_path, video_path)
        SELECT id, set_id, word, definition, image_path, NULL FROM flashcards
    ''')

    cursor.execute('DROP TABLE flashcards')
    cursor.execute('ALTER TABLE flashcards_new RENAME TO flashcards')

    cursor.execute('PRAGMA foreign_keys = ON;')
    conn.commit()

# Function to add new flashcards
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
def add_card(conn, set_id, word, definition, image_path=None, video_path=None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO flashcards (set_id, word, definition, image_path, video_path)
        VALUES(?, ?, ?, ?, ?)
    ''', (set_id, word, definition, image_path, video_path))
    card_id = cursor.lastrowid
    conn.commit()
    return card_id

# Function to retrieve all sets from database
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
        SELECT word, definition, image_path, video_path FROM flashcards
        WHERE set_id = ?
    ''', (set_id,))
    rows = cursor.fetchall()
    cards = [(row[0], row[1], row[2] if row[2] else '', row[3] if row[3] else '') for row in rows]
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
            video_path_var.set('')

def add_word():
    set_name = set_name_var.get()
    word = word_var.get()
    definition = definition_var.get()
    image_path = image_path_var.get() if image_path_var.get() else None
    video_path = video_path_var.get() if video_path_var.get() else None

    if set_name and word and definition:
        sets = get_sets(conn)
        if set_name not in sets:
            set_id = add_set(conn, set_name)
        else:
            set_id = sets[set_name]
        add_card(conn, set_id, word, definition, image_path, video_path)
        word_var.set('')
        definition_var.set('')
        image_path_var.set('')
        video_path_var.set('')
        populate_sets_combobox()
    else:
        messagebox.showerror("Error", "Please fill in all fields.")

def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn).keys())
    sets_combobox.set('')  # Clear the current selection

# Function to delete selected flashcard set
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
    global current_cards, card_index
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
        current_cards = []
        card_index = 0
        clear_flashcard_display()

def next_card():
    global card_index, current_cards
    if current_cards:
        card_index = min(card_index + 1, len(current_cards) - 1)
        show_card()

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
    video_canvas.delete("all")

def extract_audio(video_path):
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            audio_path = temp_audio_file.name
        ffmpeg.input(video_path).output(audio_path).run(overwrite_output=True)
    except FileNotFoundError:
        messagebox.showerror("Error", "FFmpeg not found. Please install FFmpeg and ensure it is in the PATH.")
        raise
    except PermissionError as e:
        messagebox.showerror("Error", f"Permission denied: {e}")
        raise
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract audio: {e}")
        raise
    return audio_path

def play_audio(video_path):
    try:
        audio_path = extract_audio(video_path)
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except PermissionError as e:
        messagebox.showerror("Error", f"Permission denied: {e}")
        raise
    except Exception as e:
        messagebox.showerror("Error", f"Failed to play audio: {e}")
        raise
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)  # Remove the temporary audio file after playing

playing_video = False  # Global flag to control video playback
audio_thread = None    # Global variable to store the audio thread

def play_video(video_path):
    global playing_video, audio_thread
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Start audio playback in a separate thread
    audio_thread = threading.Thread(target=play_audio, args=(video_path,))
    audio_thread.start()

    while cap.isOpened() and playing_video:
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (400, 300))
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            video_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            video_canvas.image = img
            video_canvas.update()
            cv2.waitKey(int(1000 / fps))
        else:
            break
    cap.release()

def start_video(video_path):
    global playing_video, current_video_path
    playing_video = True
    current_video_path = video_path
    threading.Thread(target=play_video, args=(video_path,)).start()

def stop_video():
    global playing_video
    playing_video = False
    if audio_thread is not None:
        audio_thread.join()
    video_canvas.delete("all")


def show_card():
    global card_index, current_cards

    if current_cards:
        if 0 <= card_index < len(current_cards):
            word, definition, image_path, video_path = current_cards[card_index]
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

            if video_path:
                start_video(video_path)
            else:
                stop_video()
        else:
            clear_flashcard_display()
    else:
        clear_flashcard_display()


# Function to flip the current card and display its definition
def flip_card():
    global card_index
    global current_cards

    if current_cards:
        word, definition, image_path, video_path = current_cards[card_index]
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
    filetypes = [('Video files', '*.mp4;*.avi;*.mkv')] if video else [('Image files', '*.png;*.jpg;*.jpeg;*.gif')]
    file_path = filedialog.askopenfilename(filetypes=filetypes)
    if file_path:
        absolute_path = os.path.abspath(file_path)
        path_var.set(absolute_path)

if __name__ == '__main__':
    # Connect to sqlite database
    conn = sqlite3.connect('ezflash.db')
    create_tables(conn)
    update_table_schema(conn)

    root = tk.Tk()
    root.title('EZFlip')
    root.geometry('500x700')

    style = Style(theme='solar')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Variables for storing inputs
    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()
    image_path_var = tk.StringVar()
    video_path_var = tk.StringVar()

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

    ttk.Label(create_set_frame, text='Video Path: ').pack(padx=5, pady=5)
    video_path_entry = ttk.Entry(create_set_frame, textvariable=video_path_var, width=30)
    video_path_entry.pack(padx=5, pady=5)
    ttk.Button(create_set_frame, text='Browse Video', command=lambda: browse_file(video_path_var, video=True)).pack(padx=5, pady=5)

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

    # Canvas to display video
    video_canvas = tk.Canvas(flashcards_frame, width=400, height=300)
    video_canvas.pack(padx=5, pady=10)

    # Flip button
    ttk.Button(flashcards_frame, text='Flip', command=flip_card).pack(side='left', padx=5, pady=5)

    # Next button
    ttk.Button(flashcards_frame, text='Next', command=next_card).pack(side='left', padx=5, pady=5)

    # Previous button
    ttk.Button(flashcards_frame, text='Previous', command=prev_card).pack(side='left', padx=5, pady=5)

    populate_sets_combobox()

    root.mainloop()
