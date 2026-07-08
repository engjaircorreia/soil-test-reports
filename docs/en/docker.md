# Docker

The project includes a simple Docker setup for local execution and basic deployment.

## Files

- `Dockerfile`: builds the Python application image.
- `docker-compose.yml`: starts the Django service and mounts `media/` and `output/` as local volumes.
- `.dockerignore`: keeps secrets, caches, virtual environments and local files out of the image build context.
- `.env.example`: environment variable example.

## Configuration

Create a local `.env` file:

```bash
cp .env.example .env
```

Set:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
DJANGO_SECRET_KEY=django-insecure-local-dev-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,testserver
```

Do not commit `.env`.

## Build

```bash
docker compose build
```

## Run

```bash
docker compose up
```

The container runs:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Open:

```text
http://localhost:8000
```

## Volumes

`docker-compose.yml` mounts:

```text
./media  -> /app/media
./output -> /app/output
```

`media/` receives uploads and generated workbooks from the web workflow. `output/` can be used by local scripts. Both folders should stay out of Git, except helper files such as `output/README.md` and `output/.gitkeep`.

## Useful Commands

Run tests inside the container:

```bash
docker compose run --rm app pytest
```

Validate Excel templates:

```bash
docker compose run --rm app python scripts/validate_workbooks.py
```

Check Django settings:

```bash
docker compose run --rm app python manage.py check
```

## Notes

- Extraction depends on `OPENAI_API_KEY`.
- The default database is local SQLite.
- For real production use, configure `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, HTTPS, persistent database storage and an upload retention policy.
