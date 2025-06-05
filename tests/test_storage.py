import pytest
from storage import Message, MessageStorage


def test_add_and_clear():
    s = MessageStorage()
    s.add_message(Message(1, "Alice", "hi", 1))
    assert len(s.messages) == 1
    s.clear()
    assert not s.messages


def test_renaming_flow():
    s = MessageStorage()
    s.add_message(Message(1, "Alice", "a", 1))
    s.add_message(Message(2, "Bob", "b", 1))
    first = s.start_renaming(99)
    assert first in {1, 2}
    nxt = s.record_name(99, "A")
    assert s.get_name(first, "") == "A"
    if nxt is not None:
        s.record_name(99, "B")
    assert not s.is_renaming(99)

