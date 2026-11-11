"""Build and replay a guillotine cutting plan from rectangular placements.

Each cut spans its current parent rectangle, and its kerf is removed. This is a
geometrical plan, not an instruction for a particular machine or its clamping.
"""

from decimal import Decimal


class SequenceUnavailable(ValueError):
    pass


def _d(value):
    # Placement coordinates come from floating-point arithmetic. Normalize
    # sub-micron rounding noise before comparing adjacent saw kerfs.
    return Decimal(str(value)).quantize(Decimal("0.000001"))


def build_cut_sequence(result: dict) -> list[dict]:
    """Return numbered steps or raise if a full, verified slicing plan is unavailable."""
    width = _d(result["sheet_size_mm"]["width"])
    height = _d(result["sheet_size_mm"]["height"])
    kerf = _d(result["blade_kerf_mm"])
    if width <= 0 or height <= 0 or kerf <= 0:
        raise SequenceUnavailable("La placa y el ancho de sierra deben ser positivos")
    plans = []
    for sheet in result["sheets"]:
        pieces = []
        for p in sheet["pieces"]:
            x, y, w, h = (_d(p[k]) for k in ("x", "y", "width", "height"))
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > width or y+h > height:
                raise SequenceUnavailable("Una pieza está fuera del tablero")
            pieces.append({"id": p["id"], "x": x, "y": y, "w": w, "h": h})
        if not pieces or len({p["id"] for p in pieces}) != len(pieces):
            raise SequenceUnavailable("No hay piezas o hay identificadores repetidos")
        budget = [10000]
        plan = _split((Decimal(0), Decimal(0), width, height), pieces, kerf, budget)
        if plan is None:
            raise SequenceUnavailable("No se pudo demostrar una secuencia guillotina para esta distribución")
        steps, finals = plan
        for i, step in enumerate(steps, 1):
            step["numero"] = i
        _verify((Decimal(0), Decimal(0), width, height), pieces, kerf, steps, finals)
        plans.append({"sheet_number": sheet["sheet_number"], "cuts": steps,
                      "pieces": [{"id": p["id"], "rect_mm": _rect_tuple((p["x"], p["y"], p["w"], p["h"]))}
                                 for p in pieces]})
    return plans


def _rect_tuple(rect):
    return [float(v) for v in rect]


def _cut(rect, axis, start, kerf):
    x, y, w, h = rect
    if axis == "x":
        lo, hi = max(x, start), min(x + w, start + kerf)
        if lo >= hi:
            return None
        return (x, y, lo-x, h), (hi, y, x+w-hi, h)
    lo, hi = max(y, start), min(y+h, start+kerf)
    if lo >= hi:
        return None
    return (x, y, w, lo-y), (x, hi, w, y+h-hi)


def _step(rect, axis, start, kerf):
    return {"eje": axis, "inicio_sierra_mm": float(start),
            "trayecto_centro_mm": float(start + kerf / 2),
            "ancho_sierra_mm": float(kerf), "region_antes_mm": _rect_tuple(rect)}


def _split(rect, pieces, kerf, budget):
    budget[0] -= 1
    if budget[0] < 0:
        return None
    x, y, w, h = rect
    if len(pieces) == 1:
        p = pieces[0]
        steps = []
        # Trim on the waste side; at the outside edge no cut is necessary.
        for axis, side in (("x", "low"), ("x", "high"), ("y", "low"), ("y", "high")):
            x, y, w, h = rect
            low = x if axis == "x" else y
            high = x+w if axis == "x" else y+h
            p_low = p[axis]
            p_high = p_low + p["w" if axis == "x" else "h"]
            distance = p_low-low if side == "low" else high-p_high
            if distance == 0:
                continue
            start = p_low-kerf if side == "low" else p_high
            split = _cut(rect, axis, start, kerf)
            if split is None:
                return None
            steps.append(_step(rect, axis, start, kerf))
            rect = split[1] if side == "low" else split[0]
        if rect != (p["x"], p["y"], p["w"], p["h"]):
            return None
        return steps, [rect]
    # A candidate must separate complete pieces across the whole parent region.
    for axis in ("y", "x"):
        extent = "w" if axis == "x" else "h"
        for start in sorted({p[axis] + p[extent] for p in pieces}):
            left = [p for p in pieces if p[axis] + p[extent] <= start]
            right = [p for p in pieces if p[axis] >= start + kerf]
            if not left or not right or len(left) + len(right) != len(pieces):
                continue
            regions = _cut(rect, axis, start, kerf)
            if regions is None:
                continue
            one = _split(regions[0], left, kerf, budget)
            if one is None:
                continue
            two = _split(regions[1], right, kerf, budget)
            if two is not None:
                return [_step(rect, axis, start, kerf)] + one[0] + two[0], one[1] + two[1]
    return None


def _verify(sheet, pieces, kerf, steps, finals):
    """Replay each full-span cut against available regions and match all parts."""
    regions = [sheet]
    for step in steps:
        parent = tuple(_d(v) for v in step["region_antes_mm"])
        if parent not in regions:
            raise SequenceUnavailable("La secuencia intenta cortar una región inexistente")
        regions.remove(parent)
        children = _cut(parent, step["eje"], _d(step["inicio_sierra_mm"]), kerf)
        if children is None:
            raise SequenceUnavailable("La sierra queda fuera de la región")
        regions.extend(child for child in children if child[2] > 0 and child[3] > 0)
    expected = sorted((p["x"], p["y"], p["w"], p["h"]) for p in pieces)
    if sorted(finals) != expected or any(rect not in regions for rect in expected):
        raise SequenceUnavailable("La secuencia no reproduce las piezas previstas")
