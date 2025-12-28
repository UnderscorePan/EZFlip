import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
from ttkbootstrap import Style

from ezflip.database import add_card, add_set, create_tables, get_cards, get_sets, update_table_schema
from ezflip.gesture import start_gesture_control
from ezflip.media import display_image, init_media_canvas, start_video, stop_video
from ezflip.tooltips import ToolTip


conn = None
current_cards = []
card_index = 0


def create_set():
    set_name = set_name_var.get()
    if set_name:
        if set_name not in get_sets(conn):
            add_set(conn, set_name)
            populate_sets_combobox()
            populate_sets_combobox_edit()
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
        populate_sets_combobox_edit()
    else:
        messagebox.showerror("Error", "Please fill in all fields.")


def populate_sets_combobox():
    sets_combobox['values'] = tuple(get_sets(conn).keys())
    sets_combobox.set('')


def populate_sets_combobox_edit():
    sets_combobox_edit['values'] = tuple(get_sets(conn).keys())
    sets_combobox_edit.set('')


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
    stop_video()
    if current_cards:
        clear_flashcard_display()
        card_index = min(card_index + 1, len(current_cards) - 1)
        show_card()


def prev_card():
    global card_index, current_cards
    stop_video()
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
                video_canvas.delete("all")

            stop_video()

            if video_path and notebook.tab(notebook.select(), "text") == 'Learning Mode ':
                start_video(video_path)
            else:
                print("No video path found or not in Learning Mode")

            character_label.config(image=unflipped_photo)
            character_label.image = unflipped_photo
        else:
            clear_flashcard_display()
    else:
        clear_flashcard_display()


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
        show_card()
    else:
        stop_video()


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
            video_path_var_edit.set('')
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
        flashcards_listbox.insert(tk.END, card[0])


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
    stop_video()
    root.destroy()


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


if __name__ == '__main__':
    conn = sqlite3.connect('ezflash.db')
    create_tables(conn)
    update_table_schema(conn)

    root = tk.Tk()
    root.title('EZFlip')
    root.geometry('550x750')

    style = Style(theme='solar')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    load_character_images()

    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()
    image_path_var = tk.StringVar()
    video_path_var = tk.StringVar()
    new_set_name_var = tk.StringVar()

    word_var_edit = tk.StringVar()
    definition_var_edit = tk.StringVar()
    image_path_var_edit = tk.StringVar()
    video_path_var_edit = tk.StringVar()

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    create_set_frame = ttk.Frame(notebook)
    notebook.add(create_set_frame, text='Create Set')

    ttk.Label(create_set_frame, text='Set Name: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Word(s): ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=word_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Answer: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=definition_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Image Path: ').pack(padx=5, pady=5)
    image_path_entry = ttk.Entry(create_set_frame, textvariable=image_path_var, width=30)
    image_path_entry.pack(padx=5, pady=5)
    ttk.Button(create_set_frame, text='Browse Image', command=lambda: browse_file(image_path_var)).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Video Path: ').pack(padx=5, pady=5)
    video_path_entry = ttk.Entry(create_set_frame, textvariable=video_path_var, width=30)
    video_path_entry.pack(padx=5, pady=5)
    ttk.Button(create_set_frame, text='Browse Video', command=lambda: browse_file(video_path_var, video=True)).pack(padx=5, pady=5)

    ttk.Button(create_set_frame, text='Add Word', command=add_word).pack(padx=5, pady=10)
    ttk.Button(create_set_frame, text='Save Set', command=create_set).pack(padx=5, pady=10)

    select_set_frame = ttk.Frame(notebook)
    notebook.add(select_set_frame, text='Select Set')

    sets_combobox = ttk.Combobox(select_set_frame, state='readonly')
    sets_combobox.pack(padx=5, pady=40)

    select_button = ttk.Button(select_set_frame, text='Select Set', command=select_set)
    select_button.pack(padx=5, pady=5)
    ToolTip(select_button, text="Proceed to learning mode after selection to begin.")
    ttk.Button(select_set_frame, text='Delete Set', command=delete_selected_set).pack(padx=5, pady=5)

    ttk.Label(select_set_frame, text=' Gesture control: ').pack(padx=5, pady=8)
    ttk.Label(select_set_frame, text='1 finger to go previous').pack(padx=5, pady=5)
    ttk.Label(select_set_frame, text='2 fingers to go next').pack(padx=5, pady=5)
    ttk.Label(select_set_frame, text='3 fingers to flip').pack(padx=5, pady=5)
    ttk.Label(select_set_frame, text='Press Q to turn it off').pack(padx=5, pady=5)

    edit_set_frame = ttk.Frame(notebook)
    notebook.add(edit_set_frame, text='Edit Set')

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

    center_frame = ttk.Frame(scrollable_frame)
    center_frame.grid(row=0, column=0, padx=100, pady=10)

    sets_combobox_edit = ttk.Combobox(center_frame, state='readonly')
    sets_combobox_edit.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

    select_button_edit = ttk.Button(center_frame, text='Select Set', command=select_set_for_edit)
    select_button_edit.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    ToolTip(select_button_edit, text="Select a set to edit.")

    flashcards_listbox = tk.Listbox(center_frame)
    flashcards_listbox.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky='ew')

    ttk.Button(center_frame, text='Delete Word', command=delete_word).grid(row=3, column=0, columnspan=2, padx=5, pady=10)

    ttk.Label(center_frame, text='Word(s): ').grid(row=4, column=0, padx=5, pady=5, sticky='e')
    ttk.Entry(center_frame, textvariable=word_var_edit, width=30).grid(row=4, column=1, padx=5, pady=5)

    ttk.Label(center_frame, text='Answer: ').grid(row=5, column=0, padx=5, pady=5, sticky='e')
    ttk.Entry(center_frame, textvariable=definition_var_edit, width=30).grid(row=5, column=1, padx=5, pady=5)

    ttk.Button(center_frame, text='Add Word', command=update_word).grid(row=6, column=1, padx=5, pady=5, sticky='w')

    ttk.Label(center_frame, text='Image Path: ').grid(row=7, column=0, padx=5, pady=5, sticky='e')
    image_path_entry_edit = ttk.Entry(center_frame, textvariable=image_path_var_edit, width=30)
    image_path_entry_edit.grid(row=7, column=1, padx=5, pady=5)
    ttk.Button(center_frame, text='Browse Image', command=lambda: browse_file(image_path_var_edit)).grid(row=8, column=1, padx=5, pady=5, sticky='w')

    ttk.Label(center_frame, text='Video Path: ').grid(row=9, column=0, padx=5, pady=5, sticky='e')
    video_path_entry_edit = ttk.Entry(center_frame, textvariable=video_path_var_edit, width=30)
    video_path_entry_edit.grid(row=9, column=1, padx=5, pady=5)
    ttk.Button(center_frame, text='Browse Video', command=lambda: browse_file(video_path_var_edit, video=True)).grid(row=10, column=1, padx=5, pady=5, sticky='w')

    ttk.Label(center_frame, text='New Set Name: ').grid(row=11, column=0, padx=5, pady=5, sticky='e')
    ttk.Entry(center_frame, textvariable=new_set_name_var, width=30).grid(row=11, column=1, padx=5, pady=5)
    ttk.Button(center_frame, text='Update Set Name', command=lambda: update_set_name(conn, get_sets(conn)[sets_combobox_edit.get()], new_set_name_var.get())).grid(row=12, column=1, padx=5, pady=5, sticky='w')

    populate_sets_combobox()
    populate_sets_combobox_edit()

    flashcards_frame = ttk.Frame(notebook)
    notebook.add(flashcards_frame, text='Learning Mode ')

    word_label = ttk.Label(flashcards_frame, text='', font=('TkDefaultFont', 24))
    word_label.pack(padx=5, pady=10)

    answer_label = ttk.Label(flashcards_frame, text='')
    answer_label.pack(padx=5, pady=10)

    image_label = ttk.Label(flashcards_frame)
    image_label.pack(pady=(5, 0), padx=5)

    video_canvas = tk.Canvas(flashcards_frame, width=400, height=300)
    video_canvas.pack(padx=5, pady=10)
    init_media_canvas(video_canvas)

    character_label = ttk.Label(flashcards_frame)
    character_label.pack(pady=(0, 10))

    flip_button = ttk.Button(flashcards_frame, text='Flip', command=flip_card)
    flip_button.pack(side='left', padx=5, pady=5)
    ToolTip(flip_button, text="Click to flip the card")

    ttk.Button(flashcards_frame, text='Next', command=next_card).pack(side='right', padx=5, pady=5)
    ttk.Button(flashcards_frame, text='Previous', command=prev_card).pack(side='right', padx=5, pady=5)

    gesture_thread = start_gesture_control(prev_card, next_card, flip_card)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
