# Higiene do Repositório

Use esta lista antes de publicar ou enviar o projeto para o GitHub.

## Incluir

- Código Django: `app/`, `ensaios/`
- Arquivos estáticos: `static/`
- Modelos Excel limpos: `templates/*.xlsx`
- Testes: `tests/`
- Scripts: `scripts/`
- Documentação: `README.md`, `README.pt-BR.md`, `docs/`
- Exemplos de configuração: `.env.example`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.gitignore`, `pytest.ini`, `requirements.txt`
- Marcadores de saída: `output/.gitkeep`, `output/README.md`

## Excluir

- Chaves reais de API: `.env`
- Bancos locais: `db.sqlite3`, `*.sqlite3`
- Ambientes virtuais: `.venv_xlsx/`, `.venv*/`, `venv/`
- Caches Python: `__pycache__/`, `.pytest_cache/`
- Uploads e arquivos gerados: `media/`, planilhas `.xlsx` e PDFs gerados
- Material bruto local: `local_files/`, `testelocal/`, `ENSAIOS/`
- Notas internas de planejamento: `PLANO_IMPLEMENTACAO_DJANGO.md`, `PROMPTS_IMPLEMENTACAO.md`, arquivos `plano*.md`, `prompt*.md` e `prompts*.md` na raiz
- Arquivos temporários do Excel: `~$*.xlsx`

## Verificação Recomendada Antes do Push

```bash
python manage.py check
pytest
python scripts/validate_workbooks.py
node --check static/js/app.js
```

## Observações

O `README.md` da raiz está em inglês para o GitHub. A versão em português é `README.pt-BR.md`.
