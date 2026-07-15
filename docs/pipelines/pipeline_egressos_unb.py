# Limpeza e tipagem


def parse_ano_periodo(valor):
    try:
        partes = str(valor).strip().split("/")
        return int(partes[0]), int(partes[1])
    except Exception:
        return None, None


df.columns = [c.strip().lower().replace("-", "_") for c in df.columns]

df["matricula"] = df["matricula"].astype(str).str.strip()
df["nome"] = df["nome"].str.strip().str.title()
df["ingresso"] = df["ingresso"].astype(str).str.strip()
df["ano_periodo_formado"] = df["ano_periodo_formado"].astype(str).str.strip()

df[["ano_ingresso", "periodo_ingresso"]] = pd.DataFrame(
    df["ingresso"].apply(lambda v: list(parse_ano_periodo(v))),
    index=df.index,
)
df[["ano_formatura", "periodo_formatura"]] = pd.DataFrame(
    df["ano_periodo_formado"].apply(lambda v: list(parse_ano_periodo(v))),
    index=df.index,
)

df["semestres_cursados"] = (df["ano_formatura"] - df["ano_ingresso"]) * 2 + (
    df["periodo_formatura"] - df["periodo_ingresso"]
)


def classificar_tempo(semestres):
    if pd.isna(semestres):
        return "Indefinido"
    if semestres <= 8:
        return "No prazo"
    elif semestres <= 10:
        return "Leve atraso"
    elif semestres <= 14:
        return "Atrasado"
    else:
        return "Grande atraso"


df["classificacao_tempo"] = df["semestres_cursados"].apply(classificar_tempo)
df.dropna(subset=["matricula", "nome", "ano_ingresso", "ano_formatura"], inplace=True)
df = df[df["matricula"].str.isnumeric()]
df["batch_id"] = batch_id

# Silver: dados individuais normalizados

df.to_sql(tabela_silver, connection, schema="silver", if_exists="append", index=False)

# Gold 1: distribuição temporal (por ano de ingresso e formatura)

por_ingresso = (
    df.groupby("ano_ingresso", as_index=False)
    .agg(
        total_egressos=("matricula", "count"),
        media_semestres=("semestres_cursados", "mean"),
        min_semestres=("semestres_cursados", "min"),
        max_semestres=("semestres_cursados", "max"),
    )
    .rename(columns={"ano_ingresso": "ano"})
)
por_ingresso["dimensao"] = "ingresso"

por_formatura = (
    df.groupby("ano_formatura", as_index=False)
    .agg(
        total_egressos=("matricula", "count"),
        media_semestres=("semestres_cursados", "mean"),
        min_semestres=("semestres_cursados", "min"),
        max_semestres=("semestres_cursados", "max"),
    )
    .rename(columns={"ano_formatura": "ano"})
)
por_formatura["dimensao"] = "formatura"

gold_temporal = pd.concat([por_ingresso, por_formatura], ignore_index=True)
gold_temporal["media_semestres"] = gold_temporal["media_semestres"].round(2)
gold_temporal["batch_id"] = batch_id

gold_temporal.to_sql(
    tabela_gold, connection, schema="gold", if_exists="append", index=False
)

# Gold 2: distribuição por classificação de tempo de conclusão

gold_classificacao = df.groupby("classificacao_tempo", as_index=False).agg(
    total_egressos=("matricula", "count"),
    media_semestres=("semestres_cursados", "mean"),
)
gold_classificacao["media_semestres"] = gold_classificacao["media_semestres"].round(2)
gold_classificacao["batch_id"] = batch_id

gold_classificacao.to_sql(
    tabela_gold + "_classificacao",
    connection,
    schema="gold",
    if_exists="append",
    index=False,
)
