# MyTest DMV

DMV test-prep backend (Django/DRF/Wagtail) with the Next.js frontend as a **git submodule** at [`client/`](client/).

- API docs (when running): `/api/docs/`
- Frontend repo: [aregchatalyan/mytestdmv](https://github.com/aregchatalyan/mytestdmv)
- Docker guide: [docs/DOCKER.md](docs/DOCKER.md)
- Backend API notes: [docs/README.md](docs/README.md)

## Quick start (Docker)

```bash
git clone --recurse-submodules https://github.com/GregHayrapetyan/dmv.git
cd dmv
cp .env.example .env   # set SECRET_KEY, DB_PASSWORD, OAuth/Stripe as needed
docker compose up --build
```

## Local development (without Docker)

**Backend**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

**Frontend** (submodule)

```bash
git submodule update --init --recursive
cd client
cp .env.example .env
npm install
npm run dev
```

Point `NEXT_PUBLIC_API_URL` at `http://127.0.0.1:8000/api` (or your API host).
