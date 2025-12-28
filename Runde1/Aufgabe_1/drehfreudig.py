#!/usr/bin/env python3
from fractions import Fraction
import sys
from pathlib import Path

# Einlesen und Parsen des Baums
def parse_tree_brackets(s: str):
    s = ''.join(c for c in s if c in '()')
    children = []
    parent = []
    stack = []

    for c in s:
        if c == '(':
            node = len(children)
            children.append([])
            parent.append(None)
            if stack:
                p = stack[-1]
                children[p].append(node)
                parent[node] = p
            stack.append(node)
        elif c == ')':
            if not stack:
                print("Zu viele schließende Klammern.")
            stack.pop()
    if not children:
        print("Leerer Baum.")

    root = 0
    return root, children

# Rechteck-Intervalle und Drehfreudigkeit
def compute_intervals(root, children):
    intervals = {}  # node -> (start, width, depth)
    max_depth = 0

    def dfs(u, start, width, depth):
        nonlocal max_depth
        intervals[u] = (start, width, depth)
        max_depth = max(max_depth, depth)
        k = len(children[u])
        if k:
            child_width = width / k
            x = start
            for v in children[u]:
                dfs(v, x, child_width, depth + 1)
                x += child_width

    dfs(root, Fraction(0, 1), Fraction(1, 1), 0)
    return intervals, max_depth


def is_drehfreudig(children, intervals) -> bool:
    leaves = [u for u in range(len(children)) if not children[u]]
    segs = sorted((intervals[u][0], intervals[u][1]) for u in leaves)
    mirrored = sorted(
        (Fraction(1, 1) - (s + w), w)
        for (s, w) in segs
    )
    return segs == mirrored

# SVG-Erzeugung
def generate_svg(children, intervals, max_depth,
                 width_px=800, level_px=70,
                 margin_x=40, margin_y=40) -> str:
    n = len(children)

    x_top = {}
    y_top = {}
    x_bottom = {}
    y_bottom = {}

    W = width_px
    Ymid = margin_y + max_depth * level_px
    width_total = margin_x * 2 + W
    height_total = margin_y * 2 + 2 * max_depth * level_px

    # Positionen berechnen
    for u, (start, width, depth) in intervals.items():
        x_frac = start + width / 2
        x_t = margin_x + float(x_frac) * W
        y_t = Ymid - (max_depth - depth) * level_px

        # 180°-Drehung um die Mitte (horizontal spiegeln + vertikal spiegeln)
        x_b = margin_x + (1.0 - float(x_frac)) * W
        y_b = 2 * Ymid - y_t

        x_top[u], y_top[u] = x_t, y_t
        x_bottom[u], y_bottom[u] = x_b, y_b

    node_r = 6
    edge_color = "#34495e"
    node_fill = "#e91e63"
    node_stroke = "#2c3e50"
    midline_color = "#cccccc"

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width_total}" height="{height_total}" '
        f'viewBox="0 0 {width_total} {height_total}">'
    )
    parts.append('<rect x="0" y="0" width="100%" height="100%" fill="white"/>')

    # Mittellinie (Blattebene)
    parts.append(
        f'<line x1="0" y1="{Ymid}" x2="{width_total}" y2="{Ymid}" '
        f'stroke="{midline_color}" stroke-width="1" stroke-dasharray="4 4"/>'
    )

    # Kanten (oben und unten)
    for u in range(n):
        for v in children[u]:
            parts.append(
                f'<line x1="{x_top[u]:.2f}" y1="{y_top[u]:.2f}" '
                f'x2="{x_top[v]:.2f}" y2="{y_top[v]:.2f}" '
                f'stroke="{edge_color}" stroke-width="2"/>'
            )
            parts.append(
                f'<line x1="{x_bottom[u]:.2f}" y1="{y_bottom[u]:.2f}" '
                f'x2="{x_bottom[v]:.2f}" y2="{y_bottom[v]:.2f}" '
                f'stroke="{edge_color}" stroke-width="2"/>'
            )

    # Knoten (oben und unten)
    for u in range(n):
        parts.append(
            f'<circle cx="{x_top[u]:.2f}" cy="{y_top[u]:.2f}" r="{node_r}" '
            f'fill="{node_fill}" stroke="{node_stroke}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<circle cx="{x_bottom[u]:.2f}" cy="{y_bottom[u]:.2f}" r="{node_r}" '
            f'fill="{node_fill}" stroke="{node_stroke}" stroke-width="1.5"/>'
        )

    parts.append('</svg>')
    return "\n".join(parts)

# main
def main():
    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        text = None
        p = Path(arg)
        if p.exists():
            text = p.read_text(encoding="utf-8")
        else:
            text = arg
    else:
        text = sys.stdin.read()

    text = text.strip()
    if not text:
        print("Keine Eingabe.")
        return

    root, children = parse_tree_brackets(text)
    intervals, max_depth = compute_intervals(root, children)
    dreh = is_drehfreudig(children, intervals)

    if dreh:
        print("Der Baum ist drehfreudig.")
        svg = generate_svg(children, intervals, max_depth)
        number = ''.join(ch for ch in sys.argv[1] if ch.isdigit())
        if not number:
            number = '0'
        out_name = "baum-" + number + ".svg"
        Path(out_name).write_text(svg, encoding="utf-8")
        print(f"SVG wurde in '{out_name}' gespeichert.")
    else:
        print("Der Baum ist nicht drehfreudig.")

if __name__ == "__main__":
    main()
