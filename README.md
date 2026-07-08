# Soil Lab Report Generator

A small Django application for generating Excel reports from soil laboratory test sheets. The current workflow supports Proctor/CBR and sieve analysis templates in Portuguese and English.

The application lets a user upload images or PDFs, extract visible lab data with the OpenAI API, review the extracted values, and download filled Excel workbooks.

## Workflow

```text
upload files -> AI extracts raw JSON -> Python normalizes -> Python calculates -> Python validates -> user reviews -> Excel is filled
```

The AI is used only for extraction. Technical calculations are handled by deterministic Python services, and uncertain or unreadable values are returned as `null` for human review.

## Features

- Upload up to three images or PDFs per job.
- Automatic file classification for Proctor, CBR and granulometry sheets.
- Portuguese and English Excel templates.
- Human review step before workbook generation.
- Deterministic calculations for moisture, Proctor points, CBR checks and granulometry.
- Technical validation before output.
- Docker support for simple deployment.
- Automated tests for extraction contracts, calculations, validation and workbook generation.

## Project Structure

```text
.
├── app/                  # Django project settings and URLs
├── ensaios/              # Django app, forms, views, models and services
│   └── services/         # Extraction, normalization, calculations and Excel filling
├── templates/            # Clean Excel templates in PT and EN
├── static/               # CSS and JavaScript for the web UI
├── scripts/              # Maintenance and validation scripts
├── docs/                 # Project documentation
├── output/               # Local script output folder
├── tests/                # Automated tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

Local-only files such as raw lab photos, generated media, SQLite databases, virtual environments and test sandboxes are ignored by Git.

## Requirements

- Python 3.12+
- OpenAI API key
- Docker, optional

## Environment

Create a virtual environment:

```bash
python3 -m venv .venv_xlsx
source .venv_xlsx/bin/activate
pip install -r requirements.txt
```

Create your local `.env` file:

```bash
cp .env.example .env
```

Then set:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
DJANGO_SECRET_KEY=django-insecure-local-dev-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,testserver
```

Do not commit `.env`.

## Run Locally

```bash
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://localhost:8000
```

## Run With Docker

```bash
cp .env.example .env
docker compose build
docker compose up
```

Open:

```text
http://localhost:8000
```

More details are available in [docs/docker.md](docs/docker.md).

## Tests and Validation

```bash
python manage.py check
pytest
python scripts/validate_workbooks.py
node --check static/js/app.js
```

`openpyxl` is used for reading and validation. The generated `.xlsx` files are filled by editing the workbook XML parts directly, which helps preserve formulas, drawings, charts and formatting from the original Excel templates.

## Excel Templates

The versioned templates are:

- `templates/compactacao_cbr_modelo_limpo.xlsx`
- `templates/compaction_cbr_clean_template_en.xlsx`
- `templates/granulometria_modelo_limpo.xlsx`
- `templates/granulometry_clean_template_en.xlsx`

Generated workbooks are written to `media/generated/` in the web workflow and to `output/` when using local scripts. These generated files are ignored by Git.

## Reliability Notes

- AI extraction must return raw visible values only.
- Missing or ambiguous values must remain `null`.
- Python calculates derived values such as water mass, dry soil mass, moisture, water to add and mold verification values.
- Proctor points and CBR penetration readings are not synthesized from final results.
- The Proctor/CBR workflow can reuse a valid hygroscopic moisture block between Proctor and CBR when one sheet is unreadable or inconsistent.
- Divergent valid moisture blocks are kept for human review.

## Documentation

- [Portuguese README](README.pt-BR.md)
- [Project structure](docs/estrutura_do_projeto.md)
- [Docker guide](docs/docker.md)
- [Cell map](docs/mapa_de_celulas.md)
- [AI extraction prompt contract](docs/prompt_extracao_ia.md)
- [Repository hygiene checklist](docs/repository_hygiene.md)

## Repository Hygiene

Before publishing, keep only source code, templates, tests and documentation in Git. Do not commit:

- `.env`
- `db.sqlite3`
- `.venv_xlsx/` or any virtual environment
- `.pytest_cache/`
- `__pycache__/`
- `media/`
- `local_files/`
- `testelocal/`
- internal planning notes such as `PLANO_IMPLEMENTACAO_DJANGO.md` and `PROMPTS_IMPLEMENTACAO.md`
- generated `.xlsx` or `.pdf` files
