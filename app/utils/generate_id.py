def is_valid_id(id: str, prefix: str = "P", length: int = 5):
    if length != len(id):
        return False

    pre_id, num = id[: len(prefix)], id[len(prefix) :]
    if pre_id != prefix:
        return False
    return num.isdigit()
