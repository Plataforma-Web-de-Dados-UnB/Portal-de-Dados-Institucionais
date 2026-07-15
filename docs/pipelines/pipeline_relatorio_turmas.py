import re

# Limpeza e tipagem

df.columns = df.columns.str.strip()
df.rename(
    columns={
        "Código": "codigo",
        "Componente Curricular": "componente",
        "Situação": "situacao",
    },
    inplace=True,
)
df.rename(columns=str.lower, inplace=True)
df.rename(columns=lambda c: re.sub(r"\s+", "_", c.strip()), inplace=True)

df["departamento"] = df["departamento"].str.strip()
df["componente"] = df["componente"].str.strip()
df["situacao"] = df["situacao"].str.strip().str.upper()
df["ch"] = pd.to_numeric(df["ch"], errors="coerce")
df["ct"] = pd.to_numeric(df["ct"], errors="coerce")


def extrair_numero(valor):
    """Extrai apenas a parte numérica de valores como '25.0 (92,59%)' ou '4,68'."""
    s = str(valor).split("(")[0].strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


for col in [
    "ap",
    "an",
    "rp",
    "rn",
    "rf",
    "rnf",
    "repmf",
    "tr",
    "ma",
    "es",
    "ca",
    "total",
    "mfa",
]:
    df[col] = df[col].apply(extrair_numero)

df["batch_id"] = batch_id

# Silver: dados brutos normalizados

df.to_sql(tabela_silver, connection, schema="silver", if_exists="append", index=False)

# Gold 1: média de MFA e taxa de aprovação por componente

gold_componentes = df.groupby(["codigo", "componente"], as_index=False).agg(
    turmas=("ct", "count"),
    total_alunos=("total", "sum"),
    aprovados=("ap", "sum"),
    mfa_media=("mfa", "mean"),
    ch=("ch", "first"),
)

gold_componentes["taxa_aprovacao"] = (
    gold_componentes["aprovados"] / gold_componentes["total_alunos"]
).round(4)
gold_componentes["mfa_media"] = gold_componentes["mfa_media"].round(2)
gold_componentes["batch_id"] = batch_id

gold_componentes.to_sql(
    tabela_gold, connection, schema="gold", if_exists="append", index=False
)

# Gold 2: resumo por departamento

gold_departamento = df.groupby("departamento", as_index=False).agg(
    total_alunos=("total", "sum"),
    aprovados=("ap", "sum"),
    mfa_media=("mfa", "mean"),
    componentes_unicos=("codigo", "nunique"),
)

gold_departamento["taxa_aprovacao"] = (
    gold_departamento["aprovados"] / gold_departamento["total_alunos"]
).round(4)
gold_departamento["mfa_media"] = gold_departamento["mfa_media"].round(2)
gold_departamento["batch_id"] = batch_id

gold_departamento.to_sql(
    tabela_gold + "_por_departamento",
    connection,
    schema="gold",
    if_exists="append",
    index=False,
)
