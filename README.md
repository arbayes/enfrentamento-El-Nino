# Moeda preparada para o El Niño 2026/2027

Site informativo da **Prefeitura Municipal de Moeda (MG)** e da **Defesa Civil de Moeda** para orientar a população sobre o El Niño 2026/2027. Ele foi pensado para ser aberto por QR Code em áreas públicas: carrega rápido no celular, não pede login e não coleta dados pessoais.

O conteúdo segue a *Proposta de Site da Defesa Civil de Moeda (versão população geral)* e o *Caderno Técnico-Operacional de Enfrentamento ao El Niño 2026/2027*.

## O que tem na página

1. Cabeçalho com a logo da Prefeitura, a Defesa Civil e o título da campanha.
2. O que é o El Niño e o que pode acontecer em Moeda.
3. Painel do tempo (umidade, previsão, estação de referência e horário da atualização).
4. Quadro de umidade do ar com os níveis Acompanhar, Atenção, Alerta e Emergência.
5. Cuidados com o calor e o sol.
6. Prevenção de dengue, chikungunya e zika.
7. Links oficiais (INMET e Ministério da Saúde).
8. Rodapé com realização, apoio e data da última revisão dos textos.

## Estrutura

```
index.html                   página única
css/estilo.css               estilos (mobile-first, cores #164370 e #286896)
js/painel.js                 preenche o painel do tempo a partir de dados/tempo.json
dados/tempo.json             dados do painel (preenchido na publicação pelo coletor)
scripts/coletar_tempo.py     coleta os dados do INMET e grava dados/tempo.json
tests/                       testes do coletor, com respostas simuladas do INMET
assets/img/                  logo e ícones
manifest.webmanifest         nome e ícone ao salvar na tela inicial
.github/workflows/pages.yml  coleta do INMET e publicação no GitHub Pages, de hora em hora
```

Não há etapa de build: são arquivos estáticos.

## Ver no computador

```bash
python3 -m http.server 8000
# abra http://localhost:8000
```

## Painel do tempo

O painel lê `dados/tempo.json`. Enquanto o arquivo estiver vazio, incompleto ou com mais de 6 horas, a página mostra **"Dados temporariamente indisponíveis"** e o botão para o INMET. Nenhum valor é inventado.

Formato esperado:

```json
{
  "fonte": "INMET",
  "estacao": "Nome da estação e município",
  "atualizado_em": "2026-10-29T14:00:00-03:00",
  "umidade": { "valor": 25, "tipo": "observada" },
  "previsao": [
    { "data": "2026-10-29", "condicao": "Sol com poucas nuvens", "temp_min": 17, "temp_max": 31 }
  ]
}
```

`umidade.tipo` pode ser `observada`, `prevista` ou `minima_prevista`, e o texto do painel muda conforme a escolha. Quando há dados, o nível correspondente é destacado no quadro de umidade.

`previsao[].umidade_min` também é gravado pelo coletor, mas o painel não o exibe.

### De onde vêm os dados

O workflow `pages.yml` roda a cada push na `main` e de hora em hora (minuto 20). Antes de publicar, ele executa `scripts/coletar_tempo.py`, que consulta o INMET fora do navegador:

| Dado | Endereço | Token |
|---|---|---|
| Previsão de Moeda (código IBGE 3142304) | `apiprevmet3.inmet.gov.br/previsao/3142304` | Não |
| Lista de estações | `apitempo.inmet.gov.br/estacoes/T` | Não |
| Medições horárias da estação | `apitempo.inmet.gov.br/token/estacao/{início}/{fim}/{código}/{token}` | Sim |

- **Com token:** o coletor escolhe a estação automática operante mais próxima de Moeda (até 60 km; a candidata esperada é a A555 Ibirité/Rola Moça) e usa a última umidade medida, se tiver no máximo 3 horas. As horas do INMET vêm em UTC e são gravadas no horário de Brasília.
- **Sem token, ou se a estação falhar:** a umidade vem da previsão (`minima_prevista`, a menor umidade prevista para hoje).
- **Se o INMET estiver fora do ar:** o coletor mantém o arquivo já publicado. Depois de 6 horas sem atualização, o painel mostra "Dados temporariamente indisponíveis".

Os avisos de cada coleta aparecem na aba **Actions** do GitHub. O token nunca é escrito no log nem no arquivo.

### Ativar as medições da estação

1. Pedir o token de acesso à API ao INMET, de preferência por e-mail institucional da Prefeitura ou da Defesa Civil.
2. No GitHub, abrir **Settings → Secrets and variables → Actions → New repository secret**, com o nome `INMET_TOKEN` e o token como valor.
3. Rodar o workflow manualmente em **Actions → Publicar no GitHub Pages → Run workflow** e conferir o log. Se o INMET indicar outro formato de endereço para o token, ajuste `URL_MEDICOES` em `scripts/coletar_tempo.py`.

### Testar o coletor

```bash
python3 -m unittest discover -s tests       # sem rede, com respostas simuladas
python3 scripts/coletar_tempo.py --saida /tmp/tempo.json   # consulta o INMET de verdade
```

O GitHub pausa workflows agendados depois de 60 dias sem atividade no repositório. Se o painel ficar "indisponível" por muito tempo, confira se a rotina está ativa na aba **Actions**.

## Publicar no GitHub Pages

1. No GitHub, abra **Settings → Pages** e, em **Source**, escolha **GitHub Actions**.
2. Cada envio para a branch `main` publica o site automaticamente pelo workflow `.github/workflows/pages.yml`.
3. O endereço fica em `https://arbayes.github.io/enfrentamento-El-Nino/`. Para o QR Code, prefira um domínio curto e estável da Prefeitura, configurado em **Settings → Pages → Custom domain**.

## Antes de imprimir os QR Codes

- Validar as faixas de umidade e as orientações com a Defesa Civil e a Secretaria Municipal de Saúde.
- Confirmar a identificação institucional da Defesa Civil.
- Confirmar com o INMET a estação de referência e cadastrar o `INMET_TOKEN`.
- Publicar telefone ou contato institucional somente depois de confirmado pela Prefeitura.
- Testar links, acessibilidade e o visual em Android e iPhone.
- Atualizar a data de "Última revisão dos textos" no rodapé sempre que o conteúdo mudar.

O conteúdo é informativo e preventivo. Não substitui alertas oficiais, avaliação médica nem os protocolos da Prefeitura e da Defesa Civil.
