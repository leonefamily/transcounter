import os
import sys
import json
import argparse
import tkinter as tk
from pathlib import Path
from datetime import datetime as dt
from typing import Optional, Dict, Union
from tkinter import ttk, filedialog, messagebox

from transcounter.utilities import APP_FOLDER, read_events, ErrorWindow
from transcounter import __version__ as pver

CONFIG_FILE = APP_FOLDER / 'converter.json'
VTYPES = {
    "car": {
        "id": "car",
        "accel": 1.5,              # m/s^2 (Acceleration)
        "decel": 4.5,              # m/s^2 (Deceleration)
        "emergencyDecel": 9.0,     # m/s^2 (Emergency Braking)
        "minGap": 2.5,             # m (Min gap to leader)
        "maxSpeed": 36.11,         # m/s (130 km/h converted)
        "desiredMaxSpeed": 36.11,  # m/s (Desired max speed)
        "speedFactor": 1.0,        # Multiplier for speed limits
        "color": "1,1,1",          # RGB (White)
        "vClass": "passenger",     # Vehicle class
        "guiShape": "passenger",   # Visualization shape
        "width": 1.8,              # m
        "height": 1.5,             # m
        "length": 4.5,             # m
        "mass": 1500,              # kg
        "personCapacity": 4,       # Passengers
    },
    "truck": {
        "id": "truck",
        "accel": 0.5,              # m/s^2 (Slower acceleration)
        "decel": 3.0,              # m/s^2 (Heavier braking distance)
        "emergencyDecel": 9.0,     # m/s^2
        "minGap": 3.5,             # m (Needs more space)
        "maxSpeed": 25.0,          # m/s (90 km/h converted)
        "desiredMaxSpeed": 25.0,   # m/s
        "speedFactor": 1.0,
        "color": "0,0.5,0",        # RGB (Greenish)
        "vClass": "truck",
        "guiShape": "truck",
        "width": 2.5,              # m
        "height": 3.5,             # m
        "length": 15.0,            # m
        "mass": 12000,             # kg
        "personCapacity": 0,       # No passengers
    },
    "motorbike": {
        "id": "motorbike",
        "accel": 2.0,              # m/s^2
        "decel": 6.0,              # m/s^2 (Good braking)
        "emergencyDecel": 10.0,    # m/s^2
        "minGap": 1.5,             # m (Narrower)
        "maxSpeed": 44.44,         # m/s (160 km/h converted)
        "desiredMaxSpeed": 44.44,  # m/s
        "speedFactor": 1.0,
        "color": "1,0.5,0",        # RGB (Orange/Yellow)
        "vClass": "motorcycle",
        "guiShape": "motorcycle",
        "width": 0.8,              # m
        "height": 1.2,             # m
        "length": 2.0,             # m
        "mass": 250,               # kg
        "personCapacity": 1,       # Rider
    }
}


def convert(
        events_path: Union[str, Path],
        output_routes_path: Union[str, Path],
        edges_source_sink: Dict[str, str]
):
    events_df = read_events(events_path=events_path)

    vtype_definitions = ''
    vehicles_definitions = ''
    seen_vtypes = set()
    missing_source_map = set()
    missing_sink_map = set()
    for nr, event in events_df.sort_values('time').iterrows():
        if event['mode'] not in seen_vtypes:
            keys_vals = ' '.join(
                f'{k}="{v}"' for k, v in VTYPES[event['mode']].items()
            )
            vtype_definitions += f'\t<vType {keys_vals}/>\n'
            seen_vtypes.add(event['mode'])

        source_key = f"source{event['from']}"
        sink_key = f"sink{event['to']}"
        # source
        if source_key in edges_source_sink and edges_source_sink[source_key] is not None:
            source_edge = edges_source_sink[source_key]
        else:
            source_edge = event['from']
            missing_source_map.add(source_edge)
        # sink
        if sink_key in edges_source_sink and edges_source_sink[sink_key] is not None:
            sink_edge = edges_source_sink[sink_key]
        else:
            sink_edge = event['to']
            missing_sink_map.add(sink_edge)

        veh_dict = {
            'id': nr,
            'type': event['mode'],
            'depart': round(event['time'], 2),
            'from': source_edge,
            'to': sink_edge
        }
        veh_keys_vals = ' '.join(
            f'{k}="{v}"' for k, v in veh_dict.items()
        )

        veh_def = f'\t<trip {veh_keys_vals}/>\n'
        vehicles_definitions += veh_def

    routes_string = (
        '<?xml version="1.0" encoding="UTF-8"?>\n\n'
        f'<!-- generated on {dt.now()} by {__name__} {pver}-->\n\n'
        f'<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n'
        f'\t<!-- VTypes -->\n{vtype_definitions}'
        '\t<!-- Vehicles, persons and containers (sorted by depart) -->\n'
        f'{vehicles_definitions}</routes>'
    )
    with open(output_routes_path, 'w') as f:
        f.write(routes_string)


class InputApp:
    def __init__(
            self,
            root: tk.Tk,
            custom_config: Optional[Dict[str, Union[str, int, float]]] = None
    ):
        self.root = root
        self.root.title("SUMO Route Converter")
        self.root.geometry("600x320")

        if custom_config:
            self.config = custom_config
        else:
            if not CONFIG_FILE.exists():
                self.config = {}
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

        # Row 1: Routes File
        ttk.Label(
            self.root,
            text="Path to routes output file",
            anchor='w'
        ).grid(
            row=1,
            column=0,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.entry_routes = ttk.Entry(self.root)
        self.entry_routes.grid(
            row=1,
            column=1,
            sticky='ew',
            padx=1,
            pady=2
        )
        self.btn_browse_routes = ttk.Button(
            self.root,
            text="Browse...",
            command=self.browse_routes
        )
        self.btn_browse_routes.grid(
            row=1,
            column=2,
            sticky='ew',
            padx=1,
            pady=2
        )

        self.edge_pairs = []
        i_cum = 2  # next row to be populated
        for i in range(1, 5):
            # source
            ttk.Label(
                self.root,
                text=f"Edge {i} source",
                anchor='w'
            ).grid(
                row=i_cum,
                column=0,
                sticky='ew',
                padx=1,
                pady=2
            )
            self.entry_source = ttk.Entry(self.root)
            self.entry_source.grid(
                row=i_cum,
                column=1,
                sticky='ew',
                padx=1,
                pady=2
            )

            # sink
            ttk.Label(
                self.root,
                text=f"Edge {i} sink",
                anchor='w'
            ).grid(
                row=i_cum + 1,
                column=0,
                sticky='ew',
                padx=1,
                pady=2
            )
            self.entry_sink = ttk.Entry(self.root)
            self.entry_sink.grid(
                row=i_cum + 1,
                column=1,
                sticky='ew',
                padx=1,
                pady=2
            )

            self.edge_pairs.append({
                'source': self.entry_source,
                'sink': self.entry_sink
            })

            i_cum += 2  # two rows are added

        self.run_btn = ttk.Button(self.root, text="Run", command=self.run_logic)
        self.run_btn.grid(
            row=i_cum,
            column=0,
            columnspan=3,
            sticky='ew',
            padx=1,
            pady=2
        )
        i_cum += 1

        # to properly expand rows vertically
        for i in range(i_cum):
            self.root.grid_rowconfigure(i, weight=1)

        # load values into widgets
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

    def browse_routes(self):
        """Opens save dialog for routes file."""
        file_path = filedialog.asksaveasfilename(
            title="Save routes file",
            defaultextension=".rou.xml",
            filetypes=[("SUMO routes", "*.rou.xml")],
            initialfile="routes"
        )
        if file_path:
            self.config['output_routes_path'] = file_path
            self.entry_routes.insert(0, file_path)

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
            elif key == 'output_routes_path':
                self.entry_routes.delete(0, tk.END)
                self.entry_routes.insert(0, str(val))
            elif key.startswith('source'):
                key_num = int(key.replace('source', '')) - 1
                self.edge_pairs[key_num]['source'].insert(0, str(val))
            elif key.startswith('sink'):
                key_num = int(key.replace('sink', '')) - 1
                self.edge_pairs[key_num]['sink'].insert(0, str(val))

    def save_config(self):
        """Saves current entry values to config."""
        APP_FOLDER.mkdir(exist_ok=True)
        self.update_config()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def reset_config(self):
        """Resets all entries to None/Empty."""
        self.entry_events.delete(0, tk.END)
        self.entry_routes.delete(0, tk.END)
        for pair in self.edge_pairs:
            pair['source'].delete(0, tk.END)
            pair['sink'].delete(0, tk.END)

    def update_config(self):
        config = {
            'events_path': self.entry_events.get() or None,
            'output_routes_path': self.entry_routes.get() or None,
        }
        for i, pair in enumerate(self.edge_pairs, start=1):
            config[f'source{i}'] = pair['source'].get() or None
            config[f'sink{i}'] = pair['sink'].get() or None
        self.config = config

    def run_logic(self):
        """Executes the main logic and handles errors."""
        try:
            events_path = self.entry_events.get() or None
            output_routes_path = self.entry_routes.get() or None
            if not events_path:
                raise ValueError("Event file path is required")
            if not output_routes_path:
                raise ValueError("Routes file path is required")
            edges_source_sink = {}
            for n, pair in enumerate(self.edge_pairs, start=1):
                edges_source_sink[f'source{n}'] = pair['source'].get() or None
                edges_source_sink[f'sink{n}'] = pair['sink'].get() or None
            convert(
                events_path=events_path,
                output_routes_path=output_routes_path,
                edges_source_sink=edges_source_sink
            )
            print(f"Processed: {events_path} -> {output_routes_path}")
            messagebox.showinfo("Success", f"Routes saved\n{output_routes_path}")

        except Exception as e:
            # Launch error window
            ErrorWindow(str(e), self.root)

    def on_close(self):
        """Handles window close event gracefully."""
        # Nothing happens, just destroy
        self.save_config()
        self.root.destroy()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SUMO route converter; CLI configuration",
    )
    parser.add_argument(
        '--nogui',
        action='store_true',
        help='Run with provided arguments without graphical user interface'
    )
    parser.add_argument(
        '--events-path',
        required='--nogui' in sys.argv,
        help='Path to the events file (CSV or JSON format). '
             'Affects whether events-path and output-routes-path are mandatory'
    )
    parser.add_argument(
        '--output-routes-path',
        required='--nogui' in sys.argv,
        help='Path to routes output file (SUMO .rou.xml format)'
    )
    for e_num in range(1, 5):
        parser.add_argument(
            f'--source{e_num}',
            help='Source node for edge {e_num}'
        )
        parser.add_argument(
            f'--sink{e_num}',
            help=f'Sink node for edge {e_num}'
        )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if not args.nogui:
        root = tk.Tk()
        app = InputApp(root=root)
        root.mainloop()
    else:
        edges_source_sink = {}
        for i in range(1, 5):
            if hasattr(args, f'source{i}'):
                val = getattr(args, f'source{i}')
                edges_source_sink[f'source{i}'] = val
            elif hasattr(args, f'sink{i}'):
                val = getattr(args, f'sink{i}')
                edges_source_sink[f'sink{i}'] = val
        convert(
            events_path=args.events_path,
            output_routes_path=args.output_routes_path,
            edges_source_sink=edges_source_sink
        )


if __name__ == "__main__":
    main()
