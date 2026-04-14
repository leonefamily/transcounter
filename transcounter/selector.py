import os
import sys
import importlib
import threading
import tkinter as tk
from tkinter import ttk
from transcounter.__init__ import __version__ as pver, __name__ as pname


def gui():
    root = tk.Tk()
    root.title(f"{pname}")
    root.geometry("300x150")

    # Create a Frame for the content
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    funcs = {}
    for script_id in ['counter', 'extrapolator', 'converter']:
        funcs[script_id] = getattr(
            importlib.import_module(f'{pname}.{script_id}'),
            'main'
        )
        btn = ttk.Button(
            main_frame, text=script_id, command=lambda s=script_id: funcs[s](args_list=[])
        )
        btn.pack(fill=tk.X, pady=5)

    root.mainloop()


if __name__ == '__main__':
    gui()
