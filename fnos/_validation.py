"""Private validation helpers for query wrapper arguments."""


def require_non_empty_string(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}参数不能为空字符串")


def require_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name}参数必须是正整数")


def require_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name}参数必须是非负整数")


def copy_dict_list(name: str, value: list[dict]) -> list[dict]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{name}参数必须是字典列表")
    return [dict(item) for item in value]
