from backend.autocomplete import MAX_RESULTS, filter_autocomplete


def test_empty_query_returns_sorted_and_capped():
    items = [(f"Item {i:02d}", f"id-{i}") for i in range(40)]
    result = filter_autocomplete("", items)
    assert len(result) == MAX_RESULTS
    names = [name for name, _value in result]
    assert names == sorted(names, key=str.lower)
    assert names[0] == "Item 00"


def test_substring_and_id_match():
    items = [
        ("Contains Text", "contains-text"),
        ("Contains Word", "contains-word"),
        ("Member Joined", "member-joined"),
    ]
    by_name = filter_autocomplete("contains", items)
    assert [value for _name, value in by_name] == ["contains-text", "contains-word"]
    by_id = filter_autocomplete("member-joined", items)
    assert by_id == [("Member Joined", "member-joined")]


def test_prefix_ranks_above_substring():
    items = [
        ("Has Attachment", "has-attachment"),
        ("Starts With", "starts-with"),
        ("Role Mentioned", "role-mentioned"),
    ]
    result = filter_autocomplete("start", items)
    assert result[0] == ("Starts With", "starts-with")


def test_hyphen_and_space_are_equivalent():
    items = [("User Mentioned", "user-mentioned")]
    assert filter_autocomplete("user mentioned", items)
    assert filter_autocomplete("user-mentioned", items)


def test_skips_blank_and_dedupes_labels():
    items = [
        ("", "empty-label"),
        ("Same", "one"),
        ("Same", "two"),
        (None, "none"),
    ]
    result = filter_autocomplete("", items)
    values = [value for _name, value in result]
    assert values == ["one", "two"]
    names = [name for name, _value in result]
    assert names[0] == "Same"
    assert "two" in names[1]
