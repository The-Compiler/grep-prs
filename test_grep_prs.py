import textwrap
import re

import pytest

from grep_prs import RepoName, _format_matches, _grep_diff


@pytest.mark.parametrize("s", ["", "noslash", "too/many/slashes"])
def test_parse_repo_name_invalid(s):
    with pytest.raises(ValueError):
        RepoName.parse(s)


@pytest.mark.parametrize(
    "pattern, diff, expected",
    [
        (
            "version",
            """
            diff --git c/setup.cfg i/setup.cfg
            new file mode 100644
            index 0000000..db2b43c
            --- /dev/null
            +++ i/setup.cfg
            @@ -0,0 +1,31 @@
            +[metadata]
            +name = grep-prs
            +version = 0.1.0
            """,
            """
            --- /dev/null
            +++ i/setup.cfg
            @@ -0,0 +1,31 @@
            +version = 0.1.0
            """,
        ),
        (
            "nomatch",
            """
            diff --git c/setup.cfg i/setup.cfg
            new file mode 100644
            index 0000000..db2b43c
            --- /dev/null
            +++ i/setup.cfg
            @@ -0,0 +1,31 @@
            +[metadata]
            +name = grep-prs
            +version = 0.1.0
            """,
            "",
        ),
    ],
)
def test_diff_grepping(pattern, diff, expected):
    diff = textwrap.dedent(diff).lstrip("\n")
    expected = textwrap.dedent(expected).lstrip("\n")

    filtered = list(_grep_diff(diff.splitlines(), re.compile(pattern)))
    print(filtered)
    assert "\n".join(_format_matches(filtered)) == expected
