import pytest

from fnos._validation import (
    copy_dict_list,
    require_non_empty_string,
    require_non_negative_int,
    require_positive_int,
)


@pytest.mark.parametrize("value", [None, "", "   ", 1])
def test_require_non_empty_string_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        require_non_empty_string("name", value)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "1"])
def test_require_positive_int_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        require_positive_int("page", value)


@pytest.mark.parametrize("value", [-1, True, 1.5, "1"])
def test_require_non_negative_int_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        require_non_negative_int("uid", value)


def test_valid_scalar_values_are_accepted():
    require_non_empty_string("name", "date-format")
    require_positive_int("page", 1)
    require_non_negative_int("uid", 0)


@pytest.mark.parametrize("value", [None, {}, [1], [{"pid": 1}, "bad"]])
def test_copy_dict_list_rejects_non_dict_lists(value):
    with pytest.raises(ValueError):
        copy_dict_list("processes", value)


def test_copy_dict_list_returns_new_list_and_dicts():
    source = [{"pid": 1001, "process": "example-process"}]
    result = copy_dict_list("processes", source)

    assert result == source
    assert result is not source
    assert result[0] is not source[0]
