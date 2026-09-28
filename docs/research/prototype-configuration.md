# Prototype Configuration

The prototype selects its base configuration as follows:

1. Without `--config`, load the checked-out `config/default.yaml`; in an installed distribution, use the packaged equivalent.
2. With `--config PATH`, use that YAML file instead of the default (it is not merged with the default).
3. Apply supported environment-variable overrides.
4. Apply command-specific flags, such as `prototype validate --corpus-root PATH`.

Research commands use `corpus_root` and `validation_output`; `prototype local` uses the separate `developer_workspace`. The remaining fields document the pinned local runtime and retrieval contracts so accidental research configuration drift fails early. Older custom YAML files that omit `developer_workspace` receive the separate default `~/.prototype/developer-workspace`.

## Configuration Files

- [default.yaml](../../config/default.yaml) contains separate research and developer storage defaults.
- [example.yaml](../../config/example.yaml) shows an external Windows-style setup.

Copy the example to an external file, then pass it before the subcommand:

```powershell
New-Item -ItemType Directory -Force C:\research | Out-Null
Copy-Item config\example.yaml C:\research\prototype.yaml
prototype --config C:/research/prototype.yaml validate
```

Keep checkouts, model caches, embeddings, indexes, and reports outside the Git repository.

## Environment Variables

| Variable | Configuration field | Example |
|---|---|---|
| `PROTOTYPE_DATA_ROOT` | `data_root` | `C:/research/prototype-data` |
| `PROTOTYPE_DEVELOPER_WORKSPACE` | `developer_workspace` | `C:/Users/you/.prototype/developer-workspace` |
| `PROTOTYPE_CORPUS_ROOT` | `corpus_root` | `C:/research/prototype-data/corpus` |
| `PROTOTYPE_VALIDATION_OUTPUT` | `validation_output` | `C:/research/prototype-data/validation` |
| `EMBEDDING_MODEL_CACHE` | `embedding_model_cache` | `C:/research/model-cache` |
| `PROTOTYPE_OFFLINE` | `offline` | `true` |
| `PROTOTYPE_DEVICE` | `device` | `cpu` |
| `PROTOTYPE_EMBEDDING_MODEL_ID` | `embedding_model_id` | `sentence-transformers/all-MiniLM-L6-v2` |
| `PROTOTYPE_EMBEDDING_MODEL_REVISION` | `embedding_model_revision` | 40-character SHA-1 |
| `PROTOTYPE_EMBEDDING_DIMENSIONS` | `embedding_dimensions` | `384` |
| `PROTOTYPE_MAX_TOKENS` | `max_tokens` | `256` |
| `PROTOTYPE_RETRIEVAL_K` | `retrieval_k` | `50` |
| `PROTOTYPE_RRF_CONSTANT` | `rrf_constant` | `60` |

Boolean values accept `true/false`, `yes/no`, `on/off`, or `1/0`. Integer values must be positive. The loader rejects non-CPU devices and changes to the frozen 384-dimensional, 256-token embedding contract.

## Storage separation

The developer workspace must not overlap `data_root`, `corpus_root`, `validation_output`, or the research `embedding_model_cache`. Configuration loading fails with the conflicting paths and points to `PROTOTYPE_DEVELOPER_WORKSPACE`. Local commands additionally reject a developer workspace inside the source checkout or a repository path overlapping research storage. Research defaults remain under `~/prototype-data`; local indexes, model weights, and local command records default under `~/.prototype/developer-workspace`.

The developer workspace location itself is deliberately omitted from research run configuration records. A local command does not create a research run record at all.

The built-in `prototype local demo` runs entirely in memory and does not create the developer workspace. `scan`, `index`, and `query` create the developer directories on first use.

## Troubleshooting

- **Configuration file is missing/unreadable:** confirm the path exists and is readable. `--config` replaces the default; it does not fall back to another custom path.
- **Configuration cannot be parsed:** check YAML indentation, quoting, and that the top-level value is a mapping.
- **Required configuration values are missing:** compare the file with `config/example.yaml`; all fields shown there are required.
- **Invalid frozen contract:** restore `device: cpu`, `embedding_dimensions: 384`, and `max_tokens: 256`.
- **Reports or source data inside the repository:** move the configured paths outside the project before running validation or indexing.