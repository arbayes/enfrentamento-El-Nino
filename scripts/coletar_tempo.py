#!/usr/bin/env python3
"""
Coleta os dados do tempo do INMET para Moeda (MG) e grava dados/tempo.json.

Roda no GitHub Actions (workflow pages.yml), nunca no navegador.

- Previsão por município: aberta, sem token.
- Medição da estação automática mais próxima: exige o token do INMET,
  lido da variável de ambiente INMET_TOKEN (segredo do repositório).

Se a estação falhar, a umidade vem da previsão (menor umidade prevista
para hoje). Se tudo falhar, reaproveita o arquivo publicado anteriormente
(--anterior); o painel o considera desatualizado depois de 6 horas e
mostra "Dados temporariamente indisponíveis". Nenhum valor é inventado.

Usa só a biblioteca padrão do Python.
"""
import argparse
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

GEOCODIGO_MOEDA = "3142304"  # código IBGE de Moeda (MG)
LAT_MOEDA, LON_MOEDA = -20.3314, -44.0537
RAIO_MAXIMO_KM = 60  # estação mais longe que isso não representa Moeda
IDADE_MAXIMA_MEDICAO = timedelta(hours=3)

URL_PREVISAO = "https://apiprevmet3.inmet.gov.br/previsao/{geocodigo}"
URL_ESTACOES = "https://apitempo.inmet.gov.br/estacoes/T"
URL_MEDICOES = "https://apitempo.inmet.gov.br/token/estacao/{inicio}/{fim}/{codigo}/{token}"

BRASILIA = timezone(timedelta(hours=-3))
TURNOS = ("manha", "tarde", "noite")


def baixar_json(url, tempo_limite=30):
    req = urllib.request.Request(url, headers={"User-Agent": "site-el-nino-moeda/1.0"})
    with urllib.request.urlopen(req, timeout=tempo_limite) as resp:
        corpo = resp.read()
    if not corpo.strip():
        raise ValueError("resposta vazia")
    return json.loads(corpo)


def numero(valor):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


def distancia_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# ---------- previsão ----------

def ler_previsao(bruto):
    """Converte a resposta de /previsao/{geocodigo} na lista do painel."""
    dias = bruto.get(GEOCODIGO_MOEDA) if isinstance(bruto, dict) else None
    if not isinstance(dias, dict):
        raise ValueError("previsão sem o município")

    previsao = []
    for chave, dia in dias.items():
        try:
            data = datetime.strptime(chave, "%d/%m/%Y").date()
        except ValueError:
            continue
        if not isinstance(dia, dict):
            continue
        # Os primeiros dias vêm divididos em manhã, tarde e noite; os demais, inteiros.
        partes = [dia[t] for t in TURNOS if isinstance(dia.get(t), dict)] or [dia]

        maximas = [v for v in (numero(p.get("temp_max")) for p in partes) if v is not None]
        minimas = [v for v in (numero(p.get("temp_min")) for p in partes) if v is not None]
        umidades = [v for v in (numero(p.get("umidade_min")) for p in partes) if v is not None]
        principal = dia.get("tarde") if isinstance(dia.get("tarde"), dict) else partes[0]

        previsao.append({
            "data": data.isoformat(),
            "condicao": (principal.get("resumo") or "").strip(),
            "temp_min": min(minimas) if minimas else None,
            "temp_max": max(maximas) if maximas else None,
            "umidade_min": min(umidades) if umidades else None,
        })

    previsao.sort(key=lambda d: d["data"])
    if not previsao:
        raise ValueError("previsão vazia")
    return previsao


# ---------- estação ----------

def escolher_estacao(estacoes):
    """A estação automática operante mais próxima de Moeda, dentro do raio."""
    candidatas = []
    for e in estacoes:
        if str(e.get("CD_SITUACAO", "")).strip().lower() != "operante":
            continue
        lat, lon = numero(e.get("VL_LATITUDE")), numero(e.get("VL_LONGITUDE"))
        if lat is None or lon is None or not e.get("CD_ESTACAO"):
            continue
        km = distancia_km(LAT_MOEDA, LON_MOEDA, lat, lon)
        if km <= RAIO_MAXIMO_KM:
            candidatas.append((km, e))
    if not candidatas:
        return None, None
    km, estacao = min(candidatas, key=lambda c: c[0])
    return estacao, km


def ultima_medicao(medicoes, agora):
    """A medição mais recente com umidade, desde que não esteja velha."""
    melhor = None
    for m in medicoes:
        umidade = numero(m.get("UMD_INS"))
        if umidade is None:
            continue
        try:
            # DT_MEDICAO + HR_MEDICAO estão em UTC (ex.: "2026-10-29" e "1500").
            quando = datetime.strptime(
                f"{m['DT_MEDICAO']} {str(m['HR_MEDICAO']).zfill(4)}", "%Y-%m-%d %H%M"
            ).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if melhor is None or quando > melhor[0]:
            melhor = (quando, umidade)
    if melhor is None or agora - melhor[0] > IDADE_MAXIMA_MEDICAO:
        return None
    return melhor


def nome_estacao(estacao, km):
    nome = str(estacao.get("DC_NOME", "")).strip().title() or "Estação do INMET"
    return f"{nome} ({estacao['CD_ESTACAO']}), a cerca de {round(km)} km de Moeda"


# ---------- montagem ----------

def coletar(token, agora, baixar=baixar_json):
    avisos = []
    previsao = []
    try:
        previsao = ler_previsao(baixar(URL_PREVISAO.format(geocodigo=GEOCODIGO_MOEDA)))
    except Exception as erro:  # noqa: BLE001 - qualquer falha vira aviso
        avisos.append(f"previsão indisponível: {erro}")

    medicao = None
    if not token:
        avisos.append("sem INMET_TOKEN: umidade vem da previsão")
    else:
        try:
            estacao, km = escolher_estacao(baixar(URL_ESTACOES))
            if estacao is None:
                avisos.append(f"nenhuma estação operante a até {RAIO_MAXIMO_KM} km")
            else:
                hoje = agora.astimezone(timezone.utc).date()
                url = URL_MEDICOES.format(
                    inicio=(hoje - timedelta(days=1)).isoformat(), fim=hoje.isoformat(),
                    codigo=estacao["CD_ESTACAO"], token=token,
                )
                ultima = ultima_medicao(baixar(url), agora)
                if ultima is None:
                    avisos.append(f"estação {estacao['CD_ESTACAO']} sem medição recente")
                else:
                    medicao = (nome_estacao(estacao, km), ultima)
        except Exception as erro:  # noqa: BLE001
            # Nunca registrar a URL: ela contém o token.
            avisos.append(f"estação indisponível: {type(erro).__name__}")

    if medicao:
        nome, (quando, umidade) = medicao
        return {
            "fonte": "INMET",
            "estacao": nome,
            "atualizado_em": quando.astimezone(BRASILIA).isoformat(timespec="minutes"),
            "umidade": {"valor": umidade, "tipo": "observada"},
            "previsao": previsao,
        }, avisos

    hoje = agora.astimezone(BRASILIA).date().isoformat()
    de_hoje = next((d for d in previsao if d["data"] == hoje), None)
    if de_hoje and de_hoje["umidade_min"] is not None:
        return {
            "fonte": "INMET",
            "estacao": "Previsão do INMET para Moeda (sem medição de estação)",
            "atualizado_em": agora.astimezone(BRASILIA).isoformat(timespec="minutes"),
            "umidade": {"valor": de_hoje["umidade_min"], "tipo": "minima_prevista"},
            "previsao": previsao,
        }, avisos

    return None, avisos


def ler_anterior(caminho):
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except ValueError:
        return None
    return dados if isinstance(dados, dict) and dados.get("atualizado_em") else None


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--saida", default="dados/tempo.json")
    parser.add_argument("--anterior", help="arquivo publicado antes, usado se tudo falhar")
    args = parser.parse_args()

    agora = datetime.now(timezone.utc)
    dados, avisos = coletar(os.environ.get("INMET_TOKEN", "").strip(), agora)
    for aviso in avisos:
        print(f"::warning::{aviso}")

    if dados is None:
        dados = ler_anterior(args.anterior)
        if dados is None:
            print("::warning::sem dados; o painel mostrará 'indisponível'")
            return 0
        print("::warning::INMET indisponível; mantendo o arquivo publicado antes")

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{args.saida}: {dados.get('estacao')}, {dados['atualizado_em']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
