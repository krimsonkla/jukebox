"""Which discography column carries which chart.

A discography heads its columns in whatever shorthand its editors chose, and
the same chart is `US Main Rock` on one article and `US Main.` on the next. The
variants are declared here so a mapper never guesses, and a column naming a
chart this project does not read is passed over rather than misfiled.

Only charts whose corpus records a chart position are listed. A discography
publishes how high a record got, and the year-end lists record something else:
how big it was across a whole year. A song can be the fortieth biggest of its
year without rising above thirty, and one that peaked at eighty-three can place
nowhere at all. Filing a peak among year-end ranks makes a spec asking for the
top forty return records that never came near it.
"""

from jukebox.charts.chart import Chart

# Several American rock charts are not these two and must not be read as them.
# `US Rock` is Hot Rock Songs, which began in 2009; `US Act. Rock`, `US Herit.
# Rock` and `US Rock Air.` are separate airplay panels; `US Bub.` is the chart
# for records that missed the Hot 100 altogether.
_NAMES: dict[Chart, tuple[str, ...]] = {
    Chart.MAINSTREAM_ROCK: (
        "US Main Rock",
        "US Main",
        "US Main.",
        "US Main. Rock",
        "US Mainstream Rock",
        "US Main Rock Tracks",
        "US Rock Tracks",
        "US Alb. Rock",
    ),
    Chart.MODERN_ROCK: (
        "US Alt.",
        "US Alt",
        "US Alternative",
        "US Mod. Rock",
        "US Mod Rock",
        "US Modern Rock",
        "US Alt. Airplay",
    ),
}

_BY_NAME = {name: chart for chart, names in _NAMES.items() for name in names}


def charted_by(header: str) -> Chart | None:
    """The chart this column heading names, if it is one this project reads."""
    return _BY_NAME.get(header.strip())
