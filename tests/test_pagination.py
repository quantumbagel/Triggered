from backend.pagination_view import page_slice


def test_page_slice_is_1_indexed_and_does_not_reset():
    data = [f"item-{i}" for i in range(1, 8)]
    assert page_slice(data, 1, 3) == ["item-1", "item-2", "item-3"]
    assert page_slice(data, 2, 3) == ["item-4", "item-5", "item-6"]
    assert page_slice(data, 3, 3) == ["item-7"]


def test_page_slice_out_of_range_is_empty():
    assert page_slice(["a"], 2, 3) == []
    assert page_slice(["a"], 0, 3) == []
    assert page_slice(["a"], 1, 0) == []
