"""A spec's filename form, shared by the model and the store."""

import pytest

from jukebox.specs import slugify


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("90s Alt-Rock", "90s-alt-rock"),
        ("Best of '85", "best-of--85"),
        ("  Padded  ", "padded"),
        ("R&B", "r-b"),
    ],
)
def test_a_name_reduces_to_a_filename(name, expected):
    assert slugify(name) == expected
