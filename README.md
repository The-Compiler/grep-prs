# git PR grep

Search a pattern in all open PRs in a project. Useful to find PRs which use an API you'd like to change/deprecate.

![screencast](.github/screencast.gif)

Usage:

```
usage: grep-prs [-h] [--token TOKEN] USER/REPO pattern
```

The `--token` argument should be a [personal access token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token). If not given, it gets read from `~/.gh_token` instead.

## Changelog

**Note: Releases aren't actually pushed to PyPI yet...**

### v0.2.0

Features:

- New `--grep-path` flag to search for paths in diffs instead of diff content.

Python support:

- Drop support for Python 3.6
- Add official support for Python 3.10 (no code changes)
- Also test on Python 3.11-dev

Bugfixes:

- Handle `UnicodeDecodeError` in PR diffs gracefully
- Fix crash when searching for part of a filename

Internal:

- Add type annotations and mypy

### v0.1.0

- Initial release
