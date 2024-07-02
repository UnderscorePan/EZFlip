import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style

if __name__ == '__main__':
    root = tk.Tk()
    root.title('EZFlip')

    style = Style(theme='solar')
    style.configure('TLabel', font=('TkDefaultFont', 18))
    style.configure('TButton', font=('TkDefaultFont', 16))

    # Variable for storing inputs
    set_name_var = tk.StringVar()
    word_var = tk.StringVar()
    definition_var = tk.StringVar()

    # Create set lol
    create_set_frame = ttk.Frame(notebook)


    root.mainloop()