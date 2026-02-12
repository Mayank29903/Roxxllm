# LongFormMemoryAI Backend

## Environment Variables

This backend uses environment variables for all configuration and secrets. **Never commit secrets to source control.**

- Copy `.env.example` to `.env` and fill in your real values before running locally or deploying.
- All sensitive values (API keys, DB URLs, service credentials) must be set via environment variables.

Example:

```sh
cp .env.example .env
# Edit .env and set your real values
```

See `.env.example` for required variables and documentation.

## Production Readiness
- No secrets, URLs, or credentials are hardcoded in the codebase.
- All configuration is loaded from environment variables.
- Use a secrets manager or environment injection for deployment.
