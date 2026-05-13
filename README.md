# logslice

> Terminal utility for slicing, filtering, and tailing structured JSON logs with a simple query syntax.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Filter logs by field value
logslice app.log --where "level=error"

# Slice a time range and select specific fields
logslice app.log --from "2024-01-10T08:00:00" --to "2024-01-10T09:00:00" --fields timestamp,message,level

# Tail live logs and filter on the fly
logslice --tail /var/log/app.json --where "status>=500"

# Chain filters and output as plain text
logslice app.log --where "service=api" --where "latency>200" --format text
```

### Query Syntax

| Operator | Example              | Description        |
|----------|----------------------|--------------------|
| `=`      | `level=error`        | Exact match        |
| `!=`     | `env!=production`    | Not equal          |
| `>`      | `latency>300`        | Greater than       |
| `~`      | `message~timeout`    | Contains substring |

---

## Options

| Flag          | Description                          |
|---------------|--------------------------------------|
| `--where`     | Filter expression (repeatable)       |
| `--fields`    | Comma-separated fields to display    |
| `--from`      | Start timestamp (ISO 8601)           |
| `--to`        | End timestamp (ISO 8601)             |
| `--tail`      | Follow a live log file               |
| `--format`    | Output format: `json` or `text`      |

---

## License

MIT © 2024 [yourname](https://github.com/yourname)