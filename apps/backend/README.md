# AgentOS Chat Backend

FastAPI service for search-backed chat with Agno and PostgreSQL.

## LangWatch tracing (optional)

When `LANGWATCH_API_KEY` is set, agent runs are exported to [LangWatch](https://langwatch.ai/) using the
[Agno integration](https://docs.agno.com/observability/langwatch). Tracing is disabled when the key is
empty; chat continues to work normally.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LANGWATCH_API_KEY` | To enable tracing | (empty) | LangWatch API key |
| `LANGWATCH_ENDPOINT` | No | SaaS | Self-hosted LangWatch base URL |
| `APP_ENVIRONMENT` | No | `local` | Trace tag: `local`, `staging`, or `production` |

`AGNO_TELEMETRY` is independent of LangWatch.

See [specs/002-langwatch-backend/quickstart.md](../../specs/002-langwatch-backend/quickstart.md) for setup and verification steps.
