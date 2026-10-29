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
dados/tempo.json             dados do painel (vazio até a integração com o INMET)
assets/img/                  logo e ícones
manifest.webmanifest         nome e ícone ao salvar na tela inicial
.github/workflows/pages.yml  publicação no GitHub Pages
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

A integração automática com o INMET ainda não foi feita. Antes dela é preciso confirmar com o INMET qual produto e forma de acesso usar, qual estação representa Moeda e, com a Defesa Civil, qual umidade o quadro deve usar. Se a integração exigir credenciais, elas devem ficar fora do navegador (por exemplo, em uma rotina agendada do GitHub Actions que grava `dados/tempo.json`).

## Publicar no GitHub Pages

1. No GitHub, abra **Settings → Pages** e, em **Source**, escolha **GitHub Actions**.
2. Cada envio para a branch `main` publica o site automaticamente pelo workflow `.github/workflows/pages.yml`.
3. O endereço fica em `https://arbayes.github.io/enfrentamento-El-Nino/`. Para o QR Code, prefira um domínio curto e estável da Prefeitura, configurado em **Settings → Pages → Custom domain**.

## Antes de imprimir os QR Codes

- Validar as faixas de umidade e as orientações com a Defesa Civil e a Secretaria Municipal de Saúde.
- Confirmar a identificação institucional da Defesa Civil.
- Confirmar a estação e o produto meteorológico do INMET.
- Publicar telefone ou contato institucional somente depois de confirmado pela Prefeitura.
- Testar links, acessibilidade e o visual em Android e iPhone.
- Atualizar a data de "Última revisão dos textos" no rodapé sempre que o conteúdo mudar.

O conteúdo é informativo e preventivo. Não substitui alertas oficiais, avaliação médica nem os protocolos da Prefeitura e da Defesa Civil.
