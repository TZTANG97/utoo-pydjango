def gen_code(seq: int) -> str:
    if seq < 100000:
        return str(seq).zfill(5)
    return str(seq)
