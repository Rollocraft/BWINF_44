#!/usr/bin/env python3
import sys
import math

EPS = 1e-9

def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])

def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def orientation(a, b, c):
    # >0: linksdrehend, <0: rechtsdrehend, 0: kollinear
    return cross(sub(b, a), sub(c, a))

def on_segment(a, b, p):
    # liegt p auf dem Segment [a,b]?
    if abs(orientation(a, b, p)) > EPS:
        return False
    return (min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and
            min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)

def segments_intersect(a, b, c, d):
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)

    # kollineare Sonderfälle
    if abs(o1) < EPS and on_segment(a, b, c):
        return True
    if abs(o2) < EPS and on_segment(a, b, d):
        return True
    if abs(o3) < EPS and on_segment(c, d, a):
        return True
    if abs(o4) < EPS and on_segment(c, d, b):
        return True

    # allgemeiner Fall
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)

def dist_point_segment(p, a, b):
    # Abstand eines Punktes p zum Segment [a,b]
    ab = sub(b, a)
    ap = sub(p, a)
    ab2 = dot(ab, ab)
    if ab2 < EPS:
        # a und b sind fast gleich
        return dist(p, a)
    t = dot(ap, ab) / ab2
    if t < 0:
        return dist(p, a)
    elif t > 1:
        return dist(p, b)
    proj = (a[0] + t * ab[0], a[1] + t * ab[1])
    return dist(p, proj)

def segment_segment_distance(a, b, c, d):
    # Abstand zweier Segmente, falls sie sich nicht schneiden
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(
        dist_point_segment(a, c, d),
        dist_point_segment(b, c, d),
        dist_point_segment(c, a, b),
        dist_point_segment(d, a, b)
    )

def point_in_polygon(p, poly):
    # Ray-Casting: True, wenn Punkt im (oder auf dem) Polygon liegt
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]

        # Punkt auf Kante?
        if on_segment((x1, y1), (x2, y2), p):
            return True

        # Strahl nach rechts: schneidet er die Kante?
        if (y1 > y) != (y2 > y):
            x_int = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x_int > x:
                inside = not inside
    return inside


def compute_max_leash_length(segments, lakes):
    if not lakes:
        # ohne Seen wäre die Leine theoretisch unendlich lang
        return float("inf")

    best = float("inf")

    for a, b in segments:
        for poly in lakes:
            n = len(poly)

            # Endpunkte See?
            if point_in_polygon(a, poly) or point_in_polygon(b, poly):
                return 0.0

            for i in range(n):
                c = poly[i]
                d = poly[(i + 1) % n]

                # Schnitt Polygonkante?
                if segments_intersect(a, b, c, d):
                    return 0.0

                # Abstand Segment–Segment
                d_seg = segment_segment_distance(a, b, c, d)
                if d_seg < best:
                    best = d_seg
    return best


def read_input_from_string(s):
    data = s.split()
    it = iter(data)

    try:
        n_segments = int(next(it))
    except StopIteration:
        print("Fehler: Ungültige Eingabe.", file=sys.stderr)

    segments = []
    for _ in range(n_segments):
        x1 = float(next(it)); y1 = float(next(it))
        x2 = float(next(it)); y2 = float(next(it))
        segments.append(((x1, y1), (x2, y2)))

    n_lakes = int(next(it))
    lakes = []
    for _ in range(n_lakes):
        k = int(next(it))
        poly = []
        for _ in range(k):
            x = float(next(it)); y = float(next(it))
            poly.append((x, y))
        lakes.append(poly)

    return segments, lakes


def main():
    if len(sys.argv) >= 2:
        fname = sys.argv[1]
    else:
        fname = 'input.txt'

    if fname == '-':
        s = sys.stdin.read()
    else:
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                s = f.read()
        except FileNotFoundError:
            print(f"Eingabedatei '{fname}' nicht gefunden.", file=sys.stderr)
            sys.exit(1)

    try:
        segments, lakes = read_input_from_string(s)
    except Exception as e:
        print(f"Fehler beim Einlesen der Eingabe: {e}", file=sys.stderr)
        sys.exit(1)

    result = compute_max_leash_length(segments, lakes)

    # Ausgabe mit 6 Nachkommastellen
    # Bei unendlicher Leine wird 'inf' ausgegeben
    if math.isinf(result):
        print("inf")
    else:
        print(f"{result:.6f}")

if __name__ == "__main__":
    main()
