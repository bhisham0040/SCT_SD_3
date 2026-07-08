import tkinter as tk
from tkinter import messagebox, font
import time
import threading
import random

# ─────────────────────────────────────────────
#  COLORS & THEME
# ─────────────────────────────────────────────
BG_DARK      = "#0D1117"
BG_CARD      = "#161B22"
BG_GRID      = "#1C2128"
ACCENT       = "#00D4FF"
ACCENT2      = "#7C3AED"
ACCENT_GLOW  = "#00AACC"
CELL_EMPTY   = "#1C2128"
CELL_GIVEN   = "#0D1117"
CELL_SOLVED  = "#0A2540"
CELL_ACTIVE  = "#002244"
CELL_CONFLICT= "#3D0000"
TEXT_GIVEN   = "#E6EDF3"
TEXT_SOLVED  = "#00D4FF"
TEXT_GHOST   = "#3D4F5C"
TEXT_DIM     = "#8B949E"
BTN_BG       = "#21262D"
BTN_HOVER    = "#30363D"
BOX_BORDER   = "#00D4FF"
INNER_BORDER = "#30363D"

SAMPLE_PUZZLES = [
    # Easy
    [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],
        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],
        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ],
    # Medium
    [
        [0,0,0, 2,6,0, 7,0,1],
        [6,8,0, 0,7,0, 0,9,0],
        [1,9,0, 0,0,4, 5,0,0],
        [8,2,0, 1,0,0, 0,4,0],
        [0,0,4, 6,0,2, 9,0,0],
        [0,5,0, 0,0,3, 0,2,8],
        [0,0,9, 3,0,0, 0,7,4],
        [0,4,0, 0,5,0, 0,3,6],
        [7,0,3, 0,1,8, 0,0,0],
    ],
    # Hard
    [
        [0,0,0, 0,0,0, 0,0,0],
        [0,0,0, 0,0,3, 0,8,5],
        [0,0,1, 0,2,0, 0,0,0],
        [0,0,0, 5,0,7, 0,0,0],
        [0,0,4, 0,0,0, 1,0,0],
        [0,9,0, 0,0,0, 0,0,0],
        [5,0,0, 0,0,0, 0,7,3],
        [0,0,2, 0,1,0, 0,0,0],
        [0,0,0, 0,4,0, 0,0,9],
    ],
]

# ─────────────────────────────────────────────
#  SOLVER  (backtracking + MRV heuristic)
# ─────────────────────────────────────────────
def find_empty(board):
    # MRV: pick cell with fewest legal values
    best, best_pos = 10, None
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                opts = len(get_options(board, r, c))
                if opts < best:
                    best, best_pos = opts, (r, c)
    return best_pos

def get_options(board, row, col):
    used = set()
    used.update(board[row])
    used.update(board[r][col] for r in range(9))
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            used.add(board[r][c])
    return [n for n in range(1, 10) if n not in used]

def is_valid(board, row, col, num):
    if num in board[row]:
        return False
    if any(board[r][col] == num for r in range(9)):
        return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == num:
                return False
    return True

def solve(board, callback=None, delay=0.0):
    pos = find_empty(board)
    if pos is None:
        return True
    row, col = pos
    for num in get_options(board, row, col):
        board[row][col] = num
        if callback:
            callback(row, col, num, "try")
            if delay:
                time.sleep(delay)
        if solve(board, callback, delay):
            return True
        board[row][col] = 0
        if callback:
            callback(row, col, 0, "backtrack")
            if delay:
                time.sleep(delay)
    return False

def count_solutions(board, limit=2):
    """Return how many solutions exist (up to limit)."""
    pos = find_empty(board)
    if pos is None:
        return 1
    row, col = pos
    total = 0
    for num in get_options(board, row, col):
        board[row][col] = num
        total += count_solutions(board, limit)
        board[row][col] = 0
        if total >= limit:
            return total
    return total


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class SudokuApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SUDOKU · SOLVER")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        self.cells      = {}          # (r,c) -> Entry widget
        self.cell_vars  = {}          # (r,c) -> StringVar
        self.given      = set()       # fixed clues
        self.solving    = False
        self.step_count = 0
        self.start_time = 0
        self.speed_var  = tk.DoubleVar(value=0.0)
        self.current_puzzle = 0

        self._build_ui()
        self._load_puzzle(SAMPLE_PUZZLES[0])

    # ── layout ────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_DARK)
        hdr.pack(pady=(28, 0))

        tk.Label(hdr, text="SUDOKU", font=("Courier", 34, "bold"),
                 bg=BG_DARK, fg=ACCENT).pack()
        tk.Label(hdr, text="A U T O   S O L V E R",
                 font=("Courier", 11), bg=BG_DARK, fg=TEXT_DIM,
                 letterSpacing=8).pack(pady=(2, 0))

        # Divider
        div = tk.Canvas(self, height=2, bg=BG_DARK, highlightthickness=0)
        div.pack(fill=tk.X, padx=40, pady=(14, 18))
        div.create_line(0, 1, 2000, 1, fill=ACCENT, width=1)

        # Stats row
        stats = tk.Frame(self, bg=BG_DARK)
        stats.pack(padx=40, fill=tk.X)

        self.steps_lbl = self._stat_widget(stats, "STEPS", "0")
        self.time_lbl  = self._stat_widget(stats, "TIME",  "0.00s")
        self.status_lbl= self._stat_widget(stats, "STATUS","READY")

        # Grid
        grid_outer = tk.Frame(self, bg=ACCENT, padx=2, pady=2)
        grid_outer.pack(padx=40, pady=(18, 0))
        grid_mid = tk.Frame(grid_outer, bg=BG_GRID)
        grid_mid.pack(padx=1, pady=1)

        self._build_grid(grid_mid)

        # Speed slider
        speed_row = tk.Frame(self, bg=BG_DARK)
        speed_row.pack(pady=(16, 0), padx=40, fill=tk.X)
        tk.Label(speed_row, text="SOLVE SPEED", font=("Courier", 8),
                 bg=BG_DARK, fg=TEXT_DIM).pack(side=tk.LEFT)
        tk.Label(speed_row, text="INSTANT", font=("Courier", 8),
                 bg=BG_DARK, fg=TEXT_GHOST).pack(side=tk.LEFT, padx=(8,0))
        tk.Scale(speed_row, from_=0, to=100, orient=tk.HORIZONTAL,
                 variable=self.speed_var, showvalue=False,
                 bg=BG_DARK, fg=ACCENT, troughcolor=BG_CARD,
                 highlightthickness=0, bd=0, sliderlength=14,
                 length=160).pack(side=tk.LEFT, padx=4)
        tk.Label(speed_row, text="STEP·BY·STEP", font=("Courier", 8),
                 bg=BG_DARK, fg=TEXT_GHOST).pack(side=tk.LEFT)

        # Buttons
        btn_row = tk.Frame(self, bg=BG_DARK)
        btn_row.pack(pady=(18, 0), padx=40, fill=tk.X)

        self._btn(btn_row, "▶  SOLVE",   self._start_solve,  accent=True).pack(side=tk.LEFT, padx=(0,8))
        self._btn(btn_row, "⟳  RESET",   self._reset).pack(side=tk.LEFT, padx=(0,8))
        self._btn(btn_row, "✎  CLEAR",   self._clear).pack(side=tk.LEFT, padx=(0,8))

        # Puzzle selector
        pzl_row = tk.Frame(self, bg=BG_DARK)
        pzl_row.pack(pady=(12, 0), padx=40, fill=tk.X)
        tk.Label(pzl_row, text="PUZZLES:", font=("Courier", 8),
                 bg=BG_DARK, fg=TEXT_DIM).pack(side=tk.LEFT, padx=(0,8))
        for i, lbl in enumerate(["Easy", "Medium", "Hard"]):
            self._btn(pzl_row, lbl, lambda x=i: self._load_sample(x),
                      small=True).pack(side=tk.LEFT, padx=4)
        self._btn(pzl_row, "Random", self._random_puzzle, small=True).pack(side=tk.LEFT, padx=4)

        # Footer
        tk.Label(self, text="Enter your own numbers · click cells to edit",
                 font=("Courier", 8), bg=BG_DARK, fg=TEXT_GHOST).pack(pady=(14, 24))

    def _stat_widget(self, parent, label, value):
        frame = tk.Frame(parent, bg=BG_CARD, padx=16, pady=8)
        frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=6)
        tk.Label(frame, text=label, font=("Courier", 7),
                 bg=BG_CARD, fg=TEXT_DIM).pack()
        val_lbl = tk.Label(frame, text=value, font=("Courier", 16, "bold"),
                           bg=BG_CARD, fg=ACCENT)
        val_lbl.pack()
        return val_lbl

    def _build_grid(self, parent):
        for r in range(9):
            for c in range(9):
                # Box borders
                pt = 2 if r % 3 == 0 else 0
                pb = 2 if r == 8 else 0
                pl = 2 if c % 3 == 0 else 0
                pr = 2 if c == 8 else 0

                wrapper = tk.Frame(parent, bg=BOX_BORDER,
                                   padx=pl, pady=pt)
                wrapper.grid(row=r, column=c)

                inner = tk.Frame(wrapper, bg=INNER_BORDER, padx=0, pady=0)
                inner.pack(padx=(0, pr if pr else 1),
                           pady=(0, pb if pb else 1))

                var = tk.StringVar()
                cell = tk.Entry(
                    inner,
                    textvariable=var,
                    width=2,
                    font=("Courier", 20, "bold"),
                    justify="center",
                    bg=CELL_EMPTY,
                    fg=TEXT_GIVEN,
                    insertbackground=ACCENT,
                    relief=tk.FLAT,
                    bd=0,
                    highlightthickness=0,
                )
                cell.pack(ipady=8, ipadx=2)

                var.trace_add("write", lambda *a, r=r, c=c: self._on_edit(r, c))
                cell.bind("<FocusIn>",  lambda e, r=r, c=c: self._on_focus(r, c))
                cell.bind("<FocusOut>", lambda e, r=r, c=c: self._on_blur(r, c))
                cell.bind("<KeyPress>", lambda e, r=r, c=c: self._on_key(e, r, c))

                self.cells[(r, c)]    = cell
                self.cell_vars[(r, c)] = var

    def _btn(self, parent, text, cmd, accent=False, small=False):
        bg = ACCENT if accent else BTN_BG
        fg = BG_DARK if accent else TEXT_DIM
        fsize = 8 if small else 10
        b = tk.Button(parent, text=text, command=cmd,
                      font=("Courier", fsize, "bold"),
                      bg=bg, fg=fg,
                      activebackground=ACCENT_GLOW if accent else BTN_HOVER,
                      activeforeground=BG_DARK if accent else TEXT_GIVEN,
                      relief=tk.FLAT, bd=0, padx=14, pady=6,
                      cursor="hand2")
        b.bind("<Enter>", lambda e: b.config(bg=ACCENT_GLOW if accent else BTN_HOVER))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    # ── grid interaction ──────────────────────
    def _on_key(self, event, r, c):
        if (r, c) in self.given:
            return "break"
        # Allow only digits 1-9, backspace, delete
        if event.keysym in ("BackSpace", "Delete"):
            return
        if event.char in "123456789":
            self.cell_vars[(r, c)].set(event.char)
            return "break"
        return "break"

    def _on_edit(self, r, c):
        if self.solving:
            return
        val = self.cell_vars[(r, c)].get()
        if val and val[-1] not in "123456789":
            self.cell_vars[(r, c)].set(val[:-1])
        self._refresh_conflicts()

    def _on_focus(self, r, c):
        if (r, c) not in self.given:
            self.cells[(r, c)].config(bg=CELL_ACTIVE)

    def _on_blur(self, r, c):
        val = self.cell_vars[(r, c)].get()
        if (r, c) in self.given:
            self.cells[(r, c)].config(bg=CELL_GIVEN)
        elif val:
            self.cells[(r, c)].config(bg=CELL_SOLVED)
        else:
            self.cells[(r, c)].config(bg=CELL_EMPTY)

    def _refresh_conflicts(self):
        board = self._read_board()
        conflicts = self._find_conflicts(board)
        for (r, c), cell in self.cells.items():
            if (r, c) in self.given:
                cell.config(fg=TEXT_GIVEN, bg=CELL_GIVEN)
            elif (r, c) in conflicts:
                cell.config(bg=CELL_CONFLICT, fg="#FF6B6B")
            else:
                val = self.cell_vars[(r, c)].get()
                cell.config(bg=CELL_SOLVED if val else CELL_EMPTY,
                            fg=TEXT_SOLVED if val else TEXT_GIVEN)

    def _find_conflicts(self, board):
        bad = set()
        for r in range(9):
            seen = {}
            for c in range(9):
                v = board[r][c]
                if v:
                    if v in seen:
                        bad.add((r, c)); bad.add((r, seen[v]))
                    else:
                        seen[v] = c
        for c in range(9):
            seen = {}
            for r in range(9):
                v = board[r][c]
                if v:
                    if v in seen:
                        bad.add((r, c)); bad.add((seen[v], c))
                    else:
                        seen[v] = r
        for br in range(3):
            for bc in range(3):
                seen = {}
                for r in range(br*3, br*3+3):
                    for c in range(bc*3, bc*3+3):
                        v = board[r][c]
                        if v:
                            if v in seen:
                                bad.add((r, c)); bad.add(seen[v])
                            else:
                                seen[v] = (r, c)
        return bad

    # ── board helpers ─────────────────────────
    def _read_board(self):
        board = []
        for r in range(9):
            row = []
            for c in range(9):
                v = self.cell_vars[(r, c)].get()
                row.append(int(v) if v.isdigit() else 0)
            board.append(row)
        return board

    def _load_puzzle(self, puzzle):
        self.given.clear()
        self.solving = False
        self._reset_stats()
        for r in range(9):
            for c in range(9):
                v = puzzle[r][c]
                self.cell_vars[(r, c)].set(str(v) if v else "")
                cell = self.cells[(r, c)]
                if v:
                    self.given.add((r, c))
                    cell.config(bg=CELL_GIVEN, fg=TEXT_GIVEN,
                                state="normal", disabledforeground=TEXT_GIVEN)
                else:
                    cell.config(bg=CELL_EMPTY, fg=TEXT_GIVEN, state="normal")

    def _load_sample(self, idx):
        self.current_puzzle = idx
        self._load_puzzle(SAMPLE_PUZZLES[idx])

    def _random_puzzle(self):
        # Generate a valid puzzle by solving an empty board with
        # randomised first row, then removing cells.
        board = [[0]*9 for _ in range(9)]
        nums = list(range(1, 10))
        random.shuffle(nums)
        for c in range(9):
            board[0][c] = nums[c]
        solve(board)
        # Remove cells ensuring unique solution
        cells = list((r, c) for r in range(9) for c in range(9))
        random.shuffle(cells)
        removed = 0
        target = random.randint(46, 54)   # 27-35 clues
        for (r, c) in cells:
            if removed >= target:
                break
            backup = board[r][c]
            board[r][c] = 0
            test = [row[:] for row in board]
            if count_solutions(test) == 1:
                removed += 1
            else:
                board[r][c] = backup
        self._load_puzzle(board)

    def _reset_stats(self):
        self.step_count = 0
        self.steps_lbl.config(text="0")
        self.time_lbl.config(text="0.00s")
        self.status_lbl.config(text="READY", fg=ACCENT)

    # ── solve controls ────────────────────────
    def _start_solve(self):
        if self.solving:
            return
        board = self._read_board()
        conflicts = self._find_conflicts(board)
        if conflicts:
            self.status_lbl.config(text="CONFLICT", fg="#FF6B6B")
            messagebox.showerror("Conflict", "The puzzle has conflicting numbers!\nPlease fix them first.")
            return

        # Lock given cells
        self.given.clear()
        for r in range(9):
            for c in range(9):
                if board[r][c]:
                    self.given.add((r, c))
                    self.cells[(r, c)].config(bg=CELL_GIVEN)
                else:
                    self.cell_vars[(r, c)].set("")
                    self.cells[(r, c)].config(bg=CELL_EMPTY, fg=TEXT_SOLVED)

        self.solving   = True
        self.step_count = 0
        self.start_time = time.time()
        self.status_lbl.config(text="SOLVING…", fg="#FFD700")

        delay = (self.speed_var.get() / 100) * 0.08   # 0 – 80 ms

        def run():
            solution = [row[:] for row in board]
            ok = solve(solution, self._vis_callback, delay)
            elapsed = time.time() - self.start_time
            self.after(0, self._on_done, ok, elapsed)

        threading.Thread(target=run, daemon=True).start()

    def _vis_callback(self, row, col, num, action):
        self.step_count += 1
        def update():
            if num == 0:
                self.cell_vars[(row, col)].set("")
                self.cells[(row, col)].config(bg=CELL_EMPTY, fg=TEXT_SOLVED)
            else:
                self.cell_vars[(row, col)].set(str(num))
                color = CELL_ACTIVE if action == "try" else CELL_CONFLICT
                self.cells[(row, col)].config(bg=color, fg=TEXT_SOLVED)

            self.steps_lbl.config(text=str(self.step_count))
            elapsed = time.time() - self.start_time
            self.time_lbl.config(text=f"{elapsed:.2f}s")
        self.after(0, update)

    def _on_done(self, ok, elapsed):
        self.solving = False
        if ok:
            # Flash cells green
            for (r, c) in self.cells:
                if (r, c) not in self.given:
                    self.cells[(r, c)].config(bg=CELL_SOLVED, fg=TEXT_SOLVED)
            self.status_lbl.config(text="SOLVED ✓", fg="#00FF88")
            self.time_lbl.config(text=f"{elapsed:.3f}s")
        else:
            self.status_lbl.config(text="UNSOLVABLE", fg="#FF4444")
            messagebox.showwarning("No Solution", "This puzzle has no valid solution.")

    def _reset(self):
        if self.solving:
            return
        # Reload last puzzle from given cells only
        board = [[0]*9 for _ in range(9)]
        for (r, c) in self.given:
            v = self.cell_vars[(r, c)].get()
            board[r][c] = int(v) if v.isdigit() else 0
        self._load_puzzle(board)
        for (r, c) in self.given:
            self.cells[(r, c)].config(bg=CELL_GIVEN)

    def _clear(self):
        if self.solving:
            return
        for r in range(9):
            for c in range(9):
                self.cell_vars[(r, c)].set("")
                self.cells[(r, c)].config(bg=CELL_EMPTY, fg=TEXT_GIVEN, state="normal")
        self.given.clear()
        self._reset_stats()


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()
