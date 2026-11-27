# Contributing

Thanks for contributing.

## Workflow

1. Branch from `main`.
2. Keep research output free of orders, accounts, and private holdings.
3. Run the local checks before pushing:

```sh
python3 -m unittest discover -s tests -v
```

4. Use English Conventional Commits with a subject of at most 72 characters.
5. Fill in every section of `.github/pull_request_template.md`.

Do not merge your own high-risk change. A current-head review receipt and a
clearing label recorded on that same head are repository gates, not something
a pull request body can waive.

## Private material

Do not commit `.env`, `watchlists/`, `holdings/`, `decision-logs/`,
`preferences/`, or real credentials. `.gitignore` does not make a committed
file secret. See [SECURITY.md](SECURITY.md) for reporting.
