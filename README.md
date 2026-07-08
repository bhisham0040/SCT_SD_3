# 🧩 Sudoku Solver

A sleek, cyberpunk-themed Sudoku Solver built with Python and tkinter.


## Features

* Enter any Sudoku puzzle — click cells to type your own numbers
* Solves automatically using a **Backtracking + MRV heuristic** algorithm
* Visual step-by-step mode — watch the algorithm think in real time
* Live conflict detection — highlights invalid numbers as you type
* 3 built-in puzzles — Easy, Medium, and Hard difficulties
* Random puzzle generator — creates valid, uniquely-solvable boards
* Live stats — step counter and solve timer update during solving
* Dark cyberpunk UI — cyan accent theme with a glowing grid
* Adjustable solve speed — from instant to frame-by-frame via slider

## Technologies Used

* Python 3
* tkinter (built-in GUI framework)
* Backtracking algorithm with MRV heuristic
* Python `threading` module (non-blocking UI during solve)

## Run Locally

```bash
# Clone the repo
git clone https://github.com/your-username/sudoku-solver.git
cd sudoku-solver

# No dependencies needed — tkinter is built into Python
# On Linux, if tkinter is missing:
sudo apt install python3-tk

# Run the app
python3 sudoku_solver.py
```

> ✅ No `pip install` needed — zero external dependencies.

