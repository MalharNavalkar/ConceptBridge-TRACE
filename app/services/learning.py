def half_adder(a: int, b: int):
    if a not in (0, 1) or b not in (0, 1):
        raise ValueError("Inputs must be binary (0 or 1)")
    return {"a": a, "b": b, "sum": a ^ b, "carry": a & b}
