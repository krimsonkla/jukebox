"""Specs are committed, so they hold no music service's content."""

import pytest
import yaml

from jukebox.charts import Chart
from jukebox.specs import NoSuchSpec, Selection, Shape, Spec, SpecStore


def a_spec(name: str = "90s Alt-Rock") -> Spec:
    """A spec worth storing."""
    return Spec(
        name=name,
        select=Selection(charts=[Chart.MODERN_ROCK], years=(1990, 1999), max_rank=40),
        shape=Shape(size=80, max_per_artist=2),
    )


def test_nothing_stored_lists_nothing(tmp_path):
    assert SpecStore(tmp_path / "absent").names() == []


def test_a_saved_spec_reads_back(tmp_path):
    store = SpecStore(tmp_path)
    store.save(a_spec())
    assert store.load("90s Alt-Rock").shape.size == 80


def test_a_spec_loads_by_slug_as_well_as_by_name(tmp_path):
    store = SpecStore(tmp_path)
    store.save(a_spec())
    assert store.load("90s-alt-rock").name == "90s Alt-Rock"


def test_an_unknown_spec_lists_the_known_ones(tmp_path):
    store = SpecStore(tmp_path)
    store.save(a_spec())
    with pytest.raises(NoSuchSpec, match="90s-alt-rock"):
        store.load("nope")


def test_the_yaml_omits_defaults_so_a_spec_reads_as_what_was_asked_for(tmp_path):
    store = SpecStore(tmp_path)
    store.save(a_spec())
    body = yaml.safe_load(store.path("90s-alt-rock").read_text())
    assert "seed" not in body["shape"] and "description" not in body


def test_saving_again_replaces_rather_than_duplicates(tmp_path):
    store = SpecStore(tmp_path)
    store.save(a_spec())
    store.save(a_spec())
    assert store.names() == ["90s-alt-rock"]


def test_stored_specs_are_listed_in_order(tmp_path):
    store = SpecStore(tmp_path)
    store.save(a_spec("B Side"))
    store.save(a_spec("A Side"))
    assert store.names() == ["a-side", "b-side"]


def test_a_spec_name_cannot_choose_a_path(tmp_path):
    """The read path gets the rule the write path already had.

    Four tools funnel through `load`, so a model steered by text it just
    fetched could otherwise name any file on the machine.
    """
    (tmp_path / "secret.yaml").write_text("name: leaked\n")
    store = SpecStore(tmp_path / "specs")
    store.save(a_spec())
    for attempt in ("../secret", "/etc/passwd", "../../secret", "..%2Fsecret"):
        with pytest.raises(NoSuchSpec):
            store.load(attempt)
