# Baseline test results

**PASSED** on macOS with Python 3.12.7. The command ran 181 tests before changes.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

App Store and EDGAR requests use fixtures or mocked HTTP. Real service reachability,
skill discovery, hosted imports and external connectors were **NOT RUN**.
See [baseline audit](BASELINE_AUDIT.md) for limitations that the tests do not cover.
