# Contributing

Thanks for your interest in DropSync! Contributions are welcome—bug fixes, documentation improvements, tests, and new integrations.

## Workflow

1. Fork the repository and create a feature branch from `main`.
2. Install development dependencies:
   
   ```bash
   pipx install --force .[dev]
   make fmt lint test
   ```

3. Make your changes with clear, concise commits. Follow the existing coding style (ruff/black/mypy enforced).
4. Update or add tests under `tests/` when changing behaviour.
5. Update documentation if you introduce new features or flags.
6. Open a pull request describing the change and any testing performed.

## Code style

- Python 3.11+, type-annotated, formatted by `black` (line length 100) and `ruff`.
- FastAPI endpoints should return typed Pydantic models.
- Tests use `pytest` and `pytest-asyncio`.

## GitHub Actions

Pull requests trigger linting (`ruff`, `black --check`, `mypy`) and `pytest` on Python 3.11. Ensure the workflow passes before requesting review.

## Reporting issues

Use GitHub Issues with details: steps to reproduce, expected vs actual behaviour, logs (`journalctl --user -u dropsync.service`). Tag platform (Arch, Debian, macOS).

## Security

If you discover a potential vulnerability, email [will@accelerated.industries](mailto:will@accelerated.industries) instead of filing a public issue. Please allow a reasonable time for response and patching.

Happy syncing!
