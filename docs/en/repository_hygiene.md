# Repository Hygiene

Use this checklist before publishing or pushing the project to GitHub.

## Include

- Django source code: `app/`, `ensaios/`
- Static assets: `static/`
- Clean Excel templates: `templates/*.xlsx`
- Tests: `tests/`
- Scripts: `scripts/`
- Documentation: `README.md`, `README.pt-BR.md`, `docs/`
- Configuration examples: `.env.example`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.gitignore`, `pytest.ini`, `requirements.txt`
- Output placeholders: `output/.gitkeep`, `output/README.md`

## Exclude

- Real API keys: `.env`
- Local databases: `db.sqlite3`, `*.sqlite3`
- Virtual environments: `.venv_xlsx/`, `.venv*/`, `venv/`
- Python caches: `__pycache__/`, `.pytest_cache/`
- Uploaded and generated files: `media/`, generated `.xlsx` and `.pdf`
- Local raw material: `local_files/`, `testelocal/`, `ENSAIOS/`
- Internal planning notes: `PLANO_IMPLEMENTACAO_DJANGO.md`, `PROMPTS_IMPLEMENTACAO.md`, root-level `plano*.md`, `prompt*.md` and `prompts*.md`
- Excel temporary files: `~$*.xlsx`

## Suggested Pre-Push Check

```bash
python manage.py check
pytest
python scripts/validate_workbooks.py
node --check static/js/app.js
```

## Notes

The root `README.md` is intentionally written in English for GitHub. The Portuguese version is `README.pt-BR.md`.
