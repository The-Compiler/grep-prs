from __future__ import annotations  # for Python 3.7 and 3.8

import re
import sys
import pathlib
import itertools
import argparse
import dataclasses
from typing import Iterator, Tuple

import rich.progress
import rich.panel
import rich.syntax
import github3


MatchType = Tuple[str, str, str]  # needs to be upper-case as not in an annotation


class Error(Exception):
    pass


@dataclasses.dataclass
class RepoName:

    """A GitHub repo like user/project."""

    namespace: str
    name: str

    @classmethod
    def parse(cls, s: str) -> "RepoName":
        namespace, name = s.split("/")
        return cls(namespace, name)


def _grep_diff(diff: list[str], pattern: re.Pattern[str]) -> Iterator[MatchType]:
    filename = None
    location = None
    for line in diff:
        if line.startswith("--- "):
            filename = line
        elif line.startswith("+++ "):
            assert filename is not None
            filename += "\n" + line
        elif line.startswith("@@ "):
            location = line
        elif not line.startswith(("+", "-")):
            continue
        elif pattern.search(line):
            if filename is None or location is None:
                print("\n".join(diff))
                raise AssertionError(f"filename: {filename}, location: {location}")
            yield (filename, location, line)


def _format_matches(matches: list[MatchType]) -> Iterator[str]:
    for filename, file_group in itertools.groupby(matches, key=lambda tpl: tpl[0]):
        yield filename

        for position, pos_group in itertools.groupby(
            file_group, key=lambda tpl: tpl[1]
        ):
            yield position

            for _filename, _pos, line in pos_group:
                yield line

            yield ""


def _print_pr_header(
    console: rich.console.Console, pr: github3.pulls.ShortPullRequest
) -> None:
    title = f"[magenta]PR #{pr.number}[/magenta]"
    panel = rich.panel.Panel(
        f"[blue]{pr.html_url}[/blue]\n"
        f"[bright_black]{pr.title}[/bright_black]\n"
        f"[yellow]@{pr.user.login}[/yellow]",
        expand=False,
        title=title,
    )
    console.print("")
    console.print(panel)


def _get_token(args: argparse.Namespace) -> str:
    if args.token is not None:
        assert isinstance(args.token, str)
        return args.token

    token_path = pathlib.Path("~/.gh_token").expanduser()
    if not token_path.exists():
        raise Error("No --token given and ~/.gh_token does not exist.")
    return token_path.read_text().strip()


def run(args: argparse.Namespace, progress: rich.progress.Progress) -> None:
    task = progress.add_task("Getting PRs...", start=False)

    gh = github3.login(token=_get_token(args))
    repo = gh.repository(args.repository.namespace, args.repository.name)
    prs = list(repo.pull_requests(state="open"))

    pattern = re.compile(args.pattern)

    progress.update(task, total=len(prs))
    progress.start_task(task)
    for pr in prs:
        progress.update(task, advance=1, description=f"#{pr.number}")

        try:
            diff = pr.patch().decode("utf-8").splitlines()
        except UnicodeDecodeError as e:
            progress.console.print(f"[bold red]#{pr.number}: {e}[/]")
            continue

        matches = list(_grep_diff(diff, pattern))

        if matches:
            _print_pr_header(progress.console, pr)
            syntax = rich.syntax.Syntax(
                "\n".join(_format_matches(matches)), "diff", theme="ansi_dark"
            )
            progress.console.print(syntax)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--token",
        action="store",
        help=(
            "The GitHub token. If not given, it gets read from ~/.gh_token. See "
            "https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token "
            "for setup details."
        ),
    )
    parser.add_argument(
        "repository",
        metavar="USER/REPO",
        help="The repository to search in",
        type=RepoName.parse,
    )
    parser.add_argument("pattern", help="The pattern to search for")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with rich.progress.Progress() as progress:
        try:
            run(args, progress)
        except Error as e:
            sys.exit(str(e))


if __name__ == "__main__":
    main()
