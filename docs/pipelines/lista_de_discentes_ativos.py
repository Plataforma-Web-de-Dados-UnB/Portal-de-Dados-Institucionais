"""Pipeline de discentes ativos para execução pelo Data-Processor-Worker.

O worker injeta no contexto: df, batch_id, connection, tabela_silver e
tabela_gold. Por isso, este arquivo deve ser cadastrado como o conteúdo do
campo "Script Python" e não executado diretamente pela linha de comando.
"""

import re
import unicodedata

from sqlalchemy import text


COLUNAS_ESPERADAS = ["Curso", "Ano", "Matricula", "Discente"]


def texto_limpo(valor):
    """Converte nulos em vazio, aplica Unicode NFC e reduz espaços internos."""
    if pd.isna(valor):
        return ""
    valor = unicodedata.normalize("NFC", str(valor))
    return re.sub(r"\s+", " ", valor).strip()


def nome_padronizado(valor):
    """Aplica título sem capitalizar preposições comuns em português."""
    partes = texto_limpo(valor).lower().split()
    minusculas = {"da", "das", "de", "do", "dos", "e"}
    return " ".join(
        parte if indice > 0 and parte in minusculas else parte.capitalize()
        for indice, parte in enumerate(partes)
    )


def curso_padronizado(valor):
    """Uniformiza caixa, espaços e separadores do campo composto de curso."""
    valor = texto_limpo(valor).upper()
    valor = re.sub(r"\s*/\s*", "/", valor)
    partes = [texto_limpo(parte) for parte in re.split(r"\s*-\s*", valor)]
    return " - ".join(parte for parte in partes if parte)


def separar_curso(valor):
    """Separa 'CURSO/UNIDADE - GRAU - TURNO' em atributos analíticos."""
    partes = [parte.strip() for parte in valor.split(" - ")]
    curso_unidade = partes[0] if partes else ""
    if "/" in curso_unidade:
        curso, unidade = curso_unidade.rsplit("/", 1)
    else:
        curso, unidade = curso_unidade, ""
    grau = partes[1] if len(partes) > 1 else ""
    turno = partes[2] if len(partes) > 2 else ""
    return pd.Series([curso.strip(), unidade.strip(), grau, turno])


def validar_linha(linha):
    erros = []
    ano_atual = pd.Timestamp.now(tz="UTC").year

    if not linha["curso"]:
        erros.append("curso ausente")
    elif not linha["unidade"]:
        erros.append("unidade ausente")
    if pd.isna(linha["ano"]):
        erros.append("ano inválido")
    elif not 1962 <= int(linha["ano"]) <= ano_atual:
        erros.append("ano fora do intervalo")
    if not re.fullmatch(r"\d{9}", linha["matricula"]):
        erros.append("matrícula deve conter 9 dígitos")
    if not linha["discente"]:
        erros.append("discente ausente")
    if linha["duplicado_no_arquivo"]:
        erros.append("matrícula duplicada no arquivo")

    return "; ".join(erros)


# Falha cedo e com mensagem clara se o arquivo não respeitar o contrato.
colunas_ausentes = [coluna for coluna in COLUNAS_ESPERADAS if coluna not in df.columns]
if colunas_ausentes:
    raise ValueError(
        "Colunas obrigatórias ausentes: "
        + ", ".join(colunas_ausentes)
        + ". Esperado: "
        + ";".join(COLUNAS_ESPERADAS)
    )

silver = df[COLUNAS_ESPERADAS].copy()
silver.columns = ["curso_raw", "ano_raw", "matricula_raw", "discente_raw"]

# Limpeza e tipagem.
silver["curso_completo"] = silver["curso_raw"].map(curso_padronizado)
silver[["curso", "unidade", "grau", "turno"]] = silver[
    "curso_completo"
].apply(separar_curso)
silver["ano"] = pd.to_numeric(
    silver["ano_raw"].map(texto_limpo).str.replace(r"\.0$", "", regex=True),
    errors="coerce",
).astype("Int64")
silver["matricula"] = silver["matricula_raw"].map(texto_limpo).str.replace(
    r"\D", "", regex=True
)
silver["discente"] = silver["discente_raw"].map(nome_padronizado)
silver["duplicado_no_arquivo"] = silver.duplicated(
    subset=["matricula"], keep="first"
) & silver["matricula"].ne("")

# Qualidade: todas as linhas seguem auditáveis na silver; somente as válidas
# alimentam a gold.
silver["erros_validacao"] = silver.apply(validar_linha, axis=1)
silver["status_validacao"] = silver["erros_validacao"].map(
    lambda erros: "REJEITADO" if erros else "VALIDO"
)
silver["batch_id"] = str(batch_id)
silver["processado_em"] = pd.Timestamp.now(tz="UTC")

colunas_silver = [
    "batch_id",
    "curso_raw",
    "ano_raw",
    "matricula_raw",
    "discente_raw",
    "curso_completo",
    "curso",
    "unidade",
    "grau",
    "turno",
    "ano",
    "matricula",
    "discente",
    "duplicado_no_arquivo",
    "status_validacao",
    "erros_validacao",
    "processado_em",
]
silver = silver[colunas_silver]

validos = silver.loc[silver["status_validacao"] == "VALIDO"].copy()
gold = (
    validos.groupby(
        ["curso_completo", "curso", "unidade", "grau", "turno", "ano"],
        as_index=False,
        dropna=False,
    )
    .agg(total_discentes=("matricula", "nunique"))
    .sort_values(["curso", "ano"])
)
gold.insert(0, "batch_id", str(batch_id))
gold["processado_em"] = pd.Timestamp.now(tz="UTC")

# O nome das tabelas vem da tela de execução. A validação evita identificadores
# inesperados e torna o comportamento consistente com PostgreSQL sem aspas.
identificador = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
for rotulo, nome_tabela in (
    ("silver", tabela_silver),
    ("gold", tabela_gold),
):
    if not identificador.fullmatch(nome_tabela):
        raise ValueError(
            f"Nome da tabela {rotulo} inválido: {nome_tabela!r}. "
            "Use até 63 caracteres: letras minúsculas, números e underscore."
        )

# A mesma `connection` fornecida pelo worker mantém silver e gold na transação
# única; qualquer falha provoca rollback das duas gravações.
silver.to_sql(
    tabela_silver,
    connection,
    schema="silver",
    if_exists="append",
    index=False,
    method="multi",
    chunksize=1000,
)
gold.to_sql(
    tabela_gold,
    connection,
    schema="gold",
    if_exists="append",
    index=False,
    method="multi",
    chunksize=1000,
)

# Metadados úteis ao inspecionar o contexto em testes do worker.
resultado_pipeline = {
    "linhas_recebidas": int(len(silver)),
    "linhas_validas": int((silver["status_validacao"] == "VALIDO").sum()),
    "linhas_rejeitadas": int((silver["status_validacao"] == "REJEITADO").sum()),
    "linhas_gold": int(len(gold)),
}
