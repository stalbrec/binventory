# CLAUDE.md

Guidance for Claude Code (and other AI assistants) working in this repository.

## What this project is

**binventory** ("Unser kleines Inventar" / "our little inventory") is a personal
home-inventory tracker: label physical storage boxes, print QR codes for them,
scan to find what's inside, and browse items in a searchable table. It's a
single-app Django project built for personal/home use, not a multi-tenant SaaS
— there's no signup flow, one login form, and some UI strings are in German.

Core features:
- `Box` and `Item` models — items live in boxes.
- QR code generation per box (SVG, embedded as data URIs) and a bulk
  "download all QR codes" zip export.
- A hand-drawn SVG diagram of an item's shelf location (see Quirks below).
- Excel import/export of the whole inventory (`openpyxl`).
- Installable as a PWA (`django-pwa`).

## Tech stack

- **Django 5.1+**, Python 3.12 (pinned in `.python-version`).
- **uv** for dependency management (`pyproject.toml` + `uv.lock`). No
  `requirements.txt`.
- **django-tailwind v4 + daisyUI v5** for styling (themes: `nord` light /
  `dim` dark, see `DAISYUI_LIGHT_THEME` / `DAISYUI_DARK_THEME` in settings).
- **jQuery + DataTables** (loaded via CDN in `base.html`) power the inventory
  table. There is **no HTMX** anywhere in this codebase despite the modern
  Tailwind/daisyUI look — interactions are plain full-page POST/redirect.
- **qrcode** + **Pillow** for QR/SVG generation.
- **openpyxl** for Excel import/export.
- **psycopg** + Postgres in Docker; sqlite3 is the default when no
  `DATABASE_ENGINE` env var is set (convenient for bare local dev).
- **whitenoise** for serving static files; **gunicorn** in production.
- **django-browser-reload** in DEBUG mode only (not htmx-based).

## Repository layout

```
binventory/
├── binventory/            # Django project config
│   ├── settings.py        # single settings module, no dev/prod split
│   ├── urls.py             # root URLconf
│   └── wsgi.py
├── inventory/              # the one Django app — all domain logic lives here
│   ├── models.py            # Box, Item
│   ├── views.py              # FBVs + CBVs: index, item/box detail, import/export, QR zip
│   ├── utils.py               # QR code SVG generation + shelf-location SVG diagram
│   ├── urls.py                  # app_name = "inventory"
│   ├── admin.py                  # bare admin.site.register, no ModelAdmin customization
│   ├── context_processors.py      # exposes daisyUI theme names to all templates
│   ├── migrations/                 # only 0001_initial.py — young project
│   ├── templates/inventory/         # base.html, index.html, box.html, item.html, new.html, import.html
│   └── templates/registration/       # login.html (standalone, doesn't extend base.html)
├── theme/                  # django-tailwind theme app (TAILWIND_APP_NAME="theme")
│   └── static_src/          # its own package.json — Tailwind 4, daisyUI 5, postcss
├── static/images/           # favicons / PWA icons
├── manage.py
├── Dockerfile               # 3-stage build (base → builder → final)
├── compose.yml               # postgres + app services
├── entrypoint.sh               # migrate + collectstatic + gunicorn
├── pyproject.toml / uv.lock
└── .python-version           # 3.12
```

There is no `tests/` directory, no CI config (`.github/workflows` does not
exist), and no committed lint/type-check config — see "What's absent" below.

## Models & URLs

`inventory/models.py`:
- `Box(name: CharField(20), location: CharField(50))` — `__str__` →
  `"{name} ({location})"`.
- `Item(name: CharField(200), box: FK(Box, on_delete=CASCADE))` — has a
  `location()` method that delegates to `self.box.location` (not a DB field).

`inventory/urls.py` (`app_name = "inventory"`, mounted at root in
`binventory/urls.py`):

| Path | View | Name |
|---|---|---|
| `""` | `IndexView` | `index` |
| `"new"` | `new_item` | `new` |
| `"import"` | `import_excel` | `import` |
| `"export"` | `export_excel` | `export` |
| `"qrcodes"` | `download_all_box_qr_codes` | `qrcodes` |
| `"item/<int:pk>"` | `ItemView` | `item` |
| `"box/<int:pk>"` | `BoxView` | `box` |
| `"login/"` | `CustomLoginView` | `login` |

`BoxAwareDetailView` is a small shared base `DetailView` (injects
`available_boxes` into context) that `ItemView` and `BoxView` both extend —
the one reuse pattern of note in `views.py`.

## Development workflow

All commands go through `uv` — there's no Makefile/justfile.

```bash
uv sync                                   # install dependencies
cp .env.example .env                      # if you create one; otherwise write your own .env
uv run python manage.py migrate
uv run python manage.py createsuperuser   # to get an admin/login user
uv run python manage.py runserver
```

Tailwind CSS needs its own process, run separately from `runserver`:

```bash
uv run python manage.py tailwind install   # first time only, installs npm deps
uv run python manage.py tailwind start     # dev watch mode
uv run python manage.py tailwind build     # one-off production build
```

### Environment variables (loaded from `.env` via python-dotenv)

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Django `SECRET_KEY` |
| `DJANGO_DEBUG` | `False` | `DEBUG`; also toggles Tailwind dev mode and browser-reload |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1` | comma-separated `ALLOWED_HOSTS` (reused as `INTERNAL_IPS`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://127.0.0.1` | comma-separated `CSRF_TRUSTED_ORIGINS` |
| `DATABASE_ENGINE` | `sqlite3` | Django DB engine suffix, e.g. `postgresql` |
| `DATABASE_NAME` | `mydb` | |
| `DATABASE_USERNAME` | `myuser` | |
| `DATABASE_PASSWORD` | `mypassword` | |
| `DATABASE_HOST` | `postgres` | |
| `DATABASE_PORT` | `5432` | |

No `.env.example` is committed; the table above is the full set of vars the
app reads.

### Docker

```bash
docker compose up   # postgres + app; requires a .env.prod file (not committed)
```

The Dockerfile is a 3-stage build: `base` installs `uv` + Node + Python deps,
`builder` runs `tailwind install`/`tailwind build`/`collectstatic` (so CSS is
compiled and static files collected **at image build time**), and the final
stage copies only the built artifacts into a slim image (no Node in the
runtime image). `entrypoint.sh` runs `migrate` + `collectstatic` + `gunicorn`
at container start.

## What's absent (don't assume otherwise)

- **No test suite.** No `tests.py`, no pytest config. Don't invent test
  commands; if asked to add tests, you're introducing the first ones.
- **No CI.** No `.github/workflows`.
- **No committed lint/format/type-check config** (no ruff config, no mypy,
  no pre-commit). Commit history (`make ruff happy`) shows `ruff` has been
  run ad hoc via `uvx ruff check .` / `uvx ruff format .` — reasonable to use
  the same if asked to lint, but there's no enforced config to follow.
- **No CONTRIBUTING.md.**

## Conventions

- **Commit messages**: short, lowercase, no Conventional Commits prefixes, no
  trailing period — e.g. `fix new item view`, `adding cross-reference urls to
  boxes and items in model views`, `make ruff happy`. Match this style.
- **One Django app** (`inventory`) holds all domain logic; don't split into
  per-feature apps unless asked.
- Views mix function-based views and class-based generic views in the same
  `views.py` — follow whichever style fits the existing view being touched
  rather than converting wholesale.
- No DRF/API layer — this is a server-rendered app.
- Templates use daisyUI/Tailwind utility classes (`btn`, `card`,
  `table-zebra`, `input-bordered`, etc.); `inventory/templates/inventory/base.html`
  is the shared layout (note `registration/login.html` intentionally does
  *not* extend it).

## Known quirks (pre-existing — don't "fix" incidentally)

- `MIDDLEWARE` in `binventory/settings.py` lists `SecurityMiddleware` twice.
- Module-level `logging.error(...)` calls are used as ad hoc debug output in
  `binventory/settings.py` (logs `ALLOWED_HOSTS` at import time) and in
  `BoxView` (`views.py`, logs the QR code base64 string).
- `export_excel`'s xlsx MIME type is misspelled:
  `application/vnd.openxmlformats-officedocument.speadsheetml.sheet`.
- `generate_location_svg` in `inventory/utils.py` parses locations matching
  `"{prefix}-(\d+)-(\d+)-(\d+)"` and is hardcoded to `prefix="Hobbyraum"` in
  `views.py` — this is specific to the original author's shelving setup, not
  a generalized/configurable feature.
- The `postgres` healthcheck in `compose.yml` passes `echo`/`&&`/`pg_isready`
  as separate argv elements rather than a shell string, so it likely doesn't
  chain the way it looks like it should.

If you touch code near any of these, flag it rather than silently changing
behavior beyond what was asked.
