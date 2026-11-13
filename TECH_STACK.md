# Tech Stack Example

- **Web app:** Flask + gunicorn webhook, nginx reverse-proxy (SSL termination), systemd `ai-email.service` on `:8080`
- **Language:** Python 3.11+ (`requires-python = ">=3.11"`)
- **Key packages:** litellm, pydantic, httpx, boto3, structlog, python-dotenv, html2text, mistune, pymupdf, stripe
- **DB:** SQLite 
- **Email:** AWS SES (outbound via boto3) + SNS/S3 (inbound storage/notification)
- **Payments:** Stripe Checkout + webhook
- **Testing/lint:** pytest tests, ruff (dev dep, no config in pyproject)

## Infra (VPS)
- **Provider:** DigitalOcean droplet, SFO3, 1 vCPU / 512MB RAM / 10GB
- **SSH:** key-only (ed25519), user `agent` (passwordless sudo), `ssh agent@IPADDRESS`
- **Deploy:** `./scripts/deploy.sh` — rsyncs `src/` + pyproject.toml, reinstalls deps, restarts service, health check
- **Env:** `/opt/ai-email/.env` (chmod 600, agent-owned)
- **Watchdogs:** on-VPS healthcheck (systemd timer every 5 min, `healthcheck.py`); off-box cron watchdog  (SSHes in + alerts Telegram on failure, every 15 min)
- **Backups:** nightly SQLite dump (iterdump + gzip) to local git 