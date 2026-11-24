"""Validação mecânica pura, compartilhada com a auditoria de síntese."""
def validar_publicado(bp: dict) -> dict:
    """Os validadores mecânicos de HOJE (`synthesize`), sobre o bucket
    publicado. `aspas_bruto`/`clamp_bruto` dizem se a RESPOSTA CRUA violava
    (a flag que o código gravou ao corrigir); os demais olham o publicado."""
    from espectro24 import synthesize as S
    from espectro24.config import MAX_TEMAS
    from espectro24.models import Tema
    temas = bp.get("temas") or []
    objs = [Tema(**{k: t[k] for k in ("tema", "mencoes_aproximadas", "n_reviews_analisadas",
                                     "exemplo_parafraseado")}) for t in temas]
    obs = bp.get("observacao_geral") or ""
    n = bp.get("n_validas")
    m = [t["mencoes_aproximadas"] for t in temas]
    v = {
        "idioma_pt_br": S._idioma_e_pt_br(S._texto_para_checagem_idioma(objs, obs)),
        "escopo_sem_marcador": not S._tem_marcador_de_escopo(obs),
        "sem_aspas_no_publicado": not any(c in t["exemplo_parafraseado"]
                                          for t in temas for c in S._ASPAS_CHARS),
        "mencoes_em_0_n": all(0 <= x <= n for x in m),
        "max_temas": len(temas) <= MAX_TEMAS,
        "ordem_decrescente": m == sorted(m, reverse=True),
        "n_reviews_analisadas_igual_n": all(t["n_reviews_analisadas"] == n for t in temas),
        "campos_nao_vazios": all(t["tema"].strip() and t["exemplo_parafraseado"].strip()
                                 for t in temas) and bool(obs.strip()),
        # regra 3 do PROMPT (não é validador de código): sem tema de menção
        # única, salvo bucket com menos de 5 reviews
        "regra3_sem_mencao_unica": n < 5 or all(x >= 2 for x in m),
        "flags_publicadas_ok": not bp.get("idioma_invalido") and not bp.get("escopo_suspeito"),
    }
    bruto = {"aspas_bruto": not any(t.get("aspas_removidas") for t in temas),
             "clamp_bruto": not any(t.get("mencoes_clampadas") for t in temas)}
    return {"publicado": v, "resposta_crua": bruto,
            "passa_publicado": all(v.values()),
            "passa_crua_estimada": all(v.values()) and all(bruto.values())}

