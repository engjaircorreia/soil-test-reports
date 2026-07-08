# Estrutura do Projeto

Este documento descreve os arquivos que devem compor o repositório público e separa o que é código versionável do que é material local.

## Árvore Principal

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
│   └── validate_workbooks.py
├── tests/
├── docs/
│   ├── en/
│   └── pt-BR/
├── output/
│   ├── .gitkeep
│   └── README.md
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── manage.py
├── pytest.ini
├── requirements.txt
├── README.md
└── README.pt-BR.md
```

## Pastas Versionáveis

`app/` contém a configuração principal do Django.

`ensaios/` contém o app Django, incluindo formulários, views, modelos, templates HTML e serviços técnicos.

`ensaios/services/` concentra a lógica de domínio:

- `extraction_openai.py`: chamada da API da OpenAI e contrato do prompt;
- `schemas.py`: estruturas esperadas para o JSON de extração;
- `normalization.py`: conversão de datas, números e marcadores;
- `calculations.py`: cálculos técnicos determinísticos;
- `technical_validation.py`: validações técnicas e campos obrigatórios;
- `pipeline.py`: orquestração entre extração, normalização, cálculo, validação e revisão;
- `workbook_fill.py`: preenchimento seguro dos modelos Excel;
- `validation.py`: validação dos arquivos `.xlsx`.

`templates/` contém os modelos Excel limpos. Eles devem ser versionados porque são a base funcional do projeto. O preenchimento deve alterar apenas células mapeadas, preservando fórmulas, estilos, desenhos e gráficos.

`static/` contém CSS e JavaScript da interface web.

`scripts/` contém o script de validação usado para conferir a integridade dos modelos Excel.

`tests/` contém a suíte automatizada.

`docs/en/` contém a documentação em inglês.

`docs/pt-BR/` contém a documentação em português brasileiro.

`output/` fica versionada apenas com `.gitkeep` e `README.md`; planilhas geradas são ignoradas.

## Pastas e Arquivos Locais

Estes itens não devem ser enviados ao GitHub:

- `.env`;
- `db.sqlite3`;
- `.venv_xlsx/` ou qualquer ambiente virtual;
- `.pytest_cache/`;
- `__pycache__/`;
- `media/`;
- `local_files/`;
- `testelocal/`;
- fotos, PDFs e planilhas reais de ensaio;
- planilhas `.xlsx` e PDFs gerados.

## Fluxo de Dados

```text
upload
  -> extração por IA em JSON bruto
  -> normalização Python
  -> cálculo Python
  -> validação técnica
  -> revisão humana
  -> preenchimento do Excel
  -> download
```

A IA deve apenas extrair dados visíveis. O sistema calcula valores derivados e bloqueia ou sinaliza campos incoerentes para revisão.
