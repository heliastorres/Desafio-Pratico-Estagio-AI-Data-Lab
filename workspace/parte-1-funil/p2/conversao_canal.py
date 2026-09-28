# "A conversão caiu nos últimos meses e o canal de correspondentes não
# está performando. Precisamos entender onde estamos perdendo dinheiro
#no funil."
# A percepção da liderança se confirma? = Sim, podemos ver o percentual conversão de cada
# canal.
import pandas as pd
 
df = pd.read_csv("workspace/propostas_credito_tratado.csv")
 
# Para cada canal: quantas propostas no total, e quantas viraram "Contratada".
resumo_canal = df.groupby("canal_origem").agg(
    total_propostas=("id_proposta", "count"),
    contratadas=("status_final", lambda s: (s == "Contratada").sum()),
)
resumo_canal["taxa_conversao"] = resumo_canal["contratadas"] / resumo_canal["total_propostas"]
 
# Ordenar do pior canal para o melhor, para facilitar a leitura
resumo_canal = resumo_canal.sort_values("taxa_conversao")
 
pd.options.display.float_format = "{:,.3f}".format
print(resumo_canal)