# A conversão caiu? O canal de correspondentes está mal?
# A parte "o canal de correspondentes está mal" da liderança está certa. Mas a forma 
# como ela disse como se fosse algo que piorou recentemente não se confirma 
# exatamente. Os dados mostram que esse canal já nasceu fraco e continua fraco, 
# de forma consistente. Não é uma queda nova, é um problema 
# estrutural antigo que só ficou mais visível agora.

import pandas as pd
 
df = pd.read_csv("workspace/propostas_credito_tratado.csv",
    parse_dates=["data_entrada"],)

 
# Cria uma coluna simples: "Correspondente" ou "Demais canais"
df["grupo_canal"] = df["canal_origem"].apply(
    lambda c: "Correspondente" if c == "Correspondente" else "Demais canais"
)
 
# Cria a coluna de mês
df["mes_entrada"] = df["data_entrada"].dt.to_period("M")
 
# Agrupa por mês e por grupo de canal ao mesmo tempo
resumo = df.groupby(["mes_entrada", "grupo_canal"]).agg(
    total=("id_proposta", "count"),
    contratadas=("status_final", lambda s: (s == "Contratada").sum()),
)
resumo["taxa_conversao"] = resumo["contratadas"] / resumo["total"]
 
pd.options.display.float_format = "{:,.3f}".format
print(resumo)