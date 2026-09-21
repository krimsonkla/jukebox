"""Search leads and ISRC assists — the opposite of what the design assumed."""

from jukebox.resolve import Method, Resolver

from tests.resolve.conftest import FakeCatalog, FakeIsrcs


def test_an_exact_match_resolves_by_search(track):
    hit = track("Take On Me", "a-ha")
    resolver = Resolver(FakeCatalog({("Take On Me", "a-ha"): [hit]}))
    outcome = resolver.resolve("Take On Me", "a-ha", 1985)
    assert outcome.resolved and outcome.match.uri == hit.uri
    assert outcome.method is Method.SEARCH


def test_a_conjunction_falls_through_to_the_credited_artist(track):
    # The whole cell matches nothing, which is how every collaboration was lost.
    hit = track("Separate Lives", "Phil Collins, Marilyn Martin")
    catalog = FakeCatalog({("Separate Lives", "Phil Collins"): [hit]})
    outcome = Resolver(catalog).resolve("Separate Lives", "Phil Collins and Marilyn Martin", 1985)
    assert outcome.resolved
    assert catalog.searched[0] == ("Separate Lives", "Phil Collins and Marilyn Martin")


def test_searching_stops_at_the_first_artist_that_answers(track):
    catalog = FakeCatalog({("Separate Lives", "Phil Collins"): [track("Separate Lives", "Phil")]})
    Resolver(catalog).resolve("Separate Lives", "Phil Collins and Marilyn Martin", 1985)
    assert ("Separate Lives", "Marilyn Martin") not in catalog.searched


def test_nothing_found_is_unresolved_rather_than_a_guess():
    outcome = Resolver(FakeCatalog()).resolve("Obscure", "Nobody", 1985)
    assert not outcome.resolved and outcome.match is None and outcome.method is None


def test_only_poor_candidates_is_unresolved_and_keeps_them(track):
    wrong = track("Something Else Entirely", "Another Band")
    outcome = Resolver(FakeCatalog({("Take On Me", "a-ha"): [wrong]})).resolve(
        "Take On Me", "a-ha", 1985
    )
    assert not outcome.resolved
    assert outcome.rejected and outcome.score is not None


def test_the_best_candidate_wins_not_the_first(track):
    karaoke = track("Take On Me", "Karaoke Stars", album="Karaoke Hits")
    real = track("Take On Me", "a-ha", album="Hunting High and Low")
    catalog = FakeCatalog({("Take On Me", "a-ha"): [karaoke, real]})
    assert Resolver(catalog).resolve("Take On Me", "a-ha", 1985).match.uri == real.uri


def test_an_isrc_is_taken_when_one_is_available(track):
    hit = track("Money for Nothing", "Dire Straits")
    resolver = Resolver(
        FakeCatalog(by_isrc={"GBUM72407046": [hit]}),
        FakeIsrcs({("Money for Nothing", "Dire Straits"): ("GBUM72407046",)}),
    )
    outcome = resolver.resolve("Money for Nothing", "Dire Straits", 1985)
    assert outcome.method is Method.ISRC and outcome.score is None


def test_an_isrc_that_the_catalogue_does_not_carry_falls_back_to_search(track):
    hit = track("Money for Nothing", "Dire Straits")
    resolver = Resolver(
        FakeCatalog({("Money for Nothing", "Dire Straits"): [hit]}, by_isrc={}),
        FakeIsrcs({("Money for Nothing", "Dire Straits"): ("GBUM72407046",)}),
    )
    assert resolver.resolve("Money for Nothing", "Dire Straits", 1985).method is Method.SEARCH


def test_without_an_isrc_source_nothing_is_looked_up(track):
    hit = track("Take On Me", "a-ha")
    outcome = Resolver(FakeCatalog({("Take On Me", "a-ha"): [hit]})).resolve(
        "Take On Me", "a-ha", 1985
    )
    assert outcome.method is Method.SEARCH


def test_duplicate_candidates_are_collapsed_by_uri(track):
    hit = track("Take On Me", "a-ha")
    catalog = FakeCatalog({("Take On Me", "a-ha"): [hit, hit]})
    assert Resolver(catalog).resolve("Take On Me", "a-ha", 1985).resolved
