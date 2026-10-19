"""Converte o transcript .jsonl do Claude Code em markdown legível (alternativa ao /export, FAQ do desafio).

uso: python exportar.py <sessao.jsonl> <saida.md>
Oculta diretório pessoal e e-mail. Pensamento interno não é exportado (não fica legível no transcript).
"""
import json
import re
import sys
from pathlib import Path

REDACOES = [
    (re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+dih_g", re.I), "~"),
    (re.compile(r"/c/Users/dih_g", re.I), "~"),
    (re.compile(r"[\w.+-]+@gmail\.com"), "<email-oculto>"),
    (re.compile(r"dih_g"), "<usuario>"),
    (re.compile(r"C--Users-dih-g-Desktop-ProjetoClaude", re.I), "<projeto>"),
    (re.compile(r"dih-g"), "<usuario>"),
]


def ocultar(texto: str) -> str:
    for padrao, troca in REDACOES:
        texto = padrao.sub(troca, texto)
    return texto


def cortar(texto: str, limite: int) -> str:
    texto = texto.strip()
    return texto if len(texto) <= limite else texto[:limite] + f"\n… [+{len(texto) - limite} caracteres omitidos]"


def resumo_ferramenta(bloco: dict) -> str:
    nome, entrada = bloco.get("name", "?"), bloco.get("input", {})
    if nome in ("Write",):
        corpo = entrada.get("content", "")
        return f"**{nome}** `{entrada.get('file_path', '')}` ({len(corpo.splitlines())} linhas)\n\n```\n{cortar(corpo, 1500)}\n```"
    if nome in ("Edit",):
        return (f"**Edit** `{entrada.get('file_path', '')}`\n\n```diff\n- {cortar(entrada.get('old_string', ''), 600)}\n"
                f"+ {cortar(entrada.get('new_string', ''), 600)}\n```")
    if nome in ("Bash", "PowerShell"):
        return f"**{nome}** — {entrada.get('description', '')}\n\n```bash\n{cortar(entrada.get('command', ''), 1500)}\n```"
    if nome.startswith("mcp__ccd_turn__"):
        return ""
    return f"**{nome}** `{cortar(json.dumps(entrada, ensure_ascii=False), 400)}`"


def texto_resultado(bloco: dict) -> str:
    conteudo = bloco.get("content", "")
    if isinstance(conteudo, list):
        conteudo = "\n".join(c.get("text", "") for c in conteudo if isinstance(c, dict))
    return cortar(str(conteudo), 1200)


def main(origem: str, destino: str) -> None:
    partes = ["# Sessão 01 — desafio SDD completo (spec → implementação → envelope → relatório)\n",
              "> Exportado do transcript `.jsonl` do Claude Code (o `/export` não está disponível no app desktop;",
              "> alternativa prevista no FAQ). Diretório pessoal e e-mail ocultados. Saídas longas truncadas.",
              "> O raciocínio interno do modelo não aparece no transcript e por isso não está aqui.\n"]
    turno = 0
    for linha in Path(origem).read_text(encoding="utf-8").splitlines():
        o = json.loads(linha)
        if o.get("type") not in ("user", "assistant") or o.get("isSidechain"):
            continue
        conteudo = o["message"]["content"]
        hora = o.get("timestamp", "")[11:16]
        if o["type"] == "user":
            if isinstance(conteudo, str):
                if "<system-reminder>" in conteudo and not conteudo.strip().startswith("<system-reminder>") is False:
                    pass
                texto = re.sub(r"<system-reminder>.*?</system-reminder>", "", conteudo, flags=re.S).strip()
                if texto:
                    turno += 1
                    partes.append(f'\n---\n\n<a id="turno-{turno:02d}"></a>\n## 👤 Usuário — turno {turno:02d} ({hora} UTC)\n\n{texto}\n')
                continue
            for b in conteudo:
                if b.get("type") == "text":
                    texto = re.sub(r"<system-reminder>.*?</system-reminder>", "", b["text"], flags=re.S).strip()
                    if texto and not texto.startswith("<"):
                        turno += 1
                        partes.append(f'\n---\n\n<a id="turno-{turno:02d}"></a>\n## 👤 Usuário — turno {turno:02d} ({hora} UTC)\n\n{texto}\n')
                elif b.get("type") == "tool_result":
                    r = texto_resultado(b)
                    if r and not r.startswith("Plan "):
                        partes.append(f"<details><summary>resultado</summary>\n\n```\n{r}\n```\n</details>\n")
        else:
            for b in conteudo:
                if b.get("type") == "text" and b["text"].strip():
                    partes.append(f"\n**🤖 Claude ({hora} UTC):**\n\n{b['text'].strip()}\n")
                elif b.get("type") == "tool_use":
                    r = resumo_ferramenta(b)
                    if r:
                        partes.append(f"\n🔧 {r}\n")
    Path(destino).write_bytes(ocultar("\n".join(partes)).encode("utf-8"))


if __name__ == "__main__":
    main(*sys.argv[1:])
