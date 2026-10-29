"""Testes do coletor do INMET com respostas simuladas (sem rede).

Rodar: python3 -m unittest discover -s tests
"""
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import coletar_tempo as ct  # noqa: E402

AGORA = datetime(2026, 10, 29, 17, 20, tzinfo=timezone.utc)  # 14h20 em Brasília

PREVISAO = {
    "3142304": {
        "29/10/2026": {
            "manha": {"resumo": "Poucas nuvens", "temp_max": 30, "temp_min": 16, "umidade_min": 40},
            "tarde": {"resumo": "Sol com poucas nuvens", "temp_max": 31, "temp_min": 16, "umidade_min": 22},
            "noite": {"resumo": "Céu claro", "temp_max": 31, "temp_min": 17, "umidade_min": 35},
        },
        "30/10/2026": {"resumo": "Pancadas de chuva", "temp_max": "28", "temp_min": "18", "umidade_min": "45"},
    }
}

ESTACOES = [
    {"CD_ESTACAO": "A555", "DC_NOME": "IBIRITE (ROLA MOCA)", "VL_LATITUDE": "-20.031",
     "VL_LONGITUDE": "-44.011", "CD_SITUACAO": "Operante"},
    {"CD_ESTACAO": "A999", "DC_NOME": "PERTO MAS EM PANE", "VL_LATITUDE": "-20.33",
     "VL_LONGITUDE": "-44.05", "CD_SITUACAO": "Pane"},
    {"CD_ESTACAO": "A001", "DC_NOME": "BRASILIA", "VL_LATITUDE": "-15.79",
     "VL_LONGITUDE": "-47.93", "CD_SITUACAO": "Operante"},
]

MEDICOES = [
    {"DT_MEDICAO": "2026-10-29", "HR_MEDICAO": "1500", "UMD_INS": "28"},
    {"DT_MEDICAO": "2026-10-29", "HR_MEDICAO": "1600", "UMD_INS": "24"},
    {"DT_MEDICAO": "2026-10-29", "HR_MEDICAO": "1700", "UMD_INS": None},
]


def falso(respostas):
    def baixar(url):
        for trecho, resposta in respostas.items():
            if trecho in url:
                if isinstance(resposta, Exception):
                    raise resposta
                return resposta
        raise OSError("sem rede")
    return baixar


class TestColetor(unittest.TestCase):
    def test_previsao_junta_turnos_e_dias_inteiros(self):
        dias = ct.ler_previsao(PREVISAO)
        self.assertEqual([d["data"] for d in dias], ["2026-10-29", "2026-10-30"])
        self.assertEqual(dias[0], {"data": "2026-10-29", "condicao": "Sol com poucas nuvens",
                                   "temp_min": 16, "temp_max": 31, "umidade_min": 22})
        self.assertEqual(dias[1]["temp_max"], 28.0)

    def test_escolhe_estacao_operante_mais_proxima(self):
        estacao, km = ct.escolher_estacao(ESTACOES)
        self.assertEqual(estacao["CD_ESTACAO"], "A555")
        self.assertLess(km, 40)

    def test_com_token_usa_medicao_da_estacao(self):
        dados, _ = ct.coletar("abc", AGORA, falso({
            "previsao": PREVISAO, "estacoes/T": ESTACOES, "/A555/abc": MEDICOES,
        }))
        self.assertEqual(dados["umidade"], {"valor": 24.0, "tipo": "observada"})
        self.assertEqual(dados["atualizado_em"], "2026-10-29T13:00-03:00")
        self.assertTrue(dados["estacao"].startswith("Ibirite (Rola Moca) (A555)"))
        self.assertEqual(len(dados["previsao"]), 2)

    def test_sem_token_usa_menor_umidade_prevista(self):
        dados, avisos = ct.coletar("", AGORA, falso({"previsao": PREVISAO}))
        self.assertEqual(dados["umidade"], {"valor": 22, "tipo": "minima_prevista"})
        self.assertEqual(dados["atualizado_em"], "2026-10-29T14:20-03:00")
        self.assertTrue(any("INMET_TOKEN" in a for a in avisos))

    def test_medicao_velha_cai_para_previsao(self):
        velhas = [{"DT_MEDICAO": "2026-10-29", "HR_MEDICAO": "1000", "UMD_INS": "50"}]
        dados, _ = ct.coletar("abc", AGORA, falso({
            "previsao": PREVISAO, "estacoes/T": ESTACOES, "/A555/abc": velhas,
        }))
        self.assertEqual(dados["umidade"]["tipo"], "minima_prevista")

    def test_erro_na_estacao_nao_vaza_o_token(self):
        _, avisos = ct.coletar("segredo123", AGORA, falso({
            "previsao": PREVISAO, "estacoes/T": ESTACOES,
            "/A555/": OSError("falha em .../A555/segredo123"),
        }))
        self.assertFalse(any("segredo123" in a for a in avisos))

    def test_tudo_fora_do_ar_nao_gera_dados(self):
        dados, avisos = ct.coletar("abc", AGORA, falso({}))
        self.assertIsNone(dados)
        self.assertTrue(avisos)


if __name__ == "__main__":
    unittest.main()
