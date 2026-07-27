#!/usr/bin/env python3
"""
atualizar_bancos.py — alimenta o gerador de senhas brasileiras com as
notícias de cultura pop do dia.

O que faz:
  1. Busca feeds RSS de cultura/entretenimento do Brasil (grátis, sem API paga).
  2. Extrai nomes próprios e termos marcantes das manchetes.
  3. Slugifica ("Pantera Negra" -> "panteranegra") pra virar referência de senha.
  4. Escreve bancos.json, que o site (index.html) lê no navegador.

Roda sem nenhuma dependência externa — só a biblioteca padrão do Python.
Agende com cron ou GitHub Actions pra rodar 1x/dia (veja o README).

Uso:
    python3 atualizar_bancos.py            # atualiza bancos.json
    python3 atualizar_bancos.py --dry-run  # mostra o que faria, sem gravar
"""

from __future__ import annotations

import gzip
import html
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ----------------------------------------------------------------------------
# Fontes: feeds de cultura pop / entretenimento brasileiros.
# Se um feed cair, o script apenas o ignora e segue com os demais.
# ----------------------------------------------------------------------------
FEEDS = [
    "https://g1.globo.com/rss/g1/pop-arte/",
    "https://g1.globo.com/rss/g1/musica/",
    "https://g1.globo.com/rss/g1/carnaval/",
    "https://g1.globo.com/rss/g1/",
]

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "bancos.json"

# Palavras que não viram boas referências de senha (curtas, vazias, comuns demais).
STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "um", "uma",
    "no", "na", "nos", "nas", "em", "por", "para", "pra", "com", "sem",
    "que", "se", "ao", "aos", "à", "às", "the", "of", "vai", "ser", "foi",
    "após", "apos", "sobre", "mais", "após", "diz", "é", "ele", "ela", "seu",
    "sua", "como", "novo", "nova", "ano", "anos", "dia", "veja", "após",
}

# Verbos conjugados no português informal — a peça "esperta" da senha.
# Auto-gerar conjugação correta a partir de notícia é frágil, então este banco
# é curado à mão. Raramente precisa mudar; a graça é o embaralhamento de padrão.
VERBS_SEED = [
   "fiqueiESPERANDO", "danceiATEOFIM", "choreiDEALEGRIA", "comiTUDINHO",
    "griteiGOOOL", "ameiDEMAIS", "vouVIAJAR", "canteiBEMALTO", "dormiTARDE",
    "ganheiNALOTO", "venciNOFINAL", "sorriTODODIA", "volteiPRACASA",
    "acordeiCEDO", "sofriCALADO", "riDEMAIS", "puleiOMURO", "torciMUITO",
    "FazPARTE", "SeiDENADA", "Foi-seCEDO", "TambémACHO", "OBRIGADOmeupovo",
    "corriMUITO", "estudeiPOUCO", "jogueiFORA", "pagueiCARO", "andeiDEPRESSA",
    "volteiATRAS", "faleiSERIO", "escuteiATENCAO", "olheiPROCEL", "ligueiPRAELA",
    "mandeiUMKI", "recebiUMABRAÇO", "deiUMBEIJO", "tomeiUMBANHO", "vestiAROUPA",
    "calceiOSAPATO", "compreiPÃO", "tomeiCAFÉ", "bebiSUCO", "comiFRUTA",
    "friteiOVO", "asseiBOLO", "cozinheiARROZ", "tempereiSALADA", "laveIALOUÇA",
    "varriACASA", "passeiPANOO", "tireiOPO", "pendureIROUPA", "dobreiAMEIA",
    "arrumeIACAMA", "escoveIOSDENTES", "penteieOCABELO", "fizABARBA", "passeiPERFUME",
    "coloqueIALIANÇA", "pegueIACHAVE", "abriAPORTA", "fecheIAJANELA", "acendiALUZ",
    "apagueIAVELA", "sopreiASVAS", "regueIASPLANTAS", "cuideIDOSBICHOS", "alimenteiOGATO",
    "chameIOCACHORRO", "brinqueICOMELA", "leveIPRAPASSEAR", "ensineITRUQUES", "obedeciOCORACAO",
    "seguiOMEUINSTINTO", "confieiNAMINHAINTUICAO", "tenteINOVAMENTE", "persistiMESMOASSIM", "naoDESISTI",
    "fuiEMFRENTE", "topeiODESAFIO", "aceiteIACONDICAO", "negocieiOMELHOR", "fecheIONEGOCIO",
    "assineIOCONTRATO", "pagueIADIVIDA", "quiteIOTITULO", "renoveIOCARTAO", "canceleiASENHA",
    "troqueIOCELULAR", "baixEIUMAAPLICATIVO", "atualizeIOSISTEMA", "formateIOPC", "instaleIOWINDOWS",
    "configureIAREDE", "testeIAINTERNET", "verifiqueIOEMAIL", "respondiAMENSAGEM", "curtiOPOST",
    "compartilheiOFILME", "salveIAFOTO", "editeIOVIDEO", "graveIOPODCAST", "publiqueIOTEXTO",
    "liOLIVRO", "escreviUMAHISTORIA", "desenheiUMQUADRO", "pin teIOUTRO", "rabisqueIONADA",
    "rasureIOPAPEL", "amassEIABOLA", "chuteIAGOL", "marqueIOTRIUNFO", "comemoreIAMVITORIA",
    "festejeIAMINHA", "celebreIOANIVERSARIO", "ganheiOPRESENTE", "abraeiOCARTÃO", "liOMURAL",
    "viOFILME", "assistiASERIE", "maratoneIATEMPORADA", "reveioEPISODIO", "lembreIADATRAM",
    "esqueciOSENHA", "redescobriOMEUHEROI", "reencontreiOSAMIGOS", "revisiteIALUGAR", "relembreIOMOMENTO",
    "reviviAEMOCAO", "sentiOCALOR", "enfrenteiAFRIO", "suporteiACHUVA", "aproveiteIOSOL",
    "curtIAVIAGEM", "exploreIOCAMINHO", "descobriUMNOVOLUGAR", "conheciUMAMIGO", "abraceIAPESSOA",
    "ajudeIQUEMPRECISAVA", "doeiOSANGUE", "colaboreICOMAPROJETO", "contribuiPARAOBEM", "fizADIFERENCA",
    "mudeIOMEUJEITO", "melhoreIMINHAPOSTURA", "evoluicOMO PESSOA", "cresciPROFISSIONALMENTE", "aprendIALGO",
    "ensineIOQUE SEI", "compartilheiMEUCONHECIMENTO", "multipliqueIASBENÇÃOS", "dividiAALEGRIA", "someiASFELICIDADES",
    "subtraiASTRISTEZAS", "calculeIOPERCURSO", "mediASDISTANCIAS", "peseIASDECISOES", "avalieIORISCO",
    "analiseIOPROBLEMA", "solucioneIAQUESTAO", "resolviOCONFLITO", "mediEICONFLITOS", "apazigueIOCORACAO",
    "acalmeIAALMA", "sossegueIOESPIRITO", "tranquilizeIAMINHA", "serenEIOAMBIENTE", "organizeIACASA",
    "arrumeIAGAVETA", "limpeiOGABINETE", "laveIOBANHEIRO", "enxagueIACOZINHA", "varriASALAS",
    "lustreiOMOVEL", "envernizeIAPORTA", "pinteIAPAREDE", "rebocOUOTELHADO", "consertEIOTUO",
    "arrumeIACAMA", "troqueILENCOIS", "laveIATOALHAS", "estendiACORDA", "pendureINOBANHEIRO",
    "guardeiOGUARDA-ROUPA", "organizeIASPRATELEIRAS", "separeILIXO", "recicleIMATERIAL", "reutilizeIEMBALAGENS",
    "economizeIAGUA", "poupeiENERGIA", "preserveIANATUREZA", "planteIARVORE", "regueIOJARDIM",
    "cuideIASHORTAS", "colhiASFLORES", "cheireIOPERFUME", "sentiOCHEIRO", "proveIOALIMENTO",
    "experimentEIATEMPERO", "saboreEIACOMIDA", "degustEIOWINHO", "brindeIAVIDA", "saudeIASAMIGOS",
    "agradeciAPELAPESSOA", "perdoeiOSOFENSORES", "pediDESCULPAS", "desculpeiIMEUS", "aceiteIASDIFERENCAS",
    "respeiteIOPROXIMO", "admireIAFORCA", "reconheciOMEULIMITE", "supereiASDIFICULDADES", "venciOMEUMEDO"
]

SPECIALS_SEED = ["!", "~", "@", "#", "$", "%", "&", "*"]

# Semente de segurança: se a rede falhar por completo, o gerador nunca fica vazio.
REFS_SEED = [
    "asemanainteira", "queridodiario", "noveladasnove", "festajunina",
    "paodequeijo", "brigadeirodecolher", "sextouarrasou", "jabuticaba",
]


# ----------------------------------------------------------------------------
def fetch(url: str, timeout: int = 20) -> str:
    """Baixa uma URL, lidando com gzip (feeds da Globo comprimem sempre)."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SenhaBrasileiraBot/1.0)",
            "Accept-Encoding": "gzip, identity",
        },
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    raw = resp.read()
    if raw[:2] == b"\x1f\x8b" or resp.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "ignore")


def extrair_titulos(xml: str) -> list[str]:
    """Extrai os <title> de cada <item>/<entry> do RSS, tratando CDATA."""
    titulos = []
    blocos = re.findall(r"<(?:item|entry)>(.*?)</(?:item|entry)>", xml, re.S)
    for bloco in blocos:
        m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", bloco, re.S)
        if m:
            titulos.append(html.unescape(m.group(1)).strip())
    return titulos


def sem_acento(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def slug(palavras: list[str]) -> str:
    """['Pantera', 'Negra'] -> 'panteranegra' (só letras a-z)."""
    junto = sem_acento(" ".join(palavras)).lower()
    return re.sub(r"[^a-z]", "", junto)


def extrair_referencias(titulos: list[str]) -> list[str]:
    """
    Transforma manchetes em referências de senha.
    Estratégia: capturar sequências de nomes próprios (Title Case) — que é onde
    moram os memes, artistas, filmes e novelas do dia — e virar slug.
    """
    achados: dict[str, None] = {}  # dict preserva ordem e deduplica
    for titulo in titulos:
        # Sequências de palavras que começam com maiúscula: "Pantera Negra",
        # "Ryan Gosling", "Banda Eva", "Casa Branca"...
        for seq in re.findall(r"\b([A-ZÀ-Ý][\wÀ-ú]+(?:\s+[A-ZÀ-Ý][\wÀ-ú]+)*)", titulo):
            tokens = [
                t for t in seq.split()
                if sem_acento(t).lower() not in STOPWORDS and len(t) >= 3
            ]
            if not tokens:
                continue
            s = slug(tokens)
            if 6 <= len(s) <= 24:
                achados.setdefault(s, None)
    return list(achados.keys())


def extrair_numeros(titulos: list[str]) -> list[str]:
    """Anos e números marcantes que apareceram nas notícias do dia."""
    nums: dict[str, None] = {}
    ano_atual = datetime.now().year
    for titulo in titulos:
        for n in re.findall(r"\b(\d{2,4})\b", titulo):
            # anos plausíveis ou números curtos com cara de "marcante"
            if (len(n) == 4 and 1900 <= int(n) <= ano_atual + 5) or len(n) <= 3:
                nums.setdefault(n, None)
    # sempre inclui o ano atual e o próximo (a "regra de ouro" de trocar o número)
    nums.setdefault(str(ano_atual), None)
    nums.setdefault(str(ano_atual + 1), None)
    return list(nums.keys())


def coletar() -> tuple[list[str], list[str], list[str]]:
    """Roda todos os feeds e agrega. Tolerante a falhas de rede por feed."""
    titulos: list[str] = []
    for url in FEEDS:
        try:
            xml = fetch(url)
            novos = extrair_titulos(xml)
            titulos.extend(novos)
            print(f"  ✓ {len(novos):3d} manchetes de {url}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — queremos degradar, não quebrar
            print(f"  ✗ falhou {url}: {e}", file=sys.stderr)

    refs = extrair_referencias(titulos)
    nums = extrair_numeros(titulos)
    return refs, nums, titulos


def main() -> int:
    dry = "--dry-run" in sys.argv
    print("Buscando notícias de cultura pop do Brasil...", file=sys.stderr)
    refs, nums, titulos = coletar()

    # Rede vazia? Não deixamos o gerador sem munição.
    if len(refs) < 12:
        print(f"  ! só {len(refs)} referências — completando com a semente.",
              file=sys.stderr)
        for s in REFS_SEED:
            if s not in refs:
                refs.append(s)
    if not nums:
        nums = ["2027", "1994", "2002", "171", "300"]

    # Limita o tamanho dos bancos pra manter o JSON enxuto.
    refs = refs[:60]
    nums = nums[:16]

    banco = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": "RSS cultura pop BR (Globo/G1)",
        "manchetes_lidas": len(titulos),
        "refs": refs,
        "verbs": VERBS_SEED,
        "nums": nums,
        "specials": SPECIALS_SEED,
    }

    print(f"\nReferências do dia ({len(refs)}):", file=sys.stderr)
    print("  " + ", ".join(refs[:12]) + " ...", file=sys.stderr)

    if dry:
        print("\n[--dry-run] não gravei nada.", file=sys.stderr)
        print(json.dumps(banco, ensure_ascii=False, indent=2))
        return 0

    SAIDA.write_text(json.dumps(banco, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n✓ Escrito {SAIDA}  ({len(refs)} refs, {len(nums)} números)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
