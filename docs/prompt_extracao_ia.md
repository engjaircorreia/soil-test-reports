# Prompt de Extração por IA

Este documento resume o contrato entre as imagens/PDFs dos ensaios, a IA de extração e os campos usados pelo gerador de planilhas.

## Objetivo

A IA deve extrair dados brutos visíveis nas fichas e devolver um JSON padronizado. Ela não deve calcular variáveis, completar dados ausentes, criar pontos de compactação ou sintetizar leituras de penetração a partir de resultados finais.

Quando um valor não puder ser lido com segurança, deve retornar `null`. O sistema normaliza, calcula, valida e apresenta os campos pendentes para revisão humana.

## Compactação / Proctor

Fonte preferencial: ficha de compactação, geralmente com título de compactação/Proctor e tabela de determinação de umidade.

Campos brutos e lidos:

- `proctor.higroscopica`: quadro de umidade higroscópica da ficha de compactação, com cápsula, peso bruto úmido, peso bruto seco e tara/peso da cápsula, quando existir.
- `proctor.pontos`: pontos visíveis da tabela de compactação, com pesos e cápsulas quando legíveis.
- `proctor.resultado_lido.umidade_otima_percent`: valor final lido no topo direito, perto de `h =`, `w =`, `umidade ótima` ou equivalente.
- `proctor.resultado_lido.densidade_maxima_g_cm3`: valor final lido no topo direito, perto de `gamma máx`, `Ymáx` ou densidade máxima.

O sistema calcula ou confere a curva por algoritmo. A IA não deve criar ponto faltante.

Quando a ficha de compactação e a ficha CBR forem do mesmo material, a umidade higroscópica pode ser reaproveitada entre elas. A IA deve extrair o que estiver visível em cada ficha; a conciliação é feita pelo sistema.

Não usar como resultado final:

- densidade do solo úmido;
- peso bruto úmido;
- peso do solo úmido;
- número de cápsula;
- peso da água;
- peso/molde/equipamento.

## CBR

Fonte preferencial: ficha CBR, com título `CBR`, `I.S.C.` ou `Índice de Suporte California`.

Campos brutos e lidos:

- `cbr.resultado_lido.cbr_percent`: valor final destacado no quadro `I.S.C.`/curva pressão-penetração, se existir.
- `cbr.resultado_lido.expansao_percent`: valor final no bloco `Expansão de amostra inundada`, se existir.
- `cbr.higroscopica`: coluna `HIGROSCÓPICA` do quadro `UMIDADES`, com cápsula, peso bruto úmido, peso bruto seco e tara/peso da cápsula.
- `cbr.moldagem`: coluna `MOLDAGEM` do quadro `UMIDADES`, com cápsula, peso bruto úmido, peso bruto seco e tara/peso da cápsula.
- `cbr.calculo_moldagem`: valores manuscritos do quadro `Cálculos para moldagem do C.P.`, como peso do solo, peso retido/passando na peneira nº 04 e água a juntar.
- `cbr.penetracao`: leituras visíveis da tabela de penetração. Não sintetizar pela porcentagem final.
- `cbr.expansao`: leituras visíveis de expansão.
- `cbr.verificacao_moldagem`: valores manuscritos do quadro `Verificação da moldagem`, como peso bruto do corpo de prova úmido, peso do corpo de prova úmido e densidades.

Não usar como CBR:

- coluna `Padrão`, com valores como `70`, `105`, `133`, `161`, `182`;
- leitura do manômetro;
- tempo;
- penetração;
- pressão/carga;
- dados de equipamento.

O sistema calcula peso da água, peso do solo seco, umidade, diferença de umidade, água a juntar e densidades de verificação. Valores de moldagem/verificação não são inventados; se a IA não extrair, ficam em branco para revisão.

Se `cbr.higroscopica` vier vazio ou incoerente e `proctor.higroscopica` estiver válido, o sistema usa a higroscópica do Proctor como fallback para preencher o CBR e a aba `DENS`. Se ambos vierem válidos e divergentes, os dados são preservados para revisão humana.

## Granulometria

Fonte preferencial: ficha `Granulometria por peneiramento`.

Campos brutos e lidos:

- `granulometria.peneiras`: linhas de peneiramento visíveis, com peneira, abertura, peso retido e/ou percentual passante.
- `granulometria.umidade`: cápsula e pesos da umidade, quando legíveis.
- `granulometria.amostra_total`: pesos de amostra total, quando legíveis.

Não usar como passante:

- peso retido parcial;
- peso que passa acumulado;
- abertura da peneira;
- número da peneira.

## Limites

Quando o material não apresenta limites, usar:

- `LL = NL`
- `LP = NP`
- `IP = NP`

## Conferência

Valores esperados normalmente:

- umidade ótima: `5%` a `20%`;
- densidade máxima: `1.5` a `2.3 g/cm³`;
- CBR: percentual final, não carga padrão;
- expansão: `0%` a `10%`;
- passantes: `0%` a `100%`.

Quando a IA não conseguir distinguir com segurança, deve retornar `null` e explicar em `warnings`.

Blocos de umidade são considerados incoerentes quando violam a ordem física:

```text
peso bruto úmido >= peso bruto seco >= tara da cápsula
```
