"""Two spellings of one song have to compare equal."""

from jukebox.text import core_artist, core_title, normalize


def test_case_accents_and_punctuation_fall_away():
    assert normalize("Sinéad O'Connor!") == "sinead oconnor"


def test_whitespace_collapses():
    assert normalize("  Dan   Hartman ") == "dan hartman"


def test_a_bracketed_qualifier_is_not_part_of_the_song():
    assert core_title('Like A Virgin (7" Version)') == "like a virgin"


def test_a_dashed_qualifier_is_not_part_of_the_song():
    assert core_title("Every Time You Go Away - Radio Edit") == "every time you go away"
    assert core_title('The Heat Is On - From "Beverly Hills Cop"') == "the heat is on"


def test_a_leading_article_on_an_artist_is_dropped():
    assert core_artist("The Psychedelic Furs") == core_artist("Psychedelic Furs")


def test_an_article_inside_a_name_is_kept():
    assert core_artist("Kool & the Gang") == "kool the gang"
