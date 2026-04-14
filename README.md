# transcounter

> A Python package for traffic counting and exporting data to SUMO (Simulation of Urban MObility).

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Platform: Linux | macOS | Windows](https://img.shields.io/badge/platform-Linux%20|%20macOS%20|%20Windows-lightgrey.svg)](https://opensource.org/licenses/GPL-3.0)
[![License: GPL v3](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](https://opensource.org/licenses/GPL-3.0)

**Author:** Ing. Dmitrii Grishchuk

---
## 📖 Overview

`transcounter` is a utility designed to help traffic engineers and researchers count traffic data, extrapolate patterns, and convert raw data into formats compatible with SUMO. It is built with a command-line interface (CLI) for easy automation.

### Key Features

*   **📊 Traffic Counting:** Process raw traffic data into structured logs.
*   **📈 Extrapolation:** Generate extra traffic volume over time with Poisson distribution.
*   **🚗 SUMO Export:** Convert processed data for use in SUMO traffic simulations.
---
## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your machine:

1.  **Python 3.9 or higher**:
    *   **Windows:** [Download Python](https://www.python.org/downloads/windows/)
    *   **macOS:** Usually pre-installed. Check with `python3 --version`. If missing, use [Homebrew](https://brew.sh/).
    *   **Linux:** Usually pre-installed. Check with `python3 --version`. If missing, use your distro's package manager (e.g., `sudo apt install python3`).
2.  **Git** - optional: Required to clone the repository via command line / terminal.
    *   **Windows:** [Download Git](https://git-scm.com/download/win)
    *   **macOS:** `brew install git`
    *   **Linux:** Usually pre-installed; if not, on Debian-based systems can be obtained via `apt` using `sudo apt install git`
---
## 🚀 Installation

Use a **Virtual Environment (venv)** to keep dependencies isolated from your system Python.

### 1. Clone the Repository
> The easiest way is to locate the `Code` button on the repository's GitHub page, click to see the drop-down menu and choose `Download ZIP`.
> Unpack the archive after it's done downloading, and move inside the resulting folder.

If you wish to use **Git**, open your terminal (Command Prompt, PowerShell, or Terminal) and run:
```sh
git clone https://github.com/leonefamily/transcounter.git
cd transcounter
```
### 2. Create a virtual environment and install the package

Select the instructions below that match your operating system:

### 🪟 Windows
> The easiest way is to double-click the `install.bat` file, or launch it via the command prompt while being in the same directory

or, the manual option is also available:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```
### 🍎 macOS / 🐧 Linux
> The easiest way is to first allow launching the file `install.sh` in the context menu, and then double-click it. 
> Alternatively, in the directory with the file, run
> ```sh
> chmod +x install.sh  # run this only once
> source install.sh
> ```
or manually:
```sh
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Once the environment is active, you should see `(venv)` at the start of your terminal prompt on both macOS/Linux and Windows
> **Note** This will not happen if you used batch or shell script by double-clicking them


### 3. Usage

Once installed, you can run the CLI tools directly from the terminal.

### 📋 Available Commands

The `transcounter` package provides three main tools:

1.  **`counter`**: Helps to count traffic events on an intersection from video feed.
2.  **`extrapolator`**: Extrapolates and/or scales traffic patterns.
3.  **`converter`**: Converts data for SUMO export.
4.  **`transcounter`**: Shows the GUI that supports picking a script.

### counter

> Double-click `run_counter.bat` (on Windows) or `run_counter.sh` (on macOS and Linux; make sure it's allowed to launch)

or run command without arguments to enter the graphical interface, while in `(venv)`
```sh
counter
```
The program will ask for the path you would like to save the output file.
It remembers the previous choices, if you launch again.

It produces .csv or .json files with columns/keys: 
- `mode` - mode of the vehicle (for now, the available options are car, truck, motorbike)
- `from` - ID of source
- `to` - ID of target
- `time` - time in seconds since the start button was pushed and vehicle move registered 

#### How to use the GUI
Using LMB, drag a corresponding vehicle type's icon from the source area to the road area where the vehicle has moved, and let go.
The events count will increase, and a message will appear below, e.g. `car, 4 > 1: 1`, where the last number
symbolizes hom many vehicles of this type have made this maneuver so far.

> Roads are numbered counterclockwise from the left side. Left is 1, bottom is 2, right is 3, top is 4

> **Note** Do not forget to start the timer when counting (leftmost button `Start` at the top row)

The timer may as well be paused and resumed with `Pause` and `Resume` buttons, but currently cannot be rewound.
Time is shown in human-readable format, but the data has values in seconds (including fractions). 

Should you want to undo the last action, locate the `Undo` button on the bottom-left part of the window.
It removes the last record from events list, thus decreasing the total count of events, 
and the affected vehicle type maneuvers' count.

### extrapolator

Run the extrapolator to predict traffic flow using Poisson distribution based on the counted flows.
Useful when the desired duration of the simulation is longer than the actual time span of counted events.


> Double-click `run_extrapolator.bat` (on Windows) or `run_extrapolator.sh` (on macOS and Linux; make sure it's allowed to launch)

or run without arguments to see the GUI:
```sh
extrapolator
```
Provide the path to the events file obtained from the `counter` program, and the path to the output file
that will hold the results of this script by direct pasting or interactively choosing
with the system dialog accessible via `Browse...`.

`Until` option dictates, what will be the last second
of the new results. It cannot be less than the latest entry in the original events, or less than 0. Value of 0 will
disable extrapolation. The value is 3600 by default, which corresponds to 1 hour.

`Scale by` is a scale factor, it will add extra vehicles (>1) or reduce their count less (<1).
It launches after extrapolation, if both desired. The value cannot be 0 or negative.
> **Note** Scale factor other than 1 will not keep the original events' times and order, the results will 
> be regenerated based solely on their count and time boundaries.

`Seed` is used to get reproducible results from running the script. Positive integer values are accepted; 0 will make
random numbers generators use current system time as seed. and lead to different results each time the script is launched. 

This script's GUI, too, remembers previous choices once the program is closed.

If you'd like to use the command line interface eather than inputting values graphically, run:
```sh
extrapolator --nogui --events-path="/path/to/events.csv" --output-path="/path/to/new_events.csv" --until=3600 --scale-factor=1 --seed=1
```
The same will work when `extrapolator` is replaced with `.\run_extrapolator.bat` or `./run_extrapolator.sh` on appropriate systems.
### converter

The script converts events data to SUMO .rou.xml format.

> Double-click `run_extrapolator.bat` (on Windows) or `run_extrapolator.sh` (on macOS and Linux; make sure it's allowed to launch)

or launch without arguments to enter GUI:
```sh
converter
```
Provide the desired events (either just counted, or extrapolated/scaled) to the corresponding fields. Let the script know,
what are source and sink edges of roads are called, e.g. if the desired spawn edge for vehicles going from road 1
is named E1 in the SUMO network, input this value.
> **Note** If you don't provide source and sink edges names, the script will just use internal values, e.g. 1 to 4.
> In order for the resulting routes file to work in SUMO, you would need to change the edges names to these numbers.

Last typed options are saved upon quitting.

Command line options to launch script from the terminal:
```sh
converter --nogui --events-path="/path/to/events.csv" --output-routes-path="/path/to/save/events.rou.xml" --source1="E1" --sink1="-E1" --source2="E2" --sink2="-E2" --source3="E3" --sink3="-E3" --source4="E4" --sink4="-E4"
```
The same will work when `converter` is replaced with `.\run_converter.bat` or `./run_converter.sh` on appropriate systems.

---
## 📂 Project Structure
```text
├── transcounter/
│   ├── images/
│   │   ├── car.png
│   │   ├── motorbike.png
│   │   └── truck.png
│   ├── __init__.py
│   ├── converter.py
│   ├── counter.py
│   ├── extrapolator.py
│   ├── selector.py
│   └── utilities.py
├── .gitignore
├── install.bat
├── install.sh
├── LICENSE
├── pyproject.toml
├── README.md
├── run_converter.bat
├── run_converter.sh
├── run_counter.bat
├── run_counter.sh
├── run_extrapolator.bat
└── run_extrapolator.sh
```

---
## 📚 Dependencies

This project relies on the following Python libraries:

*   `shapely` (>=2.0.0)
*   `numpy` (>=2.0.0)
*   `pandas` (>=2.0.0)
*   `pygame` (>=2.0.0)
*   `pygame-widgets` (>=1.0.0)

---
## ⚠️ Known issues

- On Windows 10 and 11 there is an error `Path to file ... does not exist` when providing paths to files that
are to be created through the system dialog due to _Controlled Folder Access_ restrictions.
The workaround is to paste the desired path directly into the corresponding field

___
## 🤝 Development

Contributions are what make the open-source community such an amazing place to learn, inspire, and create.

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

Binary artifacts of PyInstaller can be produced using this command from project's directory
(with virtual environment that gets created after installation, pyinstaller must be installed additionally):
```sh
pyinstaller --onefile --windowed --name="transcounter" --hidden-import=transcounter.counter 
--hidden-import=transcounter.extrapolator --hidden-import=transcounter.converter --add-data "transcounter/images:transcounter/images" 
transcounter/selector.py
```

---
## 📄 License

This project is licensed under the GPL v3 License - see the [LICENSE](LICENSE) file for details.

---
## 📞 Contact

*   **Project Link:** [https://github.com/leonefamily/transcounter](https://github.com/leonefamily/transcounter)
*   **Author:** Ing. Dmitrii Grishchuk - search for contacts at the [BUT site](https://www.vut.cz/) or at the [Brno Chief Architect's Office site](https://kambrno.com/)