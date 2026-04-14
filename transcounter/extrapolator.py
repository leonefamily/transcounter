import argparse
import json
import sys

import numpy as np
from pathlib import Path
from typing import Optional, Union, Dict, Any, List

import pandas as pd
from transcounter.utilities import initialize, read_events, APP_FOLDER, ErrorWindow, write_events

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

CONFIG_FILE = APP_FOLDER / 'extrapolator.json'

class InputApp:
    def __init__(
            self,
            root: tk.Tk,
            custom_config: Optional[Dict[str, Union[str, int, float]]] = None
    ):
        self.root = root
        self.root.title("Counted values extrapolator")
        self.root.geometry("600x200")

        if custom_config:
            self.config = custom_config
        else:
            if not CONFIG_FILE.exists():
                self.config = {
                    'until': 3600,
                    'scale_factor': 1,
                    'seed': 1
                }
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=4)
        self.root.grid_columnconfigure(2, weight=1)

        ttk.Label(
            self.root,
            text="Path to event file",
            anchor='w'
        ).grid(
            row=0,
            column=0,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.entry_events = ttk.Entry(self.root)
        self.entry_events.grid(
            row=0,
            column=1,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.btn_browse_events = ttk.Button(
            self.root,
            text="Browse...",
            command=self.browse_events
        )
        self.btn_browse_events.grid(
            row=0,
            column=2,
            sticky='ew',
            padx=1,
            pady=2
        )

        ttk.Label(
            self.root,
            text="Output file",
            anchor='w'
        ).grid(
            row=1,
            column=0,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.entry_output = ttk.Entry(self.root)
        self.entry_output.grid(
            row=1,
            column=1,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.btn_browse_output = ttk.Button(
            self.root,
            text="Browse...",
            command=self.browse_events
        )
        self.btn_browse_output.grid(
            row=1,
            column=2,
            sticky='ew',
            padx=1,
            pady=2
        )

        ttk.Label(
            self.root,
            text="Until (s)",
            anchor='w'
        ).grid(
            row=2,
            column=0,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.entry_until = ttk.Entry(self.root)
        self.entry_until.grid(
            row=2,
            column=1,
            sticky='ew',
            padx=1,
            pady=2
        )

        ttk.Label(
            self.root,
            text="Scale by",
            anchor='w'
        ).grid(
            row=3,
            column=0,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.entry_scale_factor = ttk.Entry(self.root)
        self.entry_scale_factor.grid(
            row=3,
            column=1,
            sticky='ew',
            padx=1,
            pady=2
        )

        ttk.Label(
            self.root,
            text="Seed",
            anchor='w'
        ).grid(
            row=4,
            column=0,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.entry_seed = ttk.Entry(self.root)
        self.entry_seed.grid(
            row=4,
            column=1,
            sticky='ew',
            padx=1,
            pady=2
        )

        self.run_btn = ttk.Button(self.root, text="Run", command=self.run_logic)
        self.run_btn.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky='ew',
            padx=1,
            pady=2
        )

        for i in range(6):
            self.root.grid_rowconfigure(i, weight=1)

        self.load_values()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def browse_events(self):
        """Opens file dialog for event file."""
        file_path = filedialog.askopenfilename(
            title="Select event file",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("JSON file", "*.json")]
        )
        if file_path:
            self.config['events_path'] = file_path
            self.entry_events.insert(0, file_path)

    def browse_output(self):
        file_path = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv"), ("JSON file", "*.json")]
        )
        if file_path:
            self.config['save_path'] = file_path
            self.entry_events.insert(0, file_path)

    def load_values(
            self,
            custom_config: Optional[Dict[str, Union[str, int, float]]] = None
    ):
        """Puts loaded config values into entries."""
        if custom_config is not None:
            config = custom_config
        else:
            config = self.config

        for key, val in config.items():
            if val is None:
                val = ""
            if key == 'events_path':
                self.entry_events.delete(0, tk.END)
                self.entry_events.insert(0, str(val))
            elif key == 'output_path':
                self.entry_output.delete(0, tk.END)
                self.entry_output.insert(0, str(val))
            elif key == 'until':
                self.entry_until.delete(0, tk.END)
                self.entry_until.insert(0, str(val))
            elif key == 'scale_factor':
                self.entry_scale_factor.delete(0, tk.END)
                self.entry_scale_factor.insert(0, str(val))
            elif key == 'seed':
                self.entry_seed.delete(0, tk.END)
                self.entry_seed.insert(0, str(val))

    def save_config(self):
        """Saves current entry values to config."""
        APP_FOLDER.mkdir(exist_ok=True)
        self.update_config()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def reset_config(self):
        """Resets all entries to None/Empty."""
        self.entry_events.delete(0, tk.END)
        self.entry_output.delete(0, tk.END)
        self.entry_until.delete(0, tk.END)
        self.entry_scale_factor.delete(0, tk.END)
        self.entry_seed.delete(0, tk.END)

    def update_config(self):
        config = {
            'events_path': self.entry_events.get() or None,
            'output_path': self.entry_output.get() or None,
            'until': self.entry_until.get() or None,
            'scale_factor': self.entry_scale_factor.get() or None,
            'seed': self.entry_seed.get() or None
        }
        self.config = config

    def run_logic(self):
        """Executes the main logic and handles errors."""
        try:
            events_path = self.entry_events.get() or None
            output_path = self.entry_output.get() or None
            until = nonneg_float(self.entry_until.get() or None)
            scale_factor = nonneg_float(self.entry_scale_factor.get() or None)
            seed = int(self.entry_seed.get() or None)
            if not events_path:
                raise ValueError("Event file path is required")
            extrapolate_scale(
                events_path=events_path,
                output_path=output_path,
                until=until,
                scale_factor=scale_factor,
                seed=seed
            )
            print(f"Processed: {events_path} -> {output_path}")
            messagebox.showinfo(
                "Success", f"New events saved\n{output_path}"
            )

        except Exception as e:
            ErrorWindow(str(e), self.root)

    def on_close(self):
        """Handles window close event gracefully."""
        self.save_config()
        self.root.destroy()


def nonneg_float(val: Any) -> float:
    fval = float(val)
    if fval <= 0:
        raise ValueError(
            'Float value cannot be less than or equal to 0'
        )
    return fval


def extrapolate(
        events_df: pd.DataFrame,
        until: Union[int, float] = 3600,
        seed: int = 1
) -> pd.DataFrame:
    if seed == 0:
        rng = np.random.default_rng()
    else:
        rng = np.random.default_rng(seed)
    earliest_time = round(events_df['time'].min())
    latest_time = round(events_df['time'].max())
    target_window = round(until - earliest_time)
    current_window = latest_time - earliest_time
    window_difference = target_window - current_window
    if target_window <= 0:
        raise ValueError(
            '`until` is less or equal than earliest time in dataset, cannot interpolate'
        )
    new_events_rows = []
    for (mode, from_e, to_e), mode_rel_df in events_df.groupby(['mode', 'from', 'to']):
        mode_count = len(mode_rel_df)
        to_generate = round(window_difference * mode_count / current_window)
        rate = mode_count / current_window
        generated = 0
        for sec, put in enumerate(rng.poisson(lam=rate, size=window_difference).tolist()):
            if put == 0:
                continue
            for cnt in range(put):
                new_events_rows.append({
                    'mode': mode,
                    'from': from_e,
                    'to': to_e,
                    'time': latest_time + sec + rng.random()
                })
                generated += 1
        print(
            f'extrapolate: generated {generated} vehicles of mode `{mode}` '
            f'on relation {from_e} -> {to_e} using poisson. '
            f'Expected number was {to_generate}'
        )
    new_events_df = pd.concat([
        events_df,
        pd.DataFrame(new_events_rows)
    ]).sort_values(by='time', ascending=True)
    return new_events_df


def scale(
        events_df: pd.DataFrame,
        factor: Union[float],
        seed: int = 1
) -> pd.DataFrame:
    if seed == 0:
        rng = np.random.default_rng()
    else:
        rng = np.random.default_rng(seed)
    earliest_time = round(events_df['time'].min())
    latest_time = round(events_df['time'].max())
    window = latest_time - earliest_time
    new_events_rows = []
    for (mode, from_e, to_e), mode_rel_df in events_df.groupby(['mode', 'from', 'to']):
        mode_count = len(mode_rel_df)
        to_generate = round(mode_count * factor)
        rate = to_generate / window
        generated = 0
        for sec, put in enumerate(rng.poisson(lam=rate, size=window).tolist()):
            if put == 0:
                continue
            for cnt in range(put):
                new_events_rows.append({
                    'mode': mode,
                    'from': from_e,
                    'to': to_e,
                    'time': earliest_time + sec + rng.random()
                })
                generated += 1
        print(
            f'scale: generated {generated} vehicles of mode `{mode}` '
            f'on relation {from_e} -> {to_e} using poisson. '
            f'Expected number was {to_generate}'
        )
    new_events_df = pd.DataFrame(new_events_rows).sort_values(
        by='time', ascending=True
    )
    return new_events_df


def extrapolate_scale(
        events_path: Union[Path, str],
        output_path: Union[Path, str],
        until: Optional[Union[int, float]] = 3600,
        scale_factor: Union[float, int] = 1,
        seed: int = 1
):
    events_df = read_events(events_path)
    if until is not None and until != 0:
        print(f'Extrapolating until {until} seconds')
        e_events_df = extrapolate(
            events_df=events_df,
            until=until,
            seed=seed
        )
    else:
        print('Not extrapolating, until is not set')
        e_events_df = events_df

    if scale_factor != 1:
        print(f'Scaling to a factor of {scale_factor}')
        s_events_df = scale(
            events_df=e_events_df,
            factor=scale_factor,
            seed=seed
        )
    else:
        print('Not scaling, scale_factor is 1')
        s_events_df = e_events_df
    write_events(events_df=s_events_df, output_path=output_path)


def parse_args(
        args_list: Optional[List[str]] = None
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Events extrapolator and scaler",
    )
    parser.add_argument(
        '--nogui',
        action='store_true',
        help='Run with provided arguments without graphical user interface'
    )
    parser.add_argument(
        '--events-path',
        type=str,
        required='--nogui' in sys.argv,
        help='Path to the event file (XML format). Use "None" or omit for default'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        required='--nogui' in sys.argv,
        help='Path to output interpolated and/or output file'
    )
    parser.add_argument(
        '--until',
        type=float,
        default=3600,
        help='Simulation time in seconds (default: 3600). Accepts int or float'
    )
    parser.add_argument(
        '--scale-factor',
        type=float,
        default=1,
        help='Route scaling factor (default: 1). Accepts int or float'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=0,
        help='Random seed for reproducibility. Must be an integer. 0 uses system time as seed'
    )
    args = parser.parse_args(sys.argv[1:] if args_list is None else args_list)
    if args.until <= 0:
        raise ValueError('--until must be greater than 0')
    if args.scale_factor <= 0:
        raise ValueError('--scale-factor must be greater than 0')
    return parser.parse_args()


def main(
        args_list: Optional[List[str]] = None
):
    args = parse_args(args_list)
    if not args.nogui:
        root = tk.Tk()
        app = InputApp(root=root)
        root.mainloop()
    else:
        extrapolate_scale(
            events_path=args.events_path,
            output_path=args.output_path,
            until=args.until,
            scale_factor=args.scale_factor,
            seed=args.seed
        )

if __name__ == '__main__':
    main()
