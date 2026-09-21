{config, ...}: {
  # Python and its toolchain. Dependencies are declared in pyproject.toml and
  # pinned in uv.lock; devenv runs `uv sync` on shell entry, so the venv under
  # $DEVENV_STATE/venv always matches the lock file.
  #
  # This shell is a convenience. It is not required: `uv sync --all-groups`
  # and `uv run pytest` give the same result, and that is the route CI takes.
  languages.python = {
    enable = true;
    version = "3.12";
    uv = {
      enable = true;
      sync = {
        enable = true;
        allGroups = true;
      };
    };
  };

  git-hooks.hooks = {
    # Formatting and linting run from the project venv, so they resolve this
    # project's imports and use the settings in pyproject.toml.
    black.enable = true;
    ruff.enable = true;
    pylint = {
      enable = true;
      # git-hooks ships its own pylint, which sits outside the venv and so
      # cannot resolve this project's third-party imports. Point it at the one
      # uv installed, where httpx, pytest and respx are importable.
      settings.binPath = "${config.devenv.state}/venv/bin/pylint";
    };

    check-added-large-files.enable = true;
    check-json.enable = true;
    check-merge-conflicts.enable = true;
    check-yaml.enable = true;
    detect-private-keys.enable = true;
    end-of-file-fixer.enable = true;
    trim-trailing-whitespace.enable = true;
  };

  # tests/fixtures/pages holds verbatim captures of Wikipedia pages. Formatting
  # them changes bytes the parser tests assert on, and scanning them reports
  # Wikipedia's own citation links as findings here. Neither is this project's
  # code, so the hooks that rewrite or scan content skip the directory.
  git-hooks.excludes = ["^tests/fixtures/pages/"];

  enterShell = ''
    export PYTHONPATH=$PYTHONPATH:$(pwd)
  '';
}
