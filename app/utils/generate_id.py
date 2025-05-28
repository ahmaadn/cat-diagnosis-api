def is_valid_id(id: str, prefix: str = "P", length: int = 5):
    if len(prefix) > len(id) or length > len(id):
        return False

    pre_id, num = id[: len(prefix)], id[len(prefix) :]
    if pre_id != prefix:
        return False
    if not num.isdigit():
        return False

    return len(id) == length
