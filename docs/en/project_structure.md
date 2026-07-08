# Project Structure

This document describes the public repository layout and separates versioned source files from local working material.

## Main Tree

```text
.
├── app/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── ensaios/
│   ├── forms.py
│   ├── models.py
│   ├── services/
│   │   ├── calculations.py
│   │   ├── extraction_openai.py
│   │   ├── normalization.py
│   │   ├── pipeline.py
│   │   ├── schemas.py
│   │   ├── technical_validation.py
│   │   ├── validation.py
│   │   └── workbook_fill.py
│   ├── templates/
│   │   └── ensaios/
│   ├── migrations/
│   ├── urls.py
│   └── views.py
├── static/
│   ├── css/
│   │   └── app.css
│   └── js/
│       └── app.js
├── templates/
│   ├── compactacao_cbr_modelo_limpo.xlsx
│   ├── compaction_cbr_clean_template_en.xlsx
│   ├── granulometria_modelo_limpo.xlsx
│   └── granulometry_clean_template_en.xlsx
├── scripts/
├── tests/
├── docs/
│   ├── en/
│   └── pt-BR/
├── output/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── manage.py
├── pytest.ini
├── requirements.txt
├── README.md
└── README.pt-BR.md
```

## Versioned Folders

`app/` contains the main Django project configuration.

`ensaios/` contains the Django app, including forms, views, models, HTML templates and technical services.

`ensaios/services/` contains the domain logic:

- `extraction_openai.py`: OpenAI API call and extraction prompt contract;
- `schemas.py`: expected extraction JSON structures;
- `normalization.py`: dates, numeric values and marker normalization;
- `calculations.py`: deterministic technical calculations;
- `technical_validation.py`: technical validation and required fields;
- `pipeline.py`: extraction, normalization, calculation, validation and review orchestration;
- `workbook_fill.py`: safe Excel template filling;
- `validation.py`: `.xlsx` workbook validation.

`templates/` contains the clean Excel templates. These files are versioned because they are core functional assets. The generator should only change mapped cells and preserve formulas, styles, drawings and charts.

`static/` contains CSS and JavaScript for the web UI.

`scripts/` contains maintenance, diagnostic and validation scripts.

`tests/` contains the automated test suite.

`docs/en/` contains English documentation.

`docs/pt-BR/` contains Brazilian Portuguese documentation.

`output/` is versioned only with `.gitkeep` and `README.md`; generated workbooks are ignored.

## Local-Only Files

Do not commit:

- `.env`;
- `db.sqlite3`;
- `.venv_xlsx/` or any virtual environment;
- `.pytest_cache/`;
- `__pycache__/`;
- `media/`;
- `local_files/`;
- `testelocal/`;
- raw lab photos, PDFs or real worksheets;
- generated `.xlsx` and `.pdf` files.

## Data Flow

```text
upload
  -> AI extraction as raw JSON
  -> Python normalization
  -> Python calculations
  -> technical validation
  -> human review
  -> Excel filling
  -> download
```

The AI extracts visible data only. The system calculates derived values and flags inconsistent or missing fields for review.
