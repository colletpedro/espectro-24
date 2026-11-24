"""Orçamento único da sessão autorizada: Etapa 1 + Etapa 2 + Lista 3.

A migração preserva a configuração legada de US$15 para que o supervisor
já carregado continue vivo. O teto canônico de US$19 é adicional, no MESMO
SQLite, e também é imposto por trigger a clientes anteriores à migração.
"""
from __future__ import annotations
import json
from pathlib import Path
import sqlite3

TETO_NANO=19_000_000_000
PRAZO_UTC=1794182400.0


def politica(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='session_budget'").fetchone(): return None
    return db.execute('SELECT teto,prazo,bloqueado FROM session_budget WHERE id=1').fetchone()


def ativar(caixa, etapa1):
    with sqlite3.connect(etapa1,timeout=30) as origem:
        registros=origem.execute('SELECT id,reservado,custo,unidades,estado,registro FROM chamadas').fetchall()
    assert registros and all(r[2] is not None and r[4]=='concluida' for r in registros), 'Etapa 1 ainda tem cobrança pendente'
    with sqlite3.connect(caixa,timeout=30) as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS session_budget (id INTEGER PRIMARY KEY CHECK(id=1),teto INTEGER NOT NULL CHECK(teto=19000000000),prazo REAL NOT NULL CHECK(prazo<=1794182400),bloqueado INTEGER NOT NULL DEFAULT 0)')
        db.execute('INSERT OR IGNORE INTO session_budget(id,teto,prazo) VALUES(1,?,?)',(TETO_NANO,PRAZO_UTC))
        assert politica(db)[:2]==(TETO_NANO,PRAZO_UTC)
        for rid,res,custo,unidades,estado,registro in registros:
            if db.execute('SELECT 1 FROM chamadas WHERE id=?',('etapa1:'+rid,)).fetchone(): continue
            reg=json.loads(registro);reg['etapa_origem']='etapa1';reg['reserva_id']='etapa1:'+rid
            db.execute('INSERT OR IGNORE INTO chamadas VALUES(?,?,?,?,?,?)',('etapa1:'+rid,res,custo,unidades,estado,json.dumps(reg,ensure_ascii=False)))
        presentes=db.execute("SELECT count(*),sum(custo) FROM chamadas WHERE id LIKE 'etapa1:%'").fetchone()
        assert presentes==(len(registros),sum(r[2] for r in registros)), 'Importação Etapa 1 diverge'
        assert db.execute('SELECT sum(coalesce(custo,reservado)) FROM chamadas').fetchone()[0]<=TETO_NANO
        db.execute('''CREATE TRIGGER IF NOT EXISTS teto_sessao_reserva BEFORE INSERT ON chamadas
        WHEN (SELECT bloqueado FROM session_budget WHERE id=1)=1 OR
        (SELECT coalesce(sum(coalesce(custo,reservado)),0) FROM chamadas)+coalesce(NEW.custo,NEW.reservado)>(SELECT teto FROM session_budget WHERE id=1)
        BEGIN SELECT RAISE(ABORT,'teto global da sessão excedido ou bloqueado'); END''')
        db.execute('''CREATE TRIGGER IF NOT EXISTS cobranca_fora_contrato AFTER UPDATE OF custo ON chamadas
        WHEN NEW.custo>NEW.reservado
        BEGIN UPDATE session_budget SET bloqueado=1 WHERE id=1; END''')
    return dict(chamadas_etapa1=len(registros),custo_etapa1_usd=sum(r[2] for r in registros)/1e9,teto_total_usd=19,prazo_utc=PRAZO_UTC)
