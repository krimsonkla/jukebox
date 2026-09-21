"""A service with a rolling window refuses a caller that arrives too fast."""

from jukebox.net import Pacer


class Clock:
    """A monotonic clock the test advances by hand."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def pacer(interval: float, clock: Clock, waited: list[float]) -> Pacer:
    """A pacer that records what it would have slept."""
    return Pacer(interval, sleep=waited.append, clock=clock)


def test_the_first_call_is_not_delayed():
    waited: list[float] = []
    pacer(1.0, Clock(), waited).wait()
    assert not waited


def test_a_call_arriving_too_soon_waits_out_the_remainder():
    clock, waited = Clock(), []
    paced = pacer(1.0, clock, waited)
    paced.wait()
    clock.now = 0.25
    paced.wait()
    assert waited == [0.75]


def test_a_call_arriving_after_the_interval_does_not_wait():
    clock, waited = Clock(), []
    paced = pacer(1.0, clock, waited)
    paced.wait()
    clock.now = 3.0
    paced.wait()
    assert not waited


def test_the_interval_is_measured_from_the_release_not_the_arrival():
    # The second call is released at 1.0 having waited out its remainder, so a
    # third arriving at 0.5 waits until 2.0. Measuring from arrival instead
    # would let every subsequent call bunch up against the one before it.
    clock, waited = Clock(), []
    paced = pacer(1.0, clock, waited)
    paced.wait()
    clock.now = 0.5
    paced.wait()
    paced.wait()
    assert waited == [0.5, 1.5]


def test_a_zero_interval_never_waits():
    clock, waited = Clock(), []
    paced = pacer(0.0, clock, waited)
    paced.wait()
    paced.wait()
    assert not waited
