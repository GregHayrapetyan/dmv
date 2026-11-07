# Docker

Runs Postgres, Django (gunicorn), and Next.js (standalone). TLS and public routing are handled by **host nginx** on the VPS (see `docker/nginx/host.mytestdmv.com.conf`). An optional compose `nginx` service (`--profile local`) is available for all-in-one HTTP on a laptop.

## Repo layout (submodule)

The frontend lives in a separate GitHub repo and is wired as a **git submodule** at `client/`:

- Backend: `https://github.com/GregHayrapetyan/dmv`
- Frontend: `https://github.com/aregchatalyan/mytestdmv` → `client/`

### Clone

```bash
git clone --recurse-submodules https://github.com/GregHayrapetyan/dmv.git
cd dmv
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

### Update frontend pin

```bash
cd client
git fetch origin
git checkout <commit-or-branch>
cd ..
git add client
git commit -m "Bump client submodule"
```

## Production (host nginx)

Matches the live split-host layout:

| Public host | Proxies to | Role |
|-------------|------------|------|
| `https://mytestdmv.com` | `127.0.0.1:3000` | Next.js (pages + BFF `/api/auth`, `/api/proxy`, `/api/tts`) |
| `https://api.mytestdmv.com` | `127.0.0.1:8000` | Django API, admin, Wagtail |
| `https://api.mytestdmv.com/media/` | host files | Uploads (nginx `alias`, not proxied) |
| `https://api.mytestdmv.com/static/` | host files | `collectstatic` output |

### 1. Env

```bash
cp .env.example .env
# fill secrets; keep production URL block from .env.example
```

Important production values:

```env
DEBUG=False
NEXT_PUBLIC_APP_DOMAIN=https://mytestdmv.com
NEXT_PUBLIC_API_URL=https://api.mytestdmv.com/api
API_URL=http://api:8000/api
COOKIE_SECURE=true
MEDIA_HOST_PATH=/home/dmv/apps/dmv/media
STATIC_HOST_PATH=/home/dmv/apps/dmv/staticfiles
API_BIND=127.0.0.1:8000
WEB_BIND=127.0.0.1:3000
```

`MEDIA_HOST_PATH` / `STATIC_HOST_PATH` **must** be the same directories as the `alias` lines in host nginx.

### 2. Apple key (optional)

```bash
cp /path/to/AuthKey_XXXXX.p8 secrets/apple_auth_key.p8
```

### 3. Start app containers (no compose nginx)

```bash
mkdir -p "$MEDIA_HOST_PATH" "$STATIC_HOST_PATH"
docker compose up --build -d
```

### 4. Host nginx

Use your existing site config, or the sample:

```bash
sudo cp docker/nginx/host.mytestdmv.com.conf /etc/nginx/sites-available/mytestdmv.com
# confirm ssl paths + media/static aliases
sudo nginx -t && sudo systemctl reload nginx
```

### 5. Seed (fresh DB)

```bash
docker compose exec api python manage.py import_questions --file questions.json
docker compose exec api python manage.py createsuperuser
```

### URLs

- Site: `https://mytestdmv.com`
- API health: `https://api.mytestdmv.com/api/health/`
- Django admin: `https://api.mytestdmv.com/admin/`
- Wagtail: `https://api.mytestdmv.com/cms/`

## Local all-in-one (optional)

Compose nginx on port 80 (single origin for app + `/media`):

```bash
# in .env use the "Local all-in-one" block from .env.example
docker compose --profile local up --build -d
```

- Site: `http://localhost/`
- API via same host: `http://localhost/api/health/`

## Services

| Service | Role |
|---------|------|
| `db` | PostgreSQL 16 |
| `api` | Django + gunicorn; migrates / collectstatic on boot; published on `API_BIND` |
| `web` | Next.js standalone; BFF at `/api/auth`, `/api/proxy`, `/api/tts`; published on `WEB_BIND` |
| `nginx` | Profile `local` only — reverse proxy + `/media` for laptop HTTP |

### Routing notes

**Production (host nginx):** frontend vhost → web only; API vhost → api + static/media files.

**Local profile:** compose nginx sends Next BFF paths to `web` and Django paths to `api`:

- `/api/auth/`, `/api/proxy/`, `/api/tts` → `web`
- `/api/*`, `/admin/`, `/cms/`, `/static/` → `api`
- `/media/` → bind-mounted media dir
- `/` → `web`

Inside Docker, the web container always uses `API_URL=http://api:8000/api` for server-side fetches. CMS **images** for `next/image` are pointed at `NEXT_PUBLIC_MEDIA_OPTIMIZE_ORIGIN` (default `http://api:8000`) so the optimizer can resize/compress over the Docker network (`images.dangerouslyAllowLocalIP` is required for that). Videos keep absolute `https://api.mytestdmv.com/media/...` URLs for host-nginx MP4 streaming.

For the Next.js **build**, set `NEXT_PUBLIC_GOOGLE_CLIENT_ID` / `NEXT_PUBLIC_APPLE_CLIENT_ID` (compose falls back to `GOOGLE_OAUTH_CLIENT_ID` / `APPLE_CLIENT_ID`). Rebuild `web` after changing those values.

## TLS / auth cookies

Use `COOKIE_SECURE=true` behind HTTPS host nginx. For plain-HTTP local profile, set `COOKIE_SECURE=false` and usually `DEBUG=True` so Django/Wagtail admin session cookies are not marked `Secure`.

### Media files

A Postgres dump restores DB rows only. CMS/lesson images live under `MEDIA_HOST_PATH` (mounted at `/app/media` in the api container).

```bash
# example restore into the bind mount
rsync -a /path/to/media/backup/ "$MEDIA_HOST_PATH"/
# or
docker compose cp /path/to/media/. api:/app/media/
```

## Useful commands

```bash
docker compose logs -f api web
docker compose exec api python manage.py createsuperuser
docker compose down
```
