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


    root.mainloop()