from backend.pagination_view import PaginationView, page_slice


def test_page_slice_is_1_indexed_and_does_not_reset():
    data = [f"item-{i}" for i in range(1, 8)]
    assert page_slice(data, 1, 3) == ["item-1", "item-2", "item-3"]
    assert page_slice(data, 2, 3) == ["item-4", "item-5", "item-6"]
    assert page_slice(data, 3, 3) == ["item-7"]


def test_page_slice_out_of_range_is_empty():
    assert page_slice(["a"], 2, 3) == []
    assert page_slice(["a"], 0, 3) == []
    assert page_slice(["a"], 1, 0) == []


def test_pagination_view_slices_current_page():
    data = [
        {"title": f"{i}. t", "subtitle": "by x", "trigger_type": "Contains Text", "dos_subtitle": "0/3"}
        for i in range(1, 8)
    ]
    pager = PaginationView(title="Server Triggers", data=data, sep=3)
    assert [item["title"] for item in pager.get_current_page_data()] == ["1. t", "2. t", "3. t"]
    pager.current_page = 3
    assert [item["title"] for item in pager.get_current_page_data()] == ["7. t"]
