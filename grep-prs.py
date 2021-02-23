import re
import sys
import pathlib

import rich.progress
import rich.panel
import rich.syntax
import github3


def _grep_diff(diff, pattern):
    for line in diff:
        if not line.startswith(('+', '-')):
            continue
        if pattern.search(line):
            yield line


def _print_pr_header(console, pr):
    title = f'[magenta]PR #{pr.number}[/magenta]'
    panel = rich.panel.Panel(
            f"[blue]{pr.html_url}[/blue]\n"
            f"[bright_black]{pr.title}[/bright_black]\n"
            f"[yellow]@{pr.user.login}[/yellow]", expand=False, title=title)
    console.print('')
    console.print(panel)


def run(progress):
    task = progress.add_task('Getting PRs...', start=False)

    token = pathlib.Path('~/.gh_token').expanduser().read_text().strip()
    gh = github3.login(token=token)
    repo = gh.repository('qutebrowser', 'qutebrowser')
    prs = list(repo.pull_requests(state='open'))

    pattern = re.compile(sys.argv[1])

    progress.update(task, description='Grepping PRs...', total=len(prs))
    progress.start_task(task)
    for pr in prs:
        progress.update(task, advance=1)

        diff = pr.patch().decode('utf-8').splitlines()
        matches = list(_grep_diff(diff, pattern))

        if matches:
            _print_pr_header(progress.console, pr)
            syntax = rich.syntax.Syntax('\n'.join(matches), 'diff')
            progress.console.print(syntax)


def main():
    with rich.progress.Progress() as progress:
        run(progress)

if __name__ == '__main__':
    main()
