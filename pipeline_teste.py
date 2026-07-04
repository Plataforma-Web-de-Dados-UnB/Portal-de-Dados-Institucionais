# Pipeline de teste: processa notas de alunos
# Variaveis disponíveis: df, batch_id, engine, tabela_silver, tabela_gold

import pandas as pd
from sqlalchemy import text

# --- Silver: limpeza e tipagem ---
df["matricula"] = df["matricula"].astype(str).str.strip()
df["nome"] = df["nome"].str.strip().str.title()
df["curso"] = df["curso"].str.strip()
df["nota_final"] = pd.to_numeric(df["nota_final"], errors="coerce").fillna(0.0)
df["situacao"] = df["situacao"].str.strip().str.capitalize()
df["batch_id"] = batch_id

df.to_sql(tabela_silver, engine, schema="silver", if_exists="append", index=False)

# --- Gold: OBT agregada por curso ---
gold_df = (
    df.groupby("curso")
    .agg(
        total_alunos=("matricula", "count"),
        media_nota=("nota_final", "mean"),
        aprovados=("situacao", lambda x: (x == "Aprovado").sum()),
        reprovados=("situacao", lambda x: (x == "Reprovado").sum()),
    )
    .reset_index()
)
gold_df["taxa_aprovacao"] = (
    gold_df["aprovados"] / gold_df["total_alunos"] * 100
).round(2)
gold_df["batch_id"] = batch_id

gold_df.to_sql(tabela_gold, engine, schema="gold", if_exists="append", index=False)
