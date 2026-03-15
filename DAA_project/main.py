# main.py
"""Main GUI application for Dominosa game"""
import tkinter as tk
from tkinter import ttk, messagebox

from constants import NEON, DEFAULT_GRID_SIZE, DEFAULT_TIME_LIMIT, DEFAULT_HINTS
from models import Cell
from game_logic import GameLogic
from renderer import Renderer


class DominosaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dominosa - Neon Graph Suite")
        self.root.geometry("1150x750")
        self.root.configure(bg=NEON["bg"])
        
        self.GRID = DEFAULT_GRID_SIZE
        self.time_left = DEFAULT_TIME_LIMIT
        self.current_turn = "User"
        self.user_score = 0
        self.comp_score = 0
        self.game_active = True
        self.timer_id = None
        self.show_edges = True

        # Hint system
        self.user_hints_left = DEFAULT_HINTS
        self.comp_hints_left = DEFAULT_HINTS
        self.hinted_move = None

        self._setup_ui()
        self.init_game()
        
        # Bind events
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())

    def _setup_ui(self):
        """Setup all UI components"""
        # Main canvas
        self.canvas = tk.Canvas(self.root, bg=NEON["bg"], highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=NEON["panel_bg"], width=650)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        # Header
        tk.Label(self.sidebar, text="Dominosa", fg=NEON["accent"], bg=NEON["panel_bg"], 
                font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=20, pady=(20, 0))
        
        # Stats Display
        self.stats_frame = tk.Frame(self.sidebar, bg=NEON["panel_bg"])
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        self.score_lbl = tk.Label(self.stats_frame, text="User: 0 | CPU: 0", fg=NEON["accent2"], 
                                 bg=NEON["panel_bg"], font=("Consolas", 12))
        self.score_lbl.pack(side="left")
        self.timer_lbl = tk.Label(self.stats_frame, text="Time: 30s", fg=NEON["accent"], 
                                 bg=NEON["panel_bg"], font=("Consolas", 12, "bold"))
        self.timer_lbl.pack(side="right")

        # Hints Display
        self.hints_frame = tk.Frame(self.sidebar, bg=NEON["panel_bg"])
        self.hints_frame.pack(fill="x", padx=20, pady=5)
        self.hints_lbl = tk.Label(self.hints_frame, text="Hints → User: 2/2 | CPU: 2/2", 
                                 fg=NEON["accent2"], bg=NEON["panel_bg"], font=("Consolas", 10))
        self.hints_lbl.pack(side="left")

        # Difficulty Selector
        tk.Label(self.sidebar, text="Difficulty Level:", fg=NEON["text"], bg=NEON["panel_bg"], 
                font=("Consolas", 10)).pack(anchor="w", padx=20, pady=(5, 0))
        self.case_var = tk.StringVar(value="Random (Easy 4x4)")
        self.case_menu = ttk.Combobox(self.sidebar, textvariable=self.case_var, state="readonly", 
                                     values=["Random (Easy 4x4)", "Random (Medium 6x6)", 
                                           "Dead End Case (Impossible)"])
        self.case_menu.pack(fill="x", padx=20, pady=5)
        self.case_menu.bind("<<ComboboxSelected>>", lambda e: self.init_game())

        # Controls
        btn_frame = tk.Frame(self.sidebar, bg=NEON["panel_bg"])
        btn_frame.pack(fill="x", padx=20, pady=5)
        b_config = {"bg": NEON["btn_bg"], "fg": NEON["text"], "relief": "flat", 
                   "font": ("Consolas", 9, "bold")}
        tk.Button(btn_frame, text="🔄 New Game", command=self.init_game, **b_config).grid(row=0, column=0, sticky="ew", padx=1)
        tk.Button(btn_frame, text="↺ Restart", command=self.restart_game, **b_config).grid(row=0, column=1, sticky="ew", padx=1)
        tk.Button(btn_frame, text="💡 Hint", command=self.use_hint, **b_config).grid(row=0, column=2, sticky="ew", padx=1)
        tk.Button(btn_frame, text="🤖 Solve", command=self.solve_logic, **b_config).grid(row=0, column=3, sticky="ew", padx=1)
        btn_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Tabbed View
        self.tabs = ttk.Notebook(self.sidebar)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Terminal Tab
        self.terminal = tk.Text(self.tabs, bg=NEON["terminal_bg"], fg=NEON["terminal_fg"], 
                               font=("Consolas", 10), borderwidth=0, padx=10, pady=10)
        self.tabs.add(self.terminal, text="📝 Terminal")
        
        # Graph View Tab
        graph_frame = tk.Frame(self.tabs, bg=NEON["terminal_bg"])
        self.tabs.add(graph_frame, text="📊 Graph View")
        
        toggle_frame = tk.Frame(graph_frame, bg=NEON["terminal_bg"])
        toggle_frame.pack(fill="x", padx=10, pady=5)
        self.edge_toggle_btn = tk.Button(toggle_frame, text="🔗 Hide Edges", command=self.toggle_edges,
                                         bg=NEON["btn_bg"], fg=NEON["text"], relief="flat", 
                                         font=("Consolas", 9, "bold"))
        self.edge_toggle_btn.pack(side="left")
        
        self.graph_canvas = tk.Canvas(graph_frame, bg=NEON["terminal_bg"], highlightthickness=0)
        self.graph_canvas.pack(fill="both", expand=True)
        self.graph_canvas.bind("<Configure>", lambda e: self.draw_graph())

    def log(self, msg):
        """Log message to terminal"""
        self.terminal.insert("end", f"{msg}\n")
        self.terminal.see("end")

    def init_game(self):
        """Initialize a new game"""
        case = self.case_var.get()
        self.GRID = 6 if "6x6" in case else 4

        if "Dead End" in case:
            self.current_vals = [[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]]
        else:
            self.current_vals = GameLogic.generate_valid_board(self.GRID)

        self.cells = [[Cell(r, c, self.current_vals[r][c]) for c in range(self.GRID)] 
                     for r in range(self.GRID)]
        self.dominoes = []
        self.used_pairs = set()
        self.selected = []
        self.user_score = 0
        self.comp_score = 0
        self.game_active = True
        self.current_turn = "User"
        self.time_left = DEFAULT_TIME_LIMIT
        
        self.user_hints_left = DEFAULT_HINTS
        self.comp_hints_left = DEFAULT_HINTS
        self.hinted_move = None
        
        max_val = self.GRID - 1
        self.all_pairs = [(i, j) for i in range(max_val + 1) for j in range(i, max_val + 1)]
        self.pair_status = {pair: "unclaimed" for pair in self.all_pairs}
        
        if self.timer_id: 
            self.root.after_cancel(self.timer_id)
        self.update_timer()
        self.draw_board()
        self.draw_graph()
        self.update_hints_display()
        
        self.terminal.delete(1.0, tk.END)
        self.log("=== HOW TO PLAY ===")
        self.log("1. Click adjacent numbers to link them.")
        self.log("2. Use each domino pair only ONCE.")
        self.log("3. Solve before the 30s timer runs out!")
        self.log("4. Each player gets 2 HINTS (no +5 bonus).")
        self.log("----------------------------")
        self.log(f">> Mode: {case}")
        self.log(">> Board Ready. User Turn.")

    def restart_game(self):
        """Restart the same board configuration"""
        saved_vals = [row[:] for row in self.current_vals]
        
        self.cells = [[Cell(r, c, saved_vals[r][c]) for c in range(self.GRID)] 
                     for r in range(self.GRID)]
        self.dominoes = []
        self.used_pairs = set()
        self.selected = []
        self.user_score = 0
        self.comp_score = 0
        self.game_active = True
        self.current_turn = "User"
        self.time_left = DEFAULT_TIME_LIMIT
        
        self.user_hints_left = DEFAULT_HINTS
        self.comp_hints_left = DEFAULT_HINTS
        self.hinted_move = None
        
        max_val = self.GRID - 1
        self.all_pairs = [(i, j) for i in range(max_val + 1) for j in range(i, max_val + 1)]
        self.pair_status = {pair: "unclaimed" for pair in self.all_pairs}
        
        if self.timer_id: 
            self.root.after_cancel(self.timer_id)
        self.update_timer()
        self.draw_board()
        self.draw_graph()
        self.update_hints_display()
        
        self.log(">> Game Restarted with same board.")

    def update_timer(self):
        """Update game timer"""
        if not self.game_active: 
            return
        self.timer_lbl.config(text=f"Time: {self.time_left}s", 
                            fg=NEON["timer_warn"] if self.time_left <= 10 else NEON["accent"])
        if self.time_left <= 0:
            self.switch_turn()
        else:
            self.time_left -= 1
            self.timer_id = self.root.after(1000, self.update_timer)

    def update_hints_display(self):
        """Update hints label"""
        self.hints_lbl.config(text=f"Hints → User: {self.user_hints_left}/2 | CPU: {self.comp_hints_left}/2")

    def draw_board(self):
        """Draw the game board"""
        result = Renderer.draw_board(self.canvas, self.cells, self.dominoes, self.selected, self.GRID)
        if result:
            self._s, self._ox, self._oy = result

    def draw_graph(self):
        """Draw the graph visualization"""
        Renderer.draw_graph(self.graph_canvas, self.all_pairs, self.used_pairs, 
                          self.dominoes, self.show_edges)

    def handle_click(self, event):
        """Handle mouse click on board"""
        if not self.game_active or self.current_turn != "User": 
            return
        c, r = (event.x - self._ox)//self._s, (event.y - self._oy)//self._s
        if 0 <= r < self.GRID and 0 <= c < self.GRID:
            cell = self.cells[r][c]
            if cell.used: 
                return
            if cell in self.selected: 
                self.selected.remove(cell)
            else: 
                self.selected.append(cell)
            if len(self.selected) == 2:
                a, b = self.selected
                self.selected = []
                if abs(a.r-b.r) + abs(a.c-b.c) == 1:
                    pair = tuple(sorted((a.v, b.v)))
                    if pair not in self.used_pairs:
                        is_hinted = self.hinted_move == (a, b) or self.hinted_move == (b, a)
                        self.place_domino(a, b, "User", is_hinted)
                        self.hinted_move = None
                        self.switch_turn()
                    else: 
                        self.log(f"! Pair {pair} already used.")
                else: 
                    self.log("! Selection must be adjacent.")
        self.draw_board()

    def place_domino(self, a, b, owner, is_hinted=False):
        """Place a domino on the board"""
        a.used = b.used = True
        self.used_pairs.add(tuple(sorted((a.v, b.v))))
        self.dominoes.append({'cells': (a, b), 'owner': owner})
        points = a.v + b.v
        if not is_hinted:
            points += 5
        if owner == "User": 
            self.user_score += points
        else: 
            self.comp_score += points
        self.score_lbl.config(text=f"User: {self.user_score} | CPU: {self.comp_score}")
        bonus_str = "(no bonus)" if is_hinted else "(+5)"
        self.log(f">> {owner} linked {a.v}:{b.v} (+{points} {bonus_str})")
        self.draw_graph()
        if all(cell.used for row in self.cells for cell in row): 
            self.end_game("BOARD CLEARED")

    def switch_turn(self):
        """Switch between players"""
        if not self.game_active: 
            return
        if not GameLogic.has_valid_moves(self.cells, self.GRID, self.used_pairs):
            self.end_game("NO VALID MOVES LEFT")
            return
        self.time_left = DEFAULT_TIME_LIMIT
        self.current_turn = "Comp" if self.current_turn == "User" else "User"
        if self.current_turn == "Comp": 
            self.root.after(1000, self.computer_move)

    def use_hint(self):
        """Show hint for current player"""
        if not self.game_active:
            self.log("! Game is not active.")
            return
        
        if self.current_turn == "User":
            if self.user_hints_left <= 0:
                self.log("! User: No hints left!")
                messagebox.showwarning("No Hints", "You've used all your hints!")
                return
            self.user_hints_left -= 1
        else:
            if self.comp_hints_left <= 0:
                self.log("! CPU: No hints left!")
                return
            self.comp_hints_left -= 1
        
        moves = GameLogic.find_all_valid_moves(self.cells, self.GRID, self.used_pairs)
        
        if not moves:
            self.log("! No valid moves available.")
            return
        
        best_sum, cell_a, cell_b = moves[0]
        
        self.log(f"💡 {self.current_turn} HINT: Link {cell_a.v} & {cell_b.v} (sum={best_sum})")
        self.log(f"   Cells: ({cell_a.r},{cell_a.c}) + ({cell_b.r},{cell_b.c})")
        
        if self.current_turn == "User":
            self.hinted_move = (cell_a, cell_b)
            self.log("   ▶ Click the cells to claim this move!")
        
        self.update_hints_display()

    def solve_logic(self):
        """Use AI solver to complete the puzzle"""
        if not self.game_active: 
            return
        self.log("🤖 AI Solver: Finding unique path...")
        curr_used_cells = {(c.r, c.c) for row in self.cells for c in row if c.used}
        grid_vals = [[c.v for c in row] for row in self.cells]
        
        solution = GameLogic.backtrack(0, self.GRID, grid_vals, curr_used_cells, self.used_pairs.copy())
        if solution:
            for (r1, c1), (r2, c2) in solution:
                self.place_domino(self.cells[r1][c1], self.cells[r2][c2], "Comp")
            self.draw_board()
            self.draw_graph()
            self.log("✅ AI solved the puzzle!")
        else:
            self.log("❌ No solution from this state.")
            messagebox.showwarning("No Solution", "No valid path exists for this board.")

    def end_game(self, reason):
        """End the game and show results"""
        self.game_active = False
        if self.timer_id: 
            self.root.after_cancel(self.timer_id)
        winner = ("USER WINS!" if self.user_score > self.comp_score else 
                 "CPU WINS!" if self.comp_score > self.user_score else "DRAW!")
        self.log("-" * 25)
        self.log(f"GAME OVER: {reason}")
        self.log(f"User: {self.user_score} | CPU: {self.comp_score}")
        self.log(f"RESULT: {winner}")
        self.log("-" * 25)
        messagebox.showinfo("Match Result", 
                          f"{winner}\n\nUser: {self.user_score}\nCPU: {self.comp_score}")

    def computer_move(self):
        """Execute computer's move"""
        move = GameLogic.computer_move(self.cells, self.GRID, self.used_pairs)
        if move:
            a, b = move
            self.place_domino(a, b, "Comp")
            self.draw_board()
        self.switch_turn()

    def toggle_edges(self):
        """Toggle graph edge visibility"""
        self.show_edges = not self.show_edges
        self.edge_toggle_btn.config(text="🔗 Hide Edges" if self.show_edges else "🔗 Show Edges")
        self.draw_graph()


if __name__ == "__main__":
    root = tk.Tk()
    app = DominosaGUI(root)
    root.mainloop()