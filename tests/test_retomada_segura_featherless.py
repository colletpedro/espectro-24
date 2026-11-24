from pathlib import Path
import sys
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import retomada_segura_featherless as R


def test_sonda_obrigatoria_unica_e_com_esfriamento(tmp_path, monkeypatch):
    monkeypatch.setattr(R, 'OUT', tmp_path)
    with pytest.raises(FileNotFoundError):
        R.conferir_sonda()
    for s in [dict(requisicoes=2, passou=False, espera_s=6000, sinais=['captcha']),
              dict(requisicoes=1, passou=False, espera_s=5399, sinais=['captcha']),
              dict(requisicoes=1, passou=True, espera_s=6000, sinais=[])]:
        R.D.salvar(tmp_path / 'sonda.json', s)
        with pytest.raises(AssertionError):
            R.conferir_sonda()
    s = dict(requisicoes=1, passou=False, espera_s=6000, sinais=['captcha'])
    R.D.salvar(tmp_path / 'sonda.json', s)
    assert R.conferir_sonda() == s


def test_prazo_nao_inicia_worker_pago(monkeypatch):
    monkeypatch.setattr(R.D, 'fim', lambda: True)
    monkeypatch.setattr(R.subprocess, 'Popen', lambda *a, **kw: pytest.fail('fora do prazo'))
    assert R.executar('filme') == 'prazo'
    monkeypatch.setattr(R.L, 'gerar_kimi', lambda *a: pytest.fail('fora do prazo'))
    with pytest.raises(R.FimDoPrazo):
        R.worker('filme')


def test_revalidacao_existente_nao_chama_modelo_nem_exibe_conteudo(tmp_path, monkeypatch):
    monkeypatch.setattr(R, 'OUT', tmp_path / 'retomada')
    monkeypatch.setattr(R.L, 'fila_ordenada', lambda: ['protegido'])
    monkeypatch.setattr(R.D, 'pasta', lambda s: tmp_path / s)
    p = tmp_path / 'protegido'
    R.D.salvar(p / 'estado.json', dict(estado='gerado', c22=True, sem_kimi=True))
    R.D.salvar(p / 'bullets.json', dict(conteudo='lacrado'))
    R.D.salvar(p / 'condicoes/Kimi-K3.1-Pro/condicoes.json', dict(conteudo='lacrado'))
    monkeypatch.setattr(R.L.F, 'resposta', lambda *a, **kw: pytest.fail('arquivo existe'))
    monkeypatch.setattr(R.D, 'validar_condicoes', lambda *a: dict(flags=0, gerou_bloco=True))
    rows = R.revalidar_existentes()
    assert rows == [dict(slug='protegido', c22=True, validadores=dict(flags=0, gerou_bloco=True))]
    assert R.D.ler(p / 'estado.json')['sem_kimi'] is False
    assert 'lacrado' not in (R.OUT / 'kimi_existentes_validados.json').read_text()


def test_worker_terminado_antes_do_limite_incluindo_graca(tmp_path, monkeypatch):
    monkeypatch.setattr(R.D, 'fim', lambda: False)
    monkeypatch.setattr(R.D, 'pasta', lambda s: tmp_path)
    monkeypatch.setattr(R, 'salvar_estado', lambda **kw: None)
    monkeypatch.setattr(R.time, 'time', lambda: R.D.PRAZO - 4)
    proc = NS(pid=123, poll=lambda: None)
    monkeypatch.setattr(R.subprocess, 'Popen', lambda *a, **kw: proc)
    encerrados = []
    monkeypatch.setattr(R.D, 'encerrar', lambda p: encerrados.append(p))
    assert R.executar('filme') == 'prazo'
    assert encerrados and all(p is proc for p in encerrados)


def test_reinicio_apos_sonda_bloqueada_nunca_coleta(tmp_path, monkeypatch):
    monkeypatch.setattr(R, 'OUT', tmp_path / 'retomada')
    monkeypatch.setattr(R.D, 'OUT', tmp_path)
    monkeypatch.setattr(R.L, 'OUT', tmp_path / 'lista3')
    R.D.salvar(R.OUT / 'sonda.json', dict(requisicoes=1, passou=False, espera_s=6000, sinais=['captcha']))
    monkeypatch.setattr(R.D, 'conferir', lambda: None)
    monkeypatch.setattr(R.L, 'diagnosticar_verificadores', lambda: [])
    monkeypatch.setattr(R, 'revalidar_existentes', lambda: [])
    monkeypatch.setattr(R.L, 'projetar_kimi', lambda: [])
    monkeypatch.setattr(R.L.F, 'sessao_ambiente', lambda: NS(resumo=lambda: dict(teto_usd=19), prazo_utc=R.D.PRAZO))
    monkeypatch.setattr(R.D, 'coletar', lambda: pytest.fail('coleta proibida'))
    monkeypatch.setattr(R.L, 'coletar_lista3', lambda: pytest.fail('coleta proibida'))
    monkeypatch.setattr(R, 'executar', lambda *a: pytest.fail('nenhum Kimi pendente'))
    monkeypatch.setattr(R, 'relatorio', lambda *a, **kw: dict(caixa={}, gerados=82))
    R.rodar()
    R.rodar()
    es = R.D.ler(R.OUT / 'estado.json')
    assert es['estado'] == 'encerrado' and es['coleta_permitida'] is False
    assert R.D.politica_sessao()['coleta_apos_prazo'] is False
