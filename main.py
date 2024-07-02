import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style

if __name__ == '__main__':
    root = tk.Tk()
    root.title('EZFlip')
    root.geometry('500x400')

    style = Style(theme='solar')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Variable for storing inputs
    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()

    # Notebook widget
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    # Create set lol
    create_set_frame = ttk.Frame(notebook)
    notebook.add(create_set_frame, text='Create Set')

    # Label and entry widget for inputs of word and answer
    ttk.Label(create_set_frame, text='Set Name: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Word: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    ttk.Label(create_set_frame, text='Answer: ').pack(padx=5, pady=5)
    ttk.Entry(create_set_frame, textvariable=set_name_var, width=30).pack(padx=5, pady=5)

    # Button to add to the set
    ttk.Button(create_set_frame, text='Add Word').pack(padx=5, pady=10)

    # Button for saving the set
    ttk.Button(create_set_frame, text='Save Set').pack(padx=5, pady=10)

    # select set page
    select_set_frame = ttk.Frame(notebook)
    notebook.add(select_set_frame, text='Select Set')

    # combobox widget for selecting set
    sets_combobox = ttk.Combobox(select_set_frame, state='readonly')
    sets_combobox.pack(padx=5, pady=5)

    # del and add button
    ttk.Button(select_set_frame, text='Select Set')
    ttk.Button(select_set_frame, text='Delete Set')

    # learn mode tab
    flashcards_frame = ttk.Frame(notebook)
    notebook.add(flashcards_frame, text='Learning Mode ')

    # initialize variable for tracking card index
    card_index = 0
    current_tabs = []

    # label to display word on card
    word_label = ttk.Label(flashcards_frame, text='', font= ('TkDefaultFont', 24))
    word_label.pack(padx=5, pady=40)

    # label to display answer
    word_label = ttk.Label(flashcards_frame, text='', font= ('TkDefaultFont', 24))
    word_label.pack(padx=5, pady=40)

    # button for flip and next flashcards
    ttk.Button(flashcards_frame, text='Flip').pack(side='left', padx=5, pady=5)
    root.mainloop()