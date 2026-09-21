"""A chart writes a collaboration as one cell; a search filter takes one artist."""

from jukebox.text import credited


def test_a_single_artist_yields_only_itself():
    assert credited("George Michael") == ("George Michael",)


def test_the_whole_cell_comes_first_because_an_ampersand_may_be_a_band_name():
    assert credited("Kool & the Gang")[0] == "Kool & the Gang"


def test_a_conjunction_yields_each_artist():
    assert credited("Phil Collins and Marilyn Martin") == (
        "Phil Collins and Marilyn Martin",
        "Phil Collins",
        "Marilyn Martin",
    )


def test_a_parenthetical_collaborator_yields_the_lead_artist():
    assert "Ray Charles" in credited("Ray Charles (with Willie Nelson)")


def test_a_slash_without_spaces_still_separates():
    assert "Harold Faltermeyer" in credited("Patti LaBelle/ Harold Faltermeyer")


def test_a_featuring_credit_yields_the_lead_artist():
    assert credited("Dionne Warwick featuring Elton John")[1] == "Dionne Warwick"


def test_no_name_is_offered_twice():
    names = credited("Wham! & Wham!")
    assert len(names) == len(set(name.lower() for name in names))
