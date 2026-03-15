import random
from models import Cell


class GameLogic:

    DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    SIMPLE_DIRECTIONS = [(0, 1), (1, 0)]

    # --------------------------------------------------
    # BOARD GENERATION
    # --------------------------------------------------
    @staticmethod
    def generate_valid_board(n):
        max_attempts = 100

        for _ in range(max_attempts):
            board = [[-1 for _ in range(n)] for _ in range(n)]
            used_pairs = set()
            max_val = n - 1

            available_pairs = [(i, j)
                               for i in range(max_val + 1)
                               for j in range(i, max_val + 1)]
            random.shuffle(available_pairs)

            idx = 0
            success = True

            while idx < n * n:
                r, c = divmod(idx, n)
                if board[r][c] != -1:
                    idx += 1
                    continue

                placed = False
                dirs = GameLogic.SIMPLE_DIRECTIONS[:]
                random.shuffle(dirs)

                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if nr < n and nc < n and board[nr][nc] == -1:
                        for pair in available_pairs:
                            if pair not in used_pairs:
                                board[r][c], board[nr][nc] = pair
                                used_pairs.add(pair)
                                available_pairs.remove(pair)
                                placed = True
                                break
                        if placed:
                            break

                if not placed:
                    success = False
                    break

                idx += 1

            if success:
                return board

        return None

    # --------------------------------------------------
    # VALID MOVE GENERATION (Component-aware)
    # --------------------------------------------------
    @staticmethod
    def _get_valid_moves(cells, grid_size, used_pairs,
                         skip_cells=None, allowed_cells=None):

        if skip_cells is None:
            skip_cells = set()

        moves = []

        for r in range(grid_size):
            for c in range(grid_size):

                if cells[r][c].used or (r, c) in skip_cells:
                    continue

                if allowed_cells is not None and (r, c) not in allowed_cells:
                    continue

                for dr, dc in GameLogic.SIMPLE_DIRECTIONS:
                    nr, nc = r + dr, c + dc

                    if (nr < grid_size and nc < grid_size and
                        not cells[nr][nc].used and
                        (nr, nc) not in skip_cells):

                        if allowed_cells is not None and (nr, nc) not in allowed_cells:
                            continue

                        pair = tuple(sorted((cells[r][c].v,
                                             cells[nr][nc].v)))

                        if pair not in used_pairs:
                            move_sum = cells[r][c].v + cells[nr][nc].v
                            moves.append((cells[r][c],
                                          cells[nr][nc],
                                          pair,
                                          move_sum))

        return moves

    # --------------------------------------------------
    # MERGE SORT (D&C)
    # --------------------------------------------------
    @staticmethod
    def merge_sort_moves(moves):
        if len(moves) <= 1:
            return moves

        mid = len(moves) // 2
        left = GameLogic.merge_sort_moves(moves[:mid])
        right = GameLogic.merge_sort_moves(moves[mid:])

        return GameLogic._merge(left, right)

    @staticmethod
    def _merge(left, right):
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            if left[i][3] >= right[j][3]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])
        return result

    # --------------------------------------------------
    # STATUS CHECK
    # --------------------------------------------------
    @staticmethod
    def has_valid_moves(cells, grid_size, used_pairs):
        return len(GameLogic._get_valid_moves(cells, grid_size, used_pairs)) > 0

    @staticmethod
    def find_all_valid_moves(cells, grid_size, used_pairs):
        moves = GameLogic._get_valid_moves(cells, grid_size, used_pairs)
        moves = GameLogic.merge_sort_moves(moves)
        return [(m[3], m[0], m[1]) for m in moves]

    # --------------------------------------------------
    # COMPUTER MOVE (D&C + LOOKAHEAD)
    # --------------------------------------------------
    @staticmethod
    def computer_move(cells, grid_size, used_pairs):

        components = GameLogic.divide_into_components(cells, grid_size)
        if not components:
            return None

        components.sort(key=len)
        target_component = set(components[0])

        moves = GameLogic._get_valid_moves(
            cells, grid_size, used_pairs,
            allowed_cells=target_component
        )

        if not moves:
            return None

        moves = GameLogic.merge_sort_moves(moves)

        best_move = None
        max_future = -1

        for cell_a, cell_b, pair, _ in moves:
            skip = {(cell_a.r, cell_a.c), (cell_b.r, cell_b.c)}

            future = GameLogic._get_valid_moves(
                cells,
                grid_size,
                used_pairs | {pair},
                skip_cells=skip,
                allowed_cells=target_component
            )

            if len(future) > max_future:
                max_future = len(future)
                best_move = (cell_a, cell_b)

        return best_move

    # --------------------------------------------------
    # BOARD SPLITTING (D&C)
    # --------------------------------------------------
    @staticmethod
    def divide_into_components(cells, grid_size):
        visited = set()
        components = []

        def dfs(r, c, comp):
            if (r, c) in visited or cells[r][c].used:
                return
            visited.add((r, c))
            comp.append((r, c))
            for dr, dc in GameLogic.DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid_size and 0 <= nc < grid_size:
                    dfs(nr, nc, comp)

        for r in range(grid_size):
            for c in range(grid_size):
                if not cells[r][c].used and (r, c) not in visited:
                    comp = []
                    dfs(r, c, comp)
                    components.append(comp)

        return components

    # --------------------------------------------------
    # BACKTRACKING SOLVER
    # --------------------------------------------------
    @staticmethod
    def backtrack(idx, grid_size, grid, used_c, used_p, moves_so_far=None):

        if moves_so_far is None:
            moves_so_far = []

        if idx == grid_size * grid_size:
            return moves_so_far

        r, c = divmod(idx, grid_size)

        if (r, c) in used_c:
            return GameLogic.backtrack(
                idx + 1, grid_size,
                grid, used_c, used_p, moves_so_far
            )

        dirs = GameLogic.DIRECTIONS[:]
        random.shuffle(dirs)

        for dr, dc in dirs:
            nr, nc = r + dr, c + dc

            if (0 <= nr < grid_size and 0 <= nc < grid_size and
                (nr, nc) not in used_c):

                pair = tuple(sorted((grid[r][c], grid[nr][nc])))

                if pair not in used_p:
                    result = GameLogic.backtrack(
                        idx + 1,
                        grid_size,
                        grid,
                        used_c | {(r, c), (nr, nc)},
                        used_p | {pair},
                        moves_so_far + [((r, c), (nr, nc))]
                    )

                    if result is not None:
                        return result

        return None
