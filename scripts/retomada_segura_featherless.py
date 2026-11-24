"""Retomada de 08/11: sonda já bloqueada, somente Kimi; nenhuma coleta.

O marcador durável da sonda é obrigatório. Reexecuções retomam os arquivos
validados e não repetem a sonda nem chamam o Letterboxd.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import lista3_featherless as L

D = L.D
OUT = D.OUT / 'retomada_segura'


def agora():
    return datetime.now(timezone.utc).isoformat()


def conferir_sonda():
    sonda = D.ler(OUT / 'sonda.json')
    assert sonda['requisicoes'] == 1 and sonda['passou'] is False
    assert sonda['espera_s'] >= 5400
    assert sonda['sinais'], 'sem evidência da parada conservadora'
    return sonda


def salvar_estado(**campos):
    path = OUT / 'estado.json'
    estado = D.ler(path) if path.exists() else {}
    estado.update(campos, atualizado_utc=agora(), coleta_permitida=False)
    D.salvar(path, estado)
    return estado


def worker(slug):
    """Processo separado permite parada de toda chamada paga no prazo."""
    if D.fim():
        raise FimDoPrazo()
    L.gerar_kimi(slug)


class FimDoPrazo(RuntimeError):
    pass


def executar(slug):
    if D.fim():
        return 'prazo'
    p = D.pasta(slug)
    with (p / 'retomada_kimi.log').open('a') as log:
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), 'worker', '--slug', slug],
            cwd=D.ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    salvar_estado(worker_pid=proc.pid, filme=slug)
    try:
        while proc.poll() is None:
            if time.time() >= D.PRAZO - 5:
                D.encerrar(proc)
                return 'prazo'
            time.sleep(.2)
        return proc.returncode
    finally:
        D.encerrar(proc)
        salvar_estado(worker_pid=None)


def revalidar_existentes():
    rows = []
    for slug in L.fila_ordenada():
        p = D.pasta(slug)
        es = D.ler(p / 'estado.json')
        dest = p / 'condicoes/Kimi-K3.1-Pro/condicoes.json'
        if es['estado'] != 'gerado' or not dest.exists():
            continue
        v = D.validar_condicoes(D.ler(p / 'bullets.json'), D.ler(dest))
        es.setdefault('validadores_condicoes', {})[L.KIMI] = v
        es['sem_kimi'] = False
        D.salvar(p / 'estado.json', es)
        rows.append(dict(slug=slug, c22=es['c22'], validadores=v))
    D.salvar(OUT / 'kimi_existentes_validados.json', rows)
    return rows


def relatorio(motivo, final=False):
    saldo = D.conta('credits/balance')
    D.salvar(OUT / 'saldo_atual.json', saldo)
    # O relatório legado usa este checkpoint para conciliar o débito.
    D.salvar(L.OUT / 'saldo_ao_parar_llm.json', saldo)
    rep = L.relatorio(final=final)
    estado = D.ler(OUT / 'estado.json')
    rep.update(retomada_segura=estado, sonda=conferir_sonda(),
               motivo_encerramento=motivo, coleta_apos_prazo=False,
               bloqueios_novos=[conferir_sonda()], commits=[],
               horario_retomada_coleta=None)
    rep['kimi_faltantes'] = [r['slug'] for r in rep['filmes']
                              if r['estado'] == 'gerado' and r['sem_kimi']]
    rep['retomada_coleta_nao_tentados'] = [r['slug'] for r in rep['filmes']
                                         if r['origem'] != 'frente1' and
                                         r['estado'] in ('nao_coletado', 'coleta_bloqueada')]
    D.salvar(OUT / 'relatorio.json', rep)
    D.salvar(L.OUT / 'relatorio_sessao.json', rep)
    md = (D.OUT / 'RELATORIO_SESSAO.md').read_text()
    md = md.replace('Coleta HTTP pode continuar.', 'Coleta encerrada por hoje, inclusive após 21h.')
    md += ('\n## Retomada segura após esfriamento\n\n'
           'Bloqueio antigo: marcador de encerramento 08/11 às 06:57:28,521983 Recife; '
           'AntiBotError. Status/assinatura exata e instante da resposta não preservados no log antigo.\n\n'
           'Sonda única: 08/11 às 09:24:39 Recife; HTTP 200 com sinal captcha. '
           'Nenhuma retomada de coleta; nenhuma outra requisição ao Letterboxd.\n\n'
           'Passada Kimi autorizada explicitamente após a parada da coleta. '
           'Juiz fora; nenhuma publicação; nenhum commit de dados ou de código.\n\n'
           f"Motivo de encerramento: {motivo}. Estado: {estado['estado']}.\n\n"
           f"Kimi ainda pendente em filmes gerados: {len(rep['kimi_faltantes'])}.\n")
    D.escrever_atomico(D.OUT / 'RELATORIO_SESSAO.md', md)
    D.escrever_atomico(OUT / 'RELATORIO.md', md)
    return rep


def rodar():
    OUT.mkdir(parents=True, exist_ok=True)
    with D.trava(OUT / 'driver.lock'), D.trava(D.OUT / 'letterboxd_global.lock'), D.trava(L.OUT / 'encadeador.lock'), D.trava(D.OUT / 'driver.lock'):
        conferir_sonda()
        D.conferir()
        politica = D.politica_sessao()
        politica.update(coleta_apos_prazo=False, coleta_suspensa_hoje=True,
                        delay_requisicoes_s=6, teto_total_usd=19)
        D.salvar(D.OUT / 'sessao_politica.json', politica)
        caixa = L.F.sessao_ambiente()
        assert caixa.resumo()['teto_usd'] == 19 and caixa.prazo_utc == D.PRAZO
        diagnostico = L.diagnosticar_verificadores()
        salvar_estado(estado='kimi', pid=os.getpid(), inicio_utc=agora(),
                      prazo_utc=D.PRAZO, sonda_passou=False, coleta_encerrada_por='sinal_captcha',
                      diagnostico_verificadores=diagnostico)
        revalidar_existentes()
        tentados = set(D.ler(OUT / 'tentados.json')) if (OUT / 'tentados.json').exists() else set()
        motivo = 'fila_kimi_concluida'
        try:
            for slug in L.projetar_kimi():
                if D.fim():
                    motivo = 'prazo'; break
                if slug in tentados:
                    continue
                salvar_estado(filme=slug)
                rc = executar(slug)
                if rc == 'prazo':
                    motivo = 'prazo'; break
                tentados.add(slug)
                D.salvar(OUT / 'tentados.json', sorted(tentados))
                L.log('Retomada Kimi', slug, 'concluido' if rc == 0 else 'falha', 'rc', rc)
                if rc != 0:
                    # Não repetir automaticamente uma falha paga ou avançar sob teto incerto.
                    motivo = 'worker_kimi_falhou'; break
            salvar_estado(estado='encerrado', motivo=motivo, fim_utc=agora(), filme=None)
        except BaseException as e:
            motivo = 'interrompido_' + type(e).__name__
            salvar_estado(estado='interrompido', motivo=motivo)
            raise
        finally:
            rep = relatorio(motivo, final=True)
            D.salvar(OUT / 'encerrado.json', dict(motivo=motivo, utc=agora(), caixa=rep['caixa']))
            L.log('Retomada encerrada', motivo, 'gerados', rep['gerados'], 'caixa', rep['caixa'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('modo', choices=['rodar', 'worker', 'relatorio'])
    ap.add_argument('--slug')
    args = ap.parse_args()
    D.config()
    if args.modo == 'rodar':
        rodar()
    elif args.modo == 'worker':
        conferir_sonda()
        worker(args.slug)
    else:
        relatorio('relatorio_manual', final=(OUT / 'encerrado.json').exists())


if __name__ == '__main__':
    main()
