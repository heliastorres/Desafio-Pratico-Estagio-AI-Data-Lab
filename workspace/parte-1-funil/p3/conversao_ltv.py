# 3. Quais características da proposta mais se associam à contratação?
# Taxa de conversão por faixa de LTV
import pandas as pd

df = pd.read_csv("workspace/propostas_credito_tratado.csv")

# Faixas alinhadas com o limite da política de crédito (LTV máximo = 60%),
# pra já deixar visível se passar desse limite muda a conversão.
df["faixa_ltv"] = pd.cut(
    df["ltv"],
    bins=[0, 0.40, 0.50, 0.60, 0.70, 1.0],
    labels=["Até 40%", "40-50%", "50-60%", "60-70% (acima da política)", "70%+ (bem acima)"],
)

resumo = df.groupby("faixa_ltv").agg(
    total=("id_proposta", "count"),
    contratadas=("status_final", lambda s: (s == "Contratada").sum()),
)
resumo["taxa_conversao"] = resumo["contratadas"] / resumo["total"]

pd.options.display.float_format = "{:,.3f}".format
print(resumo)