import sys

def diag1_index(i, j, n):
    return i - j + (n - 1)

def diag2_index(i, j, n):
    return i + j

def solve(n, col_sums, row_sums, diag1_sums, diag2_sums):
    dcount = 2 * n - 1

    # Anzahl noch freier Felder in Zeilen/Spalten/Diagonalen
    rows_free = [n] * n
    cols_free = [n] * n
    d1_free = [0] * dcount
    d2_free = [0] * dcount

    # Länge jeder Diagonale zählen
    for i in range(n):
        for j in range(n):
            d1_free[diag1_index(i, j, n)] += 1
            d2_free[diag2_index(i, j, n)] += 1

    # Noch zu platzierende Einsen
    rows_left = row_sums[:]
    cols_left = col_sums[:]
    d1_left = diag1_sums[:]
    d2_left = diag2_sums[:]

    # Gitter: None = ungesetzt, 0 oder 1 = gesetzt
    grid = [[None] * n for _ in range(n)]

    # Möglichkeiten-Masken (bit 0 -> 0 möglich, bit 1 -> 1 möglich)
    possibilities = [[0] * n for _ in range(n)]

    solutions = 0
    example_solution = None
    found_one = False  # nach erstem Treffer stoppen (sonst explodiert's)
    step_limit = 1500000
    steps = 0

    def check_bounds():
        # schnelle Plausibilitätsgrenzen
        for i in range(n):
            if rows_left[i] < 0 or rows_left[i] > rows_free[i]:
                return False
        for j in range(n):
            if cols_left[j] < 0 or cols_left[j] > cols_free[j]:
                return False
        for d in range(dcount):
            if d1_left[d] < 0 or d1_left[d] > d1_free[d]:
                return False
            if d2_left[d] < 0 or d2_left[d] > d2_free[d]:
                return False
        return True

    def is_complete():
        for i in range(n):
            for j in range(n):
                if grid[i][j] is None:
                    return False
        return True

    def allow_vals(i, j):
        d1 = diag1_index(i, j, n)
        d2 = diag2_index(i, j, n)
        a1 = rows_left[i] > 0 and cols_left[j] > 0 and d1_left[d1] > 0 and d2_left[d2] > 0
        a0 = rows_left[i] < rows_free[i] and cols_left[j] < cols_free[j] and d1_left[d1] < d1_free[d1] and d2_left[d2] < d2_free[d2]
        return a0, a1

    def choose_cell():
        # MRV-ähnlich: Zelle mit kleinster Domäne (0/1) wählen
        best = None
        best_dom = 3  # größer als max 2
        best_score = None
        for i in range(n):
            for j in range(n):
                if grid[i][j] is not None:
                    continue
                a0, a1 = allow_vals(i, j)
                dom = (1 if a0 else 0) + (1 if a1 else 0)
                if dom == 0:
                    return (i, j), 0  # sofortiger Widerspruch
                d1 = diag1_index(i, j, n)
                d2 = diag2_index(i, j, n)
                score = rows_free[i] + cols_free[j] + d1_free[d1] + d2_free[d2]
                if dom < best_dom or (dom == best_dom and (best_score is None or score < best_score)):
                    best = (i, j)
                    best_dom = dom
                    best_score = score
                    if best_dom == 1:
                        # ideal, direkt nehmen
                        pass
        return best, best_dom

    def set_cell(i, j, val, log):
        # versucht, Zelle zu setzen; gibt False bei Konflikt
        if grid[i][j] is not None:
            return grid[i][j] == val
        d1 = diag1_index(i, j, n)
        d2 = diag2_index(i, j, n)
        if val == 1:
            if rows_left[i] == 0 or cols_left[j] == 0 or d1_left[d1] == 0 or d2_left[d2] == 0:
                return False
        else:
            if rows_left[i] == rows_free[i] or cols_left[j] == cols_free[j] or d1_left[d1] == d1_free[d1] or d2_left[d2] == d2_free[d2]:
                return False
        grid[i][j] = val
        rows_free[i] -= 1
        cols_free[j] -= 1
        d1_free[d1] -= 1
        d2_free[d2] -= 1
        if val == 1:
            rows_left[i] -= 1
            cols_left[j] -= 1
            d1_left[d1] -= 1
            d2_left[d2] -= 1
        log.append((i, j, val))
        return True

    def undo(log, upto):
        # Änderungen zurücknehmen bis Länge 'upto'
        while len(log) > upto:
            i, j, val = log.pop()
            d1 = diag1_index(i, j, n)
            d2 = diag2_index(i, j, n)
            if val == 1:
                rows_left[i] += 1
                cols_left[j] += 1
                d1_left[d1] += 1
                d2_left[d2] += 1
            rows_free[i] += 1
            cols_free[j] += 1
            d1_free[d1] += 1
            d2_free[d2] += 1
            grid[i][j] = None

    def propagate(log):
        # erzwungene Werte iterativ setzen
        changed = True
        while changed:
            if not check_bounds():
                return False
            changed = False
            # Zeilen
            for i in range(n):
                if rows_free[i] == 0:
                    continue
                if rows_left[i] == 0:
                    for j in range(n):
                        if grid[i][j] is None:
                            if not set_cell(i, j, 0, log):
                                return False
                            changed = True
                elif rows_left[i] == rows_free[i]:
                    for j in range(n):
                        if grid[i][j] is None:
                            if not set_cell(i, j, 1, log):
                                return False
                            changed = True
                else:
                    # zusätzliche Schranken mit Domänen
                    can1 = 0
                    must1 = 0
                    cells = []
                    for j in range(n):
                        if grid[i][j] is None:
                            a0, a1 = allow_vals(i, j)
                            cells.append((j, a0, a1))
                            if a1:
                                can1 += 1
                            if not a0 and a1:
                                must1 += 1
                    if rows_left[i] > can1:
                        return False
                    if rows_left[i] == must1:
                        # alle anderen werden 0
                        for j, a0, a1 in cells:
                            if a0 and a1:
                                if not set_cell(i, j, 0, log):
                                    return False
                                changed = True
                    if rows_left[i] == can1:
                        # alle die 1 können, müssen 1 sein
                        for j, a0, a1 in cells:
                            if a1 and grid[i][j] is None:
                                if not set_cell(i, j, 1, log):
                                    return False
                                changed = True
            # Spalten
            for j in range(n):
                if cols_free[j] == 0:
                    continue
                if cols_left[j] == 0:
                    for i in range(n):
                        if grid[i][j] is None:
                            if not set_cell(i, j, 0, log):
                                return False
                            changed = True
                elif cols_left[j] == cols_free[j]:
                    for i in range(n):
                        if grid[i][j] is None:
                            if not set_cell(i, j, 1, log):
                                return False
                            changed = True
                else:
                    can1 = 0
                    must1 = 0
                    cells = []
                    for i in range(n):
                        if grid[i][j] is None:
                            a0, a1 = allow_vals(i, j)
                            cells.append((i, a0, a1))
                            if a1:
                                can1 += 1
                            if not a0 and a1:
                                must1 += 1
                    if cols_left[j] > can1:
                        return False
                    if cols_left[j] == must1:
                        for i, a0, a1 in cells:
                            if a0 and a1:
                                if not set_cell(i, j, 0, log):
                                    return False
                                changed = True
                    if cols_left[j] == can1:
                        for i, a0, a1 in cells:
                            if a1 and grid[i][j] is None:
                                if not set_cell(i, j, 1, log):
                                    return False
                                changed = True
            # Diagonalen 1
            for d in range(dcount):
                if d1_free[d] == 0:
                    continue
                if d1_left[d] == 0 or d1_left[d] == d1_free[d]:
                    want = 0 if d1_left[d] == 0 else 1
                    for i in range(n):
                        j = i - (d - (n - 1))
                        if 0 <= j < n and grid[i][j] is None:
                            if not set_cell(i, j, want, log):
                                return False
                            changed = True
                else:
                    can1 = 0
                    must1 = 0
                    cells = []
                    for i in range(n):
                        j = i - (d - (n - 1))
                        if 0 <= j < n and grid[i][j] is None:
                            a0, a1 = allow_vals(i, j)
                            cells.append((i, j, a0, a1))
                            if a1:
                                can1 += 1
                            if not a0 and a1:
                                must1 += 1
                    if d1_left[d] > can1:
                        return False
                    if d1_left[d] == must1:
                        for i, j, a0, a1 in cells:
                            if a0 and a1:
                                if not set_cell(i, j, 0, log):
                                    return False
                                changed = True
                    if d1_left[d] == can1:
                        for i, j, a0, a1 in cells:
                            if a1 and grid[i][j] is None:
                                if not set_cell(i, j, 1, log):
                                    return False
                                changed = True
            # Diagonalen 2
            for d in range(dcount):
                if d2_free[d] == 0:
                    continue
                if d2_left[d] == 0 or d2_left[d] == d2_free[d]:
                    want = 0 if d2_left[d] == 0 else 1
                    for i in range(n):
                        j = d - i
                        if 0 <= j < n and grid[i][j] is None:
                            if not set_cell(i, j, want, log):
                                return False
                            changed = True
                else:
                    can1 = 0
                    must1 = 0
                    cells = []
                    for i in range(n):
                        j = d - i
                        if 0 <= j < n and grid[i][j] is None:
                            a0, a1 = allow_vals(i, j)
                            cells.append((i, j, a0, a1))
                            if a1:
                                can1 += 1
                            if not a0 and a1:
                                must1 += 1
                    if d2_left[d] > can1:
                        return False
                    if d2_left[d] == must1:
                        for i, j, a0, a1 in cells:
                            if a0 and a1:
                                if not set_cell(i, j, 0, log):
                                    return False
                                changed = True
                    if d2_left[d] == can1:
                        for i, j, a0, a1 in cells:
                            if a1 and grid[i][j] is None:
                                if not set_cell(i, j, 1, log):
                                    return False
                                changed = True
        return True

    log = []

    def backtrack():
        nonlocal solutions, example_solution
        nonlocal found_one, steps
        if found_one:
            return
        steps += 1
        if steps > step_limit:
            return
        if not check_bounds():
            return

        base = len(log)
        if not propagate(log):
            undo(log, base)
            return

        if is_complete():
            if (all(x == 0 for x in rows_left) and
                all(x == 0 for x in cols_left) and
                all(x == 0 for x in d1_left) and
                all(x == 0 for x in d2_left)):
                solutions += 1
                for i in range(n):
                    for j in range(n):
                        v = grid[i][j]
                        if v == 0:
                            possibilities[i][j] |= 0b01
                        else:
                            possibilities[i][j] |= 0b10
                if example_solution is None:
                    example_solution = [row[:] for row in grid]
                # nach erster Lösung beenden
                found_one = True
        else:
            (i, j), dom = choose_cell()
            if dom == 0:
                undo(log, base)
                return
            a0, a1 = allow_vals(i, j)
            # einfache Reihenfolge: 1 zuerst wenn erlaubt
            order = []
            if a1:
                order.append(1)
            if a0:
                order.append(0)
            for val in order:
                if set_cell(i, j, val, log):
                    backtrack()
                    undo(log, len(log) - 1)
                else:
                    continue

        undo(log, base)

    backtrack()
    return possibilities, example_solution, solutions

def main():
    if len(sys.argv) != 2:
        print("Aufruf: python3 script.py input.txt")
        return

    filename = sys.argv[1]

    try:
        with open(filename, "r", encoding="utf-8") as f:
            raw = f.read().strip().split()
    except:
        print("Fehler beim Lesen der Datei.")
        return

    if not raw:
        print("Die Datei enthält keine Daten.")
        return

    idx = 0
    n = int(raw[idx]); idx += 1

    col_sums = list(map(int, raw[idx:idx+n])); idx += n
    row_sums = list(map(int, raw[idx:idx+n])); idx += n

    dcount = 2*n - 1

    if len(raw) < idx + 2*dcount:
        print("Zu wenige Werte in der Datei.")
        return

    diagA = list(map(int, raw[idx:idx+dcount])); idx += dcount
    diagB = list(map(int, raw[idx:idx+dcount])); idx += dcount

    # kleine Plausibilitätsprüfung der Summen
    total = sum(row_sums)
    if sum(col_sums) != total or sum(diagA) != total or sum(diagB) != total:
        print("Keine Figur gefunden, die zu den Summen passt.")
        return

    variants = [
        (diagA, diagB),
        (diagA[::-1], diagB),
        (diagA, diagB[::-1]),
        (diagA[::-1], diagB[::-1]),
        (diagB, diagA),
        (diagB[::-1], diagA),
        (diagB, diagA[::-1]),
        (diagB[::-1], diagA[::-1])
    ]

    possibilities = None
    example = None
    found = 0

    for d1, d2 in variants:
        possibilities, example, found = solve(n, col_sums, row_sums, d1, d2)
        if found > 0:
            break

    if found == 0:
        print("Keine Figur gefunden, die zu den Summen passt.")
        return

    for i in range(n):
        line = []
        for j in range(n):
            mask = possibilities[i][j]
            if mask == 0b10:
                line.append("X")
            elif mask == 0b01:
                line.append(".")
            elif mask == 0b11:
                line.append("?")
            else:
                line.append("?")
        print("".join(line))

if __name__ == "__main__":
    main()
