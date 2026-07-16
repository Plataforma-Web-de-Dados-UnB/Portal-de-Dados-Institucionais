# Limpeza e tipagem

df.columns = df.columns.str.strip()
df.rename(
    columns={
        "Código disciplina": "codigo_disciplina",
        "Nome disciplina": "nome_disciplina",
        "Qtd de estudantes": "qtd_estudantes",
        "Aprovações": "aprovacoes",
        "Reprovações": "reprovacoes",
        "Abandonos": "abandonos",
        "Taxa de aprovação": "taxa_aprovacao",
        "Taxa de reprovação": "taxa_reprovacao",
    },
    inplace=True,
)

# Identificadores e descrições permanecem como texto.
df["codigo_disciplina"] = df["codigo_disciplina"].astype(str).str.strip()
df["nome_disciplina"] = df["nome_disciplina"].astype(str).str.strip()

# Quantidades são armazenadas como inteiros anuláveis. Valores que não puderem
# ser convertidos tornam-se nulos, em vez de interromper toda a execução.
colunas_inteiras = [
    "qtd_estudantes",
    "aprovacoes",
    "reprovacoes",
    "abandonos",
]
for coluna in colunas_inteiras:
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce").astype("Int64")

# As taxas são números decimais entre 0 e 1. A substituição também permite que
# futuros arquivos utilizem vírgula como separador decimal.
colunas_decimais = ["taxa_aprovacao", "taxa_reprovacao"]
for coluna in colunas_decimais:
    df[coluna] = pd.to_numeric(
        df[coluna].astype(str).str.strip().str.replace(",", ".", regex=False),
        errors="coerce",
    ).astype("Float64")

df["batch_id"] = batch_id

# Silver: dados normalizados e com tipos numéricos.

df.to_sql(tabela_silver, connection, schema="silver", if_exists="append", index=False)

# Gold: cópia direta sem agregação.

df.to_sql(tabela_gold, connection, schema="gold", if_exists="append", index=False)

resultado_pipeline = {
    "linhas_recebidas": int(len(df)),
    "linhas_silver": int(len(df)),
    "linhas_gold": int(len(df)),
}
