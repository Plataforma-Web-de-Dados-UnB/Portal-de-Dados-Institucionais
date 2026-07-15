# Limpeza e tipagem

df.columns = df.columns.str.strip()
df.rename(
    columns={
        "Refeições": "refeicoes",
        "Tipo": "tipo",
        "Período": "periodo",
    },
    inplace=True,
)

df["refeicoes"] = pd.to_numeric(df["refeicoes"], errors="coerce").astype("Int64")
df["tipo"] = df["tipo"].astype(str).str.strip()
df["periodo"] = df["periodo"].astype(str).str.strip()

df["batch_id"] = batch_id

# Silver: dados brutos normalizados

df.to_sql(tabela_silver, connection, schema="silver", if_exists="append", index=False)

# Gold: cópia direta sem agregação

df.to_sql(tabela_gold, connection, schema="gold", if_exists="append", index=False)

resultado_pipeline = {
    "linhas_recebidas": int(len(df)),
    "linhas_silver": int(len(df)),
    "linhas_gold": int(len(df)),
}
