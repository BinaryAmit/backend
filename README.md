# WebRTC Django Backend — Deploy to Render

This project is a Django + Channels (ASGI) backend for WebRTC signaling. The repo includes a `render.yaml` so you can one-click deploy on Render.

## What gets provisioned

- Web service running Daphne (ASGI)
- Postgres database (DATABASE_URL injected automatically by Render)
- Redis instance for Channels (REDIS_URL injected automatically by Render)
- Static files served by WhiteNoise

## Local env variables

You can override via `.env` or system env vars.

- SECRET_KEY
- DEBUG (True/False)
- ALLOWED_HOSTS (comma-separated)
- JWT_SECRET
- CORS_ALLOWED_ORIGINS (comma-separated)
- CSRF_TRUSTED_ORIGINS (comma-separated)
- DATABASE_URL (defaults to SQLite)
- REDIS_URL (Channels layer)

## Deploy on Render

1. Push this folder to a new GitHub repo.
2. On Render, click New → Blueprint and point to your repo URL.
3. Render will detect `render.yaml` and propose:
   - 1 Web Service (Django/ASGI via Daphne)
   - 1 Postgres DB
   - 1 Redis instance
4. Click Apply. First deploy will install, migrate, and collectstatic automatically.

If you create the services manually instead of the blueprint:

- Build command: `pip install -r requirements.txt`
- Start command: `daphne -b 0.0.0.0 -p $PORT webrtc_meet.asgi:application`
- Add env vars: SECRET_KEY, JWT_SECRET, DEBUG=False, RENDER=True
- Ensure Render Postgres is linked (injects DATABASE_URL)
- Ensure Render Redis is linked (injects REDIS_URL)

## Admin and health

- Admin: `/admin/`
- Healthcheck path configured: `/admin/login/`

## Notes

- Channels uses Redis in production. Without `REDIS_URL`, it falls back to in-memory (not suitable for scaling or multi-process).
- Static files are collected to `staticfiles/` and served by WhiteNoise.
