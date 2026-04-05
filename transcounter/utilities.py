from pathlib import Path
from typing import Optional, Union

import pandas as pd
import tkinter as tk
from tkinter import ttk

APP_FOLDER = Path.home() / '.transclicker'
LAST_USED_FILE_PATH = APP_FOLDER / 'last_used_file.txt'
IMAGES_DIR = 'transcounter/images'

def initialize() -> Optional[Path]:
    APP_FOLDER.mkdir(parents=False, exist_ok=True)
    if LAST_USED_FILE_PATH.exists():
        with open(LAST_USED_FILE_PATH, 'r') as f:
            last_used_path = Path(f.read())
    else:
        last_used_path = None
    return last_used_path


def read_events(
        events_path: Union[str, Path]
) -> pd.DataFrame:
    p = Path(events_path)
    if p.suffix == '.csv':
        events_df = pd.read_csv(events_path, sep=';', decimal=',')
    elif p.suffix == '.json':
        events_df = pd.read_json(events_path, orient='records')
    else:
        raise ValueError(f'Wrong file type {p.suffix}')
    return events_df  # noqa


def write_events(
        events_df: pd.DataFrame,
        output_path: Union[str, Path]
):
    p = Path(output_path)
    if p.suffix == '.csv':
        events_df.to_csv(output_path, sep=';', decimal=',', index=False)
    elif p.suffix == '.json':
        events_df.to_json(output_path, orient='records', indent=4)
    else:
        raise ValueError(f'Wrong file type {p.suffix}')


class ErrorWindow:
    """A window that pops up if processing fails."""

    def __init__(
            self,
            error_message: str,
            root: tk.Tk
    ):
        self.root = tk.Toplevel(root)
        self.root.title("Processing error")
        self.root.geometry("500x300")
        self.root.resizable(True, True)

        self.root.transient(root)
        self.root.grab_set()

        # Frame for content
        content_frame = ttk.Frame(self.root)
        content_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        # Error Message
        msg_label = ttk.Label(
            content_frame,
            text=f"Error: {error_message}",
            font=('Arial', 12, 'bold'),
            foreground='red',
            wraplength=450
        )
        msg_label.pack(pady=5)

        detail_text = "An error occurred during processing. Please check your inputs and try again."
        detail_label = ttk.Label(content_frame, text=detail_text, wraplength=450)
        detail_label.pack(pady=5)

        # Close button
        close_btn = ttk.Button(content_frame, text="Close", command=self.root.destroy)
        close_btn.pack(pady=20)
