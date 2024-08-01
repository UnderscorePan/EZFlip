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
import pygame
import time
import sys
import mediapipe as mp
import queue

class ToolTip:
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide_tip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.show_tip)

    def unschedule(self):
        self.id = None

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# Initialize Pygame mixer
pygame.mixer.init()

# Initialize variables for threading
audio_path = ''
playing_video = False
stopping_video = False
current_video_path = ""
audio_thread = None
video_thread = None
current_cards = []
card_index = 0
video_lock = threading.Lock()  # Lock for video threading

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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

    conn.commit()

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
        SELECT id, set_id, word, definition, image_path, video_path FROM flashcards
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
    print(f"Added card with video_path: {video_path}")  # Debug statement
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
    for card in cards:
        print(f"Retrieved card with video_path: {card[3]}")  # Debug statement
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

# Function to update the name of a flashcard set
def update_set_name(conn, set_id, new_name):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE flashcard_sets
        SET name = ?
        WHERE id = ?
    ''', (new_name, set_id))
    conn.commit()
    populate_sets_combobox()
    populate_sets_combobox_edit()

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
        video_path_var.set('')  # Ensure video_path is cleared after adding
        populate_sets_combobox()
    else:
        messagebox.showerror("Error", "Please fill in all fields.")

def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn).keys())
    sets_combobox.set('')  # Clear the current selection

def populate_sets_combobox_edit():
    sets_combobox_edit['values'] = tuple(get_sets(conn).keys())
    sets_combobox_edit.set('')  # Clear the current selection

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
    global card_index, current_cards, playing_video
    stop_video()  # Stop video before moving to next card
    if current_cards:
        clear_flashcard_display()
        card_index = min(card_index + 1, len(current_cards) - 1)
        show_card()

def prev_card():
    global card_index, current_cards, playing_video
    stop_video()  # Stop video before moving to previous card
    if current_cards:
        clear_flashcard_display()
        card_index = max(card_index - 1, 0)
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
        ffmpeg.input(video_path).output(audio_path, loglevel="quiet").run(overwrite_output=True)
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
    global audio_path
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

def stop_audio():
    global audio_path
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

def play_video(video_path):
    global playing_video, audio_thread, stopping_video

    def video_thread(frame_buffer):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_time = 1 / fps  # Time per frame in seconds

        audio_thread = threading.Thread(target=play_audio, args=(video_path,))
        audio_thread.start()
        start_time = time.time()

        while cap.isOpened() and playing_video:
            ret, frame = cap.read()

            if not ret:
                break

            current_time = time.time()
            elapsed_time = current_time - start_time
            expected_frame_number = int(elapsed_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, expected_frame_number)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (400, 300))

            if not frame_buffer.full():
                frame_buffer.put(frame)

        cap.release()
        stop_audio()

    def display_thread(frame_buffer, frame_time):
        while playing_video:
            if not frame_buffer.empty():
                frame = frame_buffer.get()
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                video_canvas.create_image(0, 0, anchor=tk.NW, image=img)
                video_canvas.image = img
                video_canvas.update()
            time.sleep(frame_time)

    frame_buffer = queue.Queue(maxsize=10)  # Buffer to store frames
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_time = 1 / fps  # Time per frame in seconds
    cap.release()

    video_play_thread = threading.Thread(target=video_thread, args=(frame_buffer,))
    video_display_thread = threading.Thread(target=display_thread, args=(frame_buffer, frame_time))

    video_play_thread.daemon = True  # Set as daemon so it doesn't block exit
    video_display_thread.daemon = True  # Set as daemon so it doesn't block exit

    video_play_thread.start()
    video_display_thread.start()

def stop_video():
    global playing_video, video_thread, stopping_video
    playing_video = False
    if video_thread:
        video_thread.join()
    stop_audio()

def start_video(video_path):
    global playing_video, current_video_path
    playing_video = True
    current_video_path = video_path
    threading.Thread(target=play_video, args=(video_path,)).start()

def show_card():
    global card_index, current_cards

    if current_cards:
        if 0 <= card_index < len(current_cards):
            word, definition, image_path, video_path = current_cards[card_index]
            word_label.config(text=word)
            answer_label.config(text='')

            if image_path:
                display_image(image_path)
            else:
                video_canvas.delete("all")  # Ensure the canvas is cleared if no image

            stop_video()  # Stop the previous video before starting a new one

            if video_path and notebook.tab(notebook.select(), "text") == 'Learning Mode ':
                start_video(video_path)
            else:
                print("No video path found or not in Learning Mode")  # Debug statement

            character_label.config(image=unflipped_photo)
            character_label.image = unflipped_photo
        else:
            clear_flashcard_display()
    else:
        clear_flashcard_display()

def display_image(image_path):
    try:
        image = Image.open(image_path)
        image = image.resize((400, 300), Image.LANCZOS)  # Resize to 400x300
        photo = ImageTk.PhotoImage(image)
        video_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        video_canvas.image = photo
        video_canvas.update()
    except Exception as e:
        video_canvas.delete("all")
        video_canvas.create_text(200, 150, text='Error loading image', fill='red', font=('TkDefaultFont', 24))


# Function to flip the current card and display its definition
def flip_card():
    global card_index
    global current_cards

    if current_cards:
        word, definition, image_path, video_path = current_cards[card_index]
        answer_label.config(text=definition)
        character_label.config(image=flipped_photo)
        character_label.image = flipped_photo

def on_tab_changed(event):
    selected_tab = event.widget.select()
    tab_text = event.widget.tab(selected_tab, "text")
    if tab_text == 'Learning Mode ' and current_cards:
        show_card()  # Show the card to start video immediately
    else:
        stop_video()  # Stop video when switching out of learning mode

def update_word():
    set_name = sets_combobox_edit.get()
    word = word_var_edit.get()
    definition = definition_var_edit.get()
    image_path = image_path_var_edit.get() if image_path_var_edit.get() else None
    video_path = video_path_var_edit.get() if video_path_var_edit.get() else None

    if set_name and word and definition:
        sets = get_sets(conn)
        if set_name in sets:
            set_id = sets[set_name]
            add_card(conn, set_id, word, definition, image_path, video_path)
            word_var_edit.set('')
            definition_var_edit.set('')
            image_path_var_edit.set('')
            video_path_var_edit.set('')  # Ensure video_path is cleared after adding
            populate_flashcards_listbox(set_id)
        else:
            messagebox.showerror("Error", "Set not found.")
    else:
        messagebox.showerror("Error", "Please fill in all fields.")

def delete_word():
    selected_word = flashcards_listbox.get(tk.ACTIVE)
    if selected_word:
        set_name = sets_combobox_edit.get()
        sets = get_sets(conn)
        set_id = sets[set_name]
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM flashcards
            WHERE set_id = ? AND word = ?
        ''', (set_id, selected_word))
        conn.commit()
        populate_flashcards_listbox(set_id)

def populate_flashcards_listbox(set_id):
    flashcards_listbox.delete(0, tk.END)
    cards = get_cards(conn, set_id)
    for card in cards:
        flashcards_listbox.insert(tk.END, card[0])  # Display word in the listbox

def select_set_for_edit():
    set_name = sets_combobox_edit.get()
    if set_name:
        set_id = get_sets(conn)[set_name]
        populate_flashcards_listbox(set_id)

def browse_file(path_var, video=False):
    filetypes = [('Video files', '*.mp4;*.avi;*.mkv')] if video else [('Image files', '*.png;*.jpg;*.jpeg;*.gif')]
    file_path = filedialog.askopenfilename(filetypes=filetypes)
    if file_path:
        absolute_path = os.path.abspath(file_path)
        path_var.set(absolute_path)

def on_closing():
    stop_video()  # Ensure video stops when program closes
    root.destroy()

# Initialize Mediapipe hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Initialize state
previous_finger_count = 0

def count_fingers(hand_landmarks):
    finger_tips = [mp_hands.HandLandmark.INDEX_FINGER_TIP,
                   mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                   mp_hands.HandLandmark.RING_FINGER_TIP,
                   mp_hands.HandLandmark.PINKY_TIP]

    count = 0
    for tip in finger_tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1
    return count

def gesture_control():
    global previous_finger_count
    cap = cv2.VideoCapture(0)

    gesture_active = False  # Variable to track if a gesture is currently active
    last_gesture_time = time.time()  # Track the last time a gesture was recognized
    cooldown_period = 2.0  # Cooldown period in seconds

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        current_finger_count = 0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                current_finger_count = count_fingers(hand_landmarks)

                # Only register a new gesture if no fingers are currently lifted and cooldown has passed
                if not gesture_active and (time.time() - last_gesture_time > cooldown_period):
                    if current_finger_count == 1:
                        prev_card()  # One finger lifted
                        gesture_active = True  # Set gesture active
                        last_gesture_time = time.time()  # Update last gesture time
                    elif current_finger_count == 2:
                        next_card()  # Two fingers lifted
                        gesture_active = True  # Set gesture active
                        last_gesture_time = time.time()  # Update last gesture time
                    elif current_finger_count == 3:
                        flip_card()  # Three fingers lifted
                        gesture_active = True  # Set gesture active
                        last_gesture_time = time.time()  # Update last gesture time

                # Update gesture active state
                if current_finger_count == 0:
                    gesture_active = False  # Reset when no fingers are lifted

                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        else:
            gesture_active = False  # Reset when no hand is detected

        cv2.imshow('Gesture Control', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Start the gesture control in a separate thread
gesture_thread = threading.Thread(target=gesture_control)
gesture_thread.start()

if __name__ == '__main__':
    # Connect to sqlite database
    conn = sqlite3.connect('ezflash.db')
    create_tables(conn)
    update_table_schema(conn)

    root = tk.Tk()
    root.title('EZFlip')
    root.geometry('550x750')

    style = Style(theme='solar')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Load character images after creating the Tkinter root window
    def load_character_images():
        global flipped_photo, unflipped_photo

        flipped_image_path = "Sam_Walfie.png"
        unflipped_image_path = "Sam_Walfie_unflipped.png"

        flipped_image = Image.open(flipped_image_path)
        flipped_image = flipped_image.resize((150, 150), Image.LANCZOS)
        flipped_photo = ImageTk.PhotoImage(flipped_image)

        unflipped_image = Image.open(unflipped_image_path)
        unflipped_image = unflipped_image.resize((150, 150), Image.LANCZOS)
        unflipped_photo = ImageTk.PhotoImage(unflipped_image)

    load_character_images()

    # Variables for storing inputs
    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()
    image_path_var = tk.StringVar()
    video_path_var = tk.StringVar()
    new_set_name_var = tk.StringVar()  # Variable to store the new set name

    # Initialize variables for storing inputs in the edit set page
    word_var_edit = tk.StringVar()
    definition_var_edit = tk.StringVar()
    image_path_var_edit = tk.StringVar()
    video_path_var_edit = tk.StringVar()

    # Notebook widget
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Bind the tab change event
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # Create set frame
    create_set_frame = ttk.Frame(notebook)
    notebook.add(create_set_frame, text='Create Set')

    # Label and entry widget for inputs of word and answer
    ttk.Label(create_set_frame, text='Set Name: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Word(s): ').pack(padx=5, pady=5)
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
    select_button = ttk.Button(select_set_frame, text='Select Set', command=select_set)
    select_button.pack(padx=5, pady=5)
    ToolTip(select_button, text="Proceed to learning mode after selection to begin.")
    ttk.Button(select_set_frame, text='Delete Set', command=delete_selected_set).pack(padx=5, pady=5)

    # Label for instructions
    ttk.Label(select_set_frame, text=' Gesture control: ').pack(padx=5, pady=8)
    ttk.Label(select_set_frame, text='1 finger to go previous').pack(padx=5, pady=5)
    ttk.Label(select_set_frame, text='2 fingers to go next').pack(padx=5, pady=5)
    ttk.Label(select_set_frame, text='3 fingers to flip').pack(padx=5, pady=5)
    ttk.Label(select_set_frame, text='Press Q to turn it off').pack(padx=5,pady=5)

    # Edit set page
    edit_set_frame = ttk.Frame(notebook)
    notebook.add(edit_set_frame, text='Edit Set')

    # Create Canvas and Scrollbar in the Edit Set frame
    canvas = tk.Canvas(edit_set_frame)
    scrollbar = ttk.Scrollbar(edit_set_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Center the content using a nested frame
    center_frame = ttk.Frame(scrollable_frame)
    center_frame.grid(row=0, column=0, padx=100, pady=10)

    # Combobox widget for selecting set to edit
    sets_combobox_edit = ttk.Combobox(center_frame, state='readonly')
    sets_combobox_edit.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

    # Button to select set for editing
    select_button_edit = ttk.Button(center_frame, text='Select Set', command=select_set_for_edit)
    select_button_edit.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    ToolTip(select_button_edit, text="Select a set to edit.")

    # Listbox to display flashcards
    flashcards_listbox = tk.Listbox(center_frame)
    flashcards_listbox.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

    # Button to delete selected word
    ttk.Button(center_frame, text='Delete Word', command=delete_word).grid(row=3, column=0, columnspan=2, padx=5, pady=10)

    # Entry widgets for adding new flashcards
    ttk.Label(center_frame, text='Word(s): ').grid(row=4, column=0, padx=5, pady=5, sticky='e')
    ttk.Entry(center_frame, textvariable=word_var_edit, width=30).grid(row=4, column=1, padx=5, pady=5)

    ttk.Label(center_frame, text='Answer: ').grid(row=5, column=0, padx=5, pady=5, sticky='e')
    ttk.Entry(center_frame, textvariable=definition_var_edit, width=30).grid(row=5, column=1, padx=5, pady=5)

    # Button to add new word
    ttk.Button(center_frame, text='Add Word', command=update_word).grid(row=6, column=1, padx=5, pady=5, sticky='w')

    ttk.Label(center_frame, text='Image Path: ').grid(row=7, column=0, padx=5, pady=5, sticky='e')
    image_path_entry_edit = ttk.Entry(center_frame, textvariable=image_path_var_edit, width=30)
    image_path_entry_edit.grid(row=7, column=1, padx=5, pady=5)
    ttk.Button(center_frame, text='Browse Image', command=lambda: browse_file(image_path_var_edit)).grid(row=8, column=1, padx=5, pady=5, sticky='w')

    ttk.Label(center_frame, text='Video Path: ').grid(row=9, column=0, padx=5, pady=5, sticky='e')
    video_path_entry_edit = ttk.Entry(center_frame, textvariable=video_path_var_edit, width=30)
    video_path_entry_edit.grid(row=9, column=1, padx=5, pady=5)
    ttk.Button(center_frame, text='Browse Video', command=lambda: browse_file(video_path_var_edit, video=True)).grid(row=10, column=1, padx=5, pady=5, sticky='w')

    # Add widgets to update set name
    ttk.Label(center_frame, text='New Set Name: ').grid(row=11, column=0, padx=5, pady=5, sticky='e')
    ttk.Entry(center_frame, textvariable=new_set_name_var, width=30).grid(row=11, column=1, padx=5, pady=5)
    ttk.Button(center_frame, text='Update Set Name', command=lambda: update_set_name(conn, get_sets(conn)[sets_combobox_edit.get()], new_set_name_var.get())).grid(row=12, column=1, padx=5, pady=5, sticky='w')

    # Populate comboboxes with sets
    populate_sets_combobox()
    populate_sets_combobox_edit()

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
    image_label.pack(pady=(5, 0), padx=5)  # Adjust the padding to reduce vertical space

    # Canvas to display video
    video_canvas = tk.Canvas(flashcards_frame, width=400, height=300)
    video_canvas.pack(padx=5, pady=10)

    # Character image label
    character_label = ttk.Label(flashcards_frame)
    character_label.pack(pady=(0, 10))

    # Flip button
    flip_button = ttk.Button(flashcards_frame, text='Flip', command=flip_card)
    flip_button.pack(side='left', padx=5, pady=5)
    ToolTip(flip_button, text="Click to flip the card")

    # Next button
    ttk.Button(flashcards_frame, text='Next', command=next_card).pack(side='right', padx=5, pady=5)

    # Previous button
    ttk.Button(flashcards_frame, text='Previous', command=prev_card).pack(side='right', padx=5, pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
