"""The filename form of a spec's name."""


def slugify(name: str) -> str:
    """Lowercase, with every run of non-alphanumerics reduced to a hyphen."""
    return "".join(character if character.isalnum() else "-" for character in name.lower()).strip(
        "-"
    )
