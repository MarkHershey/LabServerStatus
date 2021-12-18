def mask_sensitive_string(value: str) -> str:
    """
    Mask sensitive string
    """
    if value is None:
        return None

    assert isinstance(value, str)

    if len(value) == 0:
        return ""
    elif len(value) == 1:
        return "*"
    elif len(value) == 2:
        return value[0] + "*"
    elif len(value) <= 4:
        return value[0] + "*" * (len(value) - 2) + value[-1]
    else:
        return value[0:2] + "*" * (len(value) - 3) + value[-1]
