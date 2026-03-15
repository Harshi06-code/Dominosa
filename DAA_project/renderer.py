# renderer.py
"""Rendering functions for board and graph visualization"""
import math
from constants import NEON


class Renderer:
    """Handles all drawing operations"""
    
    @staticmethod
    def draw_board(canvas, cells, dominoes, selected, grid_size):
        """Draw the game board"""
        canvas.delete("all")
        n, W, H = grid_size, canvas.winfo_width(), canvas.winfo_height()
        s = min(W, H) // (n + 1)
        ox, oy = (W - s*n)//2, (H - s*n)//2

        # Draw grid cells
        for r in range(n):
            for c in range(n):
                x1, y1 = ox + c*s, oy + r*s
                canvas.create_rectangle(x1, y1, x1+s, y1+s, outline=NEON["grid_border"], fill=NEON["grid_fill"])

        # Draw placed dominoes
        for d in dominoes:
            c1, c2 = d['cells']
            x1, y1 = ox + min(c1.c, c2.c)*s, oy + min(c1.r, c2.r)*s
            x2, y2 = ox + (max(c1.c, c2.c)+1)*s, oy + (max(c1.r, c2.r)+1)*s
            color = NEON["user_domino"] if d['owner'] == "User" else NEON["comp_domino"]
            canvas.create_rectangle(x1+4, y1+4, x2-4, y2-4, fill=color, outline="white", width=2)

        # Draw cell values
        for r in range(n):
            for c in range(n):
                cell = cells[r][c]
                x1, y1 = ox + c*s, oy + r*s
                canvas.create_text(x1+s/2, y1+s/2, text=str(cell.v), 
                                 fill="white" if cell.used else NEON["text"], 
                                 font=("Segoe UI", int(s*0.3), "bold"))

        # Draw selection highlights
        for sel in selected:
            x1, y1 = ox + sel.c*s, oy + sel.r*s
            canvas.create_rectangle(x1+2, y1+2, x1+s-2, y1+s-2, outline="yellow", width=3)
        
        return s, ox, oy
    
    @staticmethod
    def draw_graph(canvas, all_pairs, used_pairs, dominoes, show_edges):
        """Draw the graph representation of domino pairs"""
        canvas.delete("all")
        
        W = canvas.winfo_width()
        H = canvas.winfo_height()
        
        if W <= 1 or H <= 1:
            return
        
        # Center and radius for circular layout
        cx, cy = W // 2, H // 2
        radius = min(W, H) // 2.5
        
        # Calculate positions for each pair node
        num_pairs = len(all_pairs)
        node_positions = {}
        
        for i, pair in enumerate(all_pairs):
            angle = 2 * math.pi * i / num_pairs - math.pi / 2
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            node_positions[pair] = (x, y)
        
        # Draw edges between pairs that share a number
        if show_edges:
            for i, pair1 in enumerate(all_pairs):
                for pair2 in all_pairs[i+1:]:
                    if pair1[0] in pair2 or pair1[1] in pair2:
                        x1, y1 = node_positions[pair1]
                        x2, y2 = node_positions[pair2]
                        canvas.create_line(x1, y1, x2, y2, fill=NEON["graph_edge"], width=1)
        
        # Draw nodes
        node_radius = 25 if num_pairs <= 15 else 22
        
        for pair in all_pairs:
            x, y = node_positions[pair]
            
            # Determine node color based on status
            if pair in used_pairs:
                owner = None
                for d in dominoes:
                    c1, c2 = d['cells']
                    domino_pair = tuple(sorted((c1.v, c2.v)))
                    if domino_pair == pair:
                        owner = d['owner']
                        break
                color = NEON["user_domino"] if owner == "User" else NEON["comp_domino"]
            else:
                color = NEON["graph_unclaimed"]
            
            # Draw node circle
            canvas.create_oval(
                x - node_radius, y - node_radius,
                x + node_radius, y + node_radius,
                fill=color, outline="white", width=2
            )
            
            # Draw pair label
            label = f"{pair[0]}-{pair[1]}"
            canvas.create_text(
                x, y, text=label, fill="white",
                font=("Consolas", 9 if num_pairs > 15 else 11, "bold")
            )
        
        # Add legend
        legend_y = 20
        canvas.create_text(20, legend_y, text="Legend:", fill=NEON["text"], anchor="w", font=("Consolas", 9, "bold"))
        
        canvas.create_oval(20, legend_y + 20, 35, legend_y + 35, fill=NEON["user_domino"], outline="white")
        canvas.create_text(45, legend_y + 27, text="User", fill=NEON["text"], anchor="w", font=("Consolas", 8))
        
        canvas.create_oval(20, legend_y + 45, 35, legend_y + 60, fill=NEON["comp_domino"], outline="white")
        canvas.create_text(45, legend_y + 52, text="CPU", fill=NEON["text"], anchor="w", font=("Consolas", 8))
        
        canvas.create_oval(20, legend_y + 70, 35, legend_y + 85, fill=NEON["graph_unclaimed"], outline="white")
        canvas.create_text(45, legend_y + 77, text="Available", fill=NEON["text"], anchor="w", font=("Consolas", 8))