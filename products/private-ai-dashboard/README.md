# Private AI Dashboard — Open WebUI for LiteLLM

A thin Open WebUI layer for the existing **LiteLLM + Redis + PostgreSQL** Railway template. This repository intentionally deploys only Open WebUI; it reuses the gateway, cache, database, provider credentials, usage tracking, and model configuration already supplied by the LiteLLM template.

## Architecture

```text
Users → Open WebUI → existing LiteLLM → Novita AI
                            ├── Redis
                            └── PostgreSQL
```

## Build it on the existing Railway template

1. Deploy the existing `litellm-novita-gateway` template.
2. Add a service from this GitHub repository to that Railway project and name it `Open WebUI`.
3. Attach a persistent volume at `/app/backend/data`.
4. Give only Open WebUI a public domain.
5. Set its health check to `/health` and configure the variables below.
6. Generate a new Railway template from the expanded project. The resulting marketplace template contains Open WebUI plus the existing LiteLLM, Redis, and PostgreSQL services.

No second LiteLLM, Redis, or PostgreSQL deployment is needed.

## Railway variables

Copy each description into Railway's **Description** field.

| Variable | Value | Description |
| --- | --- | --- |
| `OPENAI_API_BASE_URL` | `http://${{litellm-novita-gateway.RAILWAY_PRIVATE_DOMAIN}}:4000/v1` | Private OpenAI-compatible LiteLLM endpoint used for every chat request. Change the service name in the reference if your gateway has a different name. |
| `OPENAI_API_KEY` | `${{litellm-novita-gateway.LITELLM_MASTER_KEY}}` | Private credential used by Open WebUI to authenticate with the existing LiteLLM gateway. |
| `WEBUI_SECRET_KEY` | `${{secret(64)}}` | Encrypts Open WebUI sessions. Generate it once and never rotate it unless all users should be signed out. |
| `WEBUI_ADMIN_EMAIL` | Required user input | Email address for the administrator account created automatically on first startup. |
| `WEBUI_ADMIN_PASSWORD` | Required user input | Strong password for the initial administrator account. Change it after first login. |
| `WEBUI_NAME` | `Private AI Dashboard` | Name displayed in the dashboard and browser title. |
| `ENABLE_OLLAMA_API` | `False` | Disables the unused Ollama connection so all requests go through LiteLLM. |
| `ENABLE_SIGNUP` | `False` | Prevents an unknown visitor from claiming an account before the administrator is ready. Enable sign-up later when inviting teammates. |
| `DEFAULT_USER_ROLE` | `pending` | Requires administrator approval for new accounts after sign-up is enabled. |
| `SCARF_NO_ANALYTICS` | `True` | Disables Scarf telemetry for a more private deployment. |
| `DO_NOT_TRACK` | `True` | Requests that Open WebUI disable optional tracking. |
| `PORT` | `8080` | Internal Open WebUI port used by Railway networking and health checks. |

## First login

1. Open the generated Open WebUI domain.
2. Sign in with `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD`.
3. Confirm that the LiteLLM models appear in the model selector.
4. Enable sign-up from the Admin Panel only when ready to invite teammates. New accounts remain pending until approved.

## Add DeepSeek or Groq

The base gateway remains Novita-only by default. Add DeepSeek or Groq to the existing LiteLLM configuration when those providers are required; Open WebUI discovers the new models automatically through LiteLLM's `/v1/models` endpoint.

[Get a Novita AI API key](https://novita.ai/?ref=mzblm2z&utm_source=affiliate) (affiliate link; the publisher may earn a commission).

## Local run

Start the existing LiteLLM gateway on port `4000`, then:

```bash
cp .env.example .env
# Set OPENAI_API_KEY to the gateway's LITELLM_MASTER_KEY
docker compose up --build
```

Open <http://localhost:3000>. The `open-webui-data` volume preserves users, chats, and settings.

## Security

- Expose only Open WebUI; keep LiteLLM, Redis, and PostgreSQL private.
- Keep `ENABLE_SIGNUP=False` until the administrator is ready to invite users.
- Never commit `.env` or expose the LiteLLM master key publicly.
- Never rotate `WEBUI_SECRET_KEY` casually because doing so invalidates sessions.
