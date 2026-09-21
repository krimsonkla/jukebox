"""Title and artist decide; the release year only breaks ties."""

import datetime as dt

from jukebox.ports import TrackMatch
from jukebox.resolve import Score, Sought


def candidate(title, artist, album="", released=None) -> TrackMatch:
    """A catalogue candidate."""
    return TrackMatch(uri="u", title=title, artist=artist, album=album, released=released)


def test_an_exact_match_scores_near_one():
    score = Score.of(candidate("Take On Me", "a-ha"), Sought("Take On Me", "a-ha", 1985))
    assert score.value > 0.95
    assert score.title == 1.0 and score.artist == 1.0


def test_a_qualifier_does_not_reduce_the_title_match():
    score = Score.of(
        candidate('Like A Virgin (7" Version) - Remastered', "Madonna"),
        Sought("Like a Virgin", "Madonna", 1985),
    )
    assert score.title == 1.0


def test_a_compilation_reissue_still_matches():
    # The same master on a 2010 compilation is the recording the chart means.
    score = Score.of(
        candidate(
            "Can't Fight This Feeling", "REO Speedwagon", "80s 100 Hits", dt.date(2010, 1, 1)
        ),
        Sought("Can't Fight This Feeling", "REO Speedwagon", 1985),
    )
    assert score.value > 0.9


def test_a_release_in_the_era_scores_above_the_same_match_outside_it():
    want = Sought("Take On Me", "a-ha", 1985)
    era = Score.of(candidate("Take On Me", "a-ha", released=dt.date(1985, 1, 1)), want)
    later = Score.of(candidate("Take On Me", "a-ha", released=dt.date(2010, 1, 1)), want)
    assert era.value > later.value


def test_a_candidate_with_no_release_date_is_neither_helped_nor_hurt():
    assert Score.of(candidate("Take On Me", "a-ha"), Sought("Take On Me", "a-ha", 1985)).value > 0.9


def test_a_karaoke_recording_is_pushed_below_the_threshold():
    score = Score.of(
        candidate("Take On Me", "Karaoke Stars", "Karaoke Hits"), Sought("Take On Me", "a-ha", 1985)
    )
    assert score.value < 0.72


def test_a_wrong_song_by_the_right_artist_scores_low():
    score = Score.of(candidate("Hunting High and Low", "a-ha"), Sought("Take On Me", "a-ha", 1985))
    assert score.value < 0.72
