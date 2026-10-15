# Testing Rules

## Running Tests

- Use `pytest` to run tests:
  ```powershell
  python -m pytest
  ```

## Structure

- All tests must be located under `app/tests/`.
- Unit tests go in `app/tests/unit/`.
- Integration tests go in `app/tests/integration/`.
- Fixtures are stored in `app/tests/fixtures/`.
- Keep tests self-contained and run them periodically during development.
