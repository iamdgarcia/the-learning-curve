# Deploy and Host Private AI Dashboard on Railway

Private AI Dashboard adds a polished, self-hosted Open WebUI interface to an existing LiteLLM gateway. Small teams get a private ChatGPT-style workspace while continuing to use the gateway's Novita AI models, Redis cache, PostgreSQL usage tracking, budgets, and API-key controls without paying recurring per-seat SaaS fees.

## About Hosting Private AI Dashboard

This repository deploys only Open WebUI and is designed to extend the existing LiteLLM, Redis, and PostgreSQL Railway template. Open WebUI connects to LiteLLM through Railway's private network, while only the dashboard receives a public domain. A persistent volume preserves users, chats, uploads, and settings across deployments. The deploying administrator provides an email and password, then can approve teammates from the Admin Panel. Provider credentials and model routing remain centralized in LiteLLM, so users never receive direct access to the underlying Novita AI key.

## Common Use Cases

- Give a small team a private ChatGPT-style interface backed by its existing LiteLLM gateway.
- Share Novita AI models without exposing provider credentials to individual users.
- Keep team conversations persistent while retaining centralized budgets and usage tracking.

## Dependencies for Private AI Dashboard Hosting

- An existing LiteLLM Gateway deployment with Redis and PostgreSQL.
- A persistent Railway volume mounted at `/app/backend/data`.
- A Novita AI API key configured on the existing gateway.

## Why Deploy Private AI Dashboard on Railway?

Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying Private AI Dashboard on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.
