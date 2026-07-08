# Gerador de Relatórios de Ensaios de Solos

Aplicação Django simples para gerar planilhas Excel de ensaios laboratoriais de solos. O fluxo atual atende modelos de Proctor/CBR e granulometria em português e inglês.

A aplicação permite enviar imagens ou PDFs, extrair os dados visíveis com a API da OpenAI, revisar os valores extraídos e baixar as planilhas preenchidas.

## Fluxo

```text
upload dos arquivos -> IA extrai JSON bruto -> Python normaliza -> Python calcula -> Python valida -> usuário revisa -> Excel é preenchido
```

A IA é usada apenas para extração. Os cálculos técnicos ficam em serviços Python determinísticos, e valores incertos ou ilegíveis retornam como `null` para revisão humana.

## Recursos

- Upload de até três imagens ou PDFs por job.
- Classificação automática dos arquivos de Proctor, CBR e granulometria.
- Modelos Excel em português e inglês.
- Etapa obrigatória de revisão humana antes da geração.
- Cálculos determinísticos para umidades, pontos Proctor, verificações CBR e granulometria.
- Validação técnica antes da saída.
- Suporte a Docker para execução/deploy simples.
- Testes automatizados para contratos de extração, cálculos, validação e geração de planilhas.

## Estrutura do Projeto

```text
.
├── app/                  # Configuração e URLs principais do Django
├── ensaios/              # App Django, formulários, views, modelos e serviços
│   └── services/         # Extração, normalização, cálculos e preenchimento Excel
├── templates/            # Modelos Excel limpos em PT e EN
├── static/               # CSS e JavaScript da interface web
├── scripts/              # Script de validação das planilhas
├── docs/                 # Documentação do projeto
├── output/               # Pasta de saída para scripts locais
├── tests/                # Testes automatizados
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

Arquivos locais, fotos brutas, mídia gerada, banco SQLite, ambientes virtuais e sandboxes de teste são ignorados pelo Git.

## Requisitos

- Python 3.12+
- Chave da API da OpenAI
- Docker, opcional

## Instalação

Clone o repositório:

```bash
git clone git@github.com:engjaircorreia/soil-test-reports.git
cd soil-test-reports
```

Se preferir HTTPS:

```bash
git clone https://github.com/engjaircorreia/soil-test-reports.git
cd soil-test-reports
```

Crie o ambiente virtual:

```bash
python3 -m venv .venv_xlsx
source .venv_xlsx/bin/activate
pip install -r requirements.txt
```

Crie seu arquivo `.env` local:

```bash
cp .env.example .env
```

Depois preencha:

```env
OPENAI_API_KEY=sua-chave-da-openai
OPENAI_MODEL=gpt-4.1-mini
DJANGO_SECRET_KEY=django-insecure-local-dev-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,testserver
```

Não envie `.env` para o Git.

## Execução Local

```bash
python manage.py migrate
python manage.py runserver
```

Acesse:

```text
http://localhost:8000
```

## Execução com Docker

```bash
cp .env.example .env
docker compose build
docker compose up
```

Acesse:

```text
http://localhost:8000
```

Mais detalhes em [docs/pt-BR/docker.md](docs/pt-BR/docker.md).

## Testes e Validação

```bash
python manage.py check
pytest
python scripts/validate_workbooks.py
node --check static/js/app.js
```

O `openpyxl` é usado para leitura e validação. As planilhas geradas são preenchidas editando diretamente partes XML do arquivo Excel, o que ajuda a preservar fórmulas, desenhos, gráficos e formatação dos modelos originais.

## Modelos Excel

Os modelos versionados são:

- `templates/compactacao_cbr_modelo_limpo.xlsx`
- `templates/compaction_cbr_clean_template_en.xlsx`
- `templates/granulometria_modelo_limpo.xlsx`
- `templates/granulometry_clean_template_en.xlsx`

As planilhas geradas pelo fluxo web ficam em `media/generated/`. As saídas de scripts locais ficam em `output/`. Esses arquivos gerados são ignorados pelo Git.

## Notas de Confiabilidade

- A extração por IA deve retornar apenas valores brutos visíveis.
- Valores ausentes, ambíguos ou ilegíveis permanecem como `null`.
- O Python calcula valores derivados, como peso da água, peso do solo seco, umidade, água a juntar e verificação de moldagem.
- Pontos de Proctor e leituras de penetração CBR não são sintetizados a partir dos resultados finais.
- O fluxo Proctor/CBR pode reaproveitar uma umidade higroscópica válida entre Proctor e CBR quando uma ficha estiver ilegível ou incoerente.
- Umidades válidas divergentes são mantidas para revisão humana.

## Documentação

- [README em inglês](README.md)
- [Documentação em português](docs/pt-BR/README.md)
- [Documentação em inglês](docs/en/README.md)
- [Estrutura do projeto](docs/pt-BR/estrutura_do_projeto.md)
- [Guia Docker](docs/pt-BR/docker.md)
- [Mapa de células](docs/pt-BR/mapa_de_celulas.md)
- [Contrato do prompt de extração por IA](docs/pt-BR/prompt_extracao_ia.md)
- [Checklist de higiene do repositório](docs/pt-BR/higiene_repositorio.md)

## Higiene do Repositório

Antes de publicar, mantenha no Git apenas código-fonte, modelos, testes e documentação. Não envie:

- `.env`
- `db.sqlite3`
- `.venv_xlsx/` ou qualquer ambiente virtual
- `.pytest_cache/`
- `__pycache__/`
- `media/`
- `local_files/`
- `testelocal/`
- notas internas de planejamento, como `PLANO_IMPLEMENTACAO_DJANGO.md` e `PROMPTS_IMPLEMENTACAO.md`
- planilhas `.xlsx` ou PDFs gerados
