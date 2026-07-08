# Docker

O projeto inclui uma configuração Docker simples para execução local e deploy básico.

## Arquivos

- `Dockerfile`: cria a imagem Python do projeto.
- `docker-compose.yml`: sobe o serviço Django e monta `media/` e `output/` como volumes locais.
- `.dockerignore`: evita copiar chaves, caches, ambientes virtuais e arquivos locais para a imagem.
- `.env.example`: exemplo das variáveis de ambiente.

## Configuração

Crie o arquivo `.env` local:

```bash
cp .env.example .env
```

Preencha:

```env
OPENAI_API_KEY=sua-chave-real
OPENAI_MODEL=gpt-4.1-mini
DJANGO_SECRET_KEY=django-insecure-local-dev-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,testserver
```

O arquivo `.env` não deve ser enviado para o GitHub.

## Build

```bash
docker compose build
```

## Execução

```bash
docker compose up
```

O container executa:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Acesse:

```text
http://localhost:8000
```

## Volumes

O `docker-compose.yml` monta:

```text
./media  -> /app/media
./output -> /app/output
```

`media/` recebe uploads e planilhas geradas pelo fluxo web. `output/` pode ser usado por scripts locais. Ambas as pastas devem permanecer fora do Git, exceto arquivos auxiliares como `output/README.md` e `output/.gitkeep`.

## Comandos Úteis

Rodar testes dentro do container:

```bash
docker compose run --rm app pytest
```

Validar modelos Excel:

```bash
docker compose run --rm app python scripts/validate_workbooks.py
```

Verificar configuração Django:

```bash
docker compose run --rm app python manage.py check
```

## Observações

- A extração depende de `OPENAI_API_KEY`.
- O banco padrão é SQLite local do container.
- Para produção real, configure `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, HTTPS, persistência de banco e política de armazenamento dos uploads.
