# Reporting a security problem

jukebox runs an OAuth client against a person's own Spotify account and stores a
refresh token on their machine. If you find a way to obtain that token, to make
the tool write to an account it was not authorized for, or to make the MCP
surface act outside what its caller asked for, please report it privately first.

**Use GitHub's private vulnerability reporting** — the *Report a vulnerability*
button under this repository's Security tab. That reaches the maintainer without
disclosing to everyone at once, which a public issue would.

Please include what you ran, what happened, and what you expected. A proof of
concept is welcome and never required.

## What is in scope

- The authorization flow in `src/jukebox/oauth/` and `src/jukebox/providers/`,
  including the loopback redirect catcher.
- Token storage and file permissions.
- The MCP surface in `src/jukebox/mcp/`, in particular anything that makes a
  tool act on a resource its caller did not name.
- Parsing of third-party HTML in `src/jukebox/charts/`.

## What is not

- Anything requiring an attacker who already has your user account on your own
  machine: the refresh token is readable by its owner by design.
- Rate limits, outages, or content errors at Wikipedia, MusicBrainz or Spotify.
- The absence of a feature.

## What to expect

An acknowledgement, and a fix or an explanation of why the behaviour is
intended. This is a personal project with no service behind it and no bounty; it
is maintained in someone's own time, so please be patient with the timeline.
