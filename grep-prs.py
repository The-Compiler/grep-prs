import re
import sys
import subprocess
import rich.progress

def call_git(*args):
    proc = subprocess.run(['git', *args], capture_output=True, encoding='utf-8', check=True)
    return proc.stdout.splitlines()


def _parse_data(lines):
    prefix = 'refs/pull/'
    suffix = '/head'
    for line in lines:
        commit, ref = line.split()
        assert ref.startswith(prefix), ref
        assert ref.endswith(suffix), ref
        yield commit, int(ref[len(prefix):-len(suffix)])


def _grep_diff(diff, pattern):
    for line in diff:
        if pattern.search(line):
            yield line


def _pr_header(console, pr):
    console.rule(f'[blue]PR #{pr}[/blue]')


def run(progress):
    task = progress.add_task('Getting PRs...', start=False)
    lines = call_git('ls-remote', 'origin', 'pull/*/head')
    data = sorted(_parse_data(lines), key=lambda pair: pair[1])

    pattern = re.compile(sys.argv[1])

    progress.update(task, description='Grepping PRs...', total=len(data))
    progress.start_task(task)
    for commit, pr in data:
        progress.update(task, advance=1)

        try:
            diff = call_git('diff', '-U0', f'HEAD...{commit}')
        except subprocess.CalledProcessError as e:
            _pr_header(progress.console, pr)
            progress.console.print(f'[red]{e.stderr.strip()}[/red]')
            continue

        matches = list(_grep_diff(diff, pattern))
        if matches:
            _pr_header(progress.console, pr)
            progress.console.print('\n'.join(matches))


def main():
    with rich.progress.Progress() as progress:
        run(progress)

if __name__ == '__main__':
    main()
