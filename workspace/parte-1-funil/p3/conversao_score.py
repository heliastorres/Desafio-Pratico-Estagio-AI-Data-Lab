# 3. Quais características da proposta mais se associam à contratação?
# Taxa de conversão por faixa de score de crédito
import pandas as pd

df = pd.read_csv("workspace/propostas_credito_tratado.csv")

# pd.cut() transforma um número contínuo (score) em faixas (categorias).
# bins = os "cortes" das faixas; labels = o nome de cada faixa.
df["faixa_score"] = pd.cut(
    df["score_credito"],
    bins=[0, 600, 700, 800, 1000],
    labels=["Baixo (até 600)", "Médio (601-700)", "Alto (701-800)", "Muito alto (800+)"],
)

resumo = df.groupby("faixa_score").agg(
    total=("id_proposta", "count"),
    contratadas=("status_final", lambda s: (s == "Contratada").sum()),
)
resumo["taxa_conversao"] = resumo["contratadas"] / resumo["total"]

pd.options.display.float_format = "{:,.3f}".format
print(resumo)