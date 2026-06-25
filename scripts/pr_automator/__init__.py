"""PR Automator — local daemon for analyzing, reviewing, and merging pull requests.

Runs entirely on your machine — no GitHub Actions minutes required. Polls open PRs
via ``gh``, runs project quality gates locally, asks a Claude reviewer agent for a
verdict, and squash-merges when all ten predicate checks pass.
"""

__version__ = "0.1.0"
