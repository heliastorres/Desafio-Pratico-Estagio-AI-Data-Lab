# 1. Onde perde mais dinheiro
import pandas as pd
 
pd.set_option("display.float_format", lambda x: "%.2f" % x)

df = pd.read_csv("workspace/propostas_credito_tratado.csv")
 
# .groupby("etapa_max_funil") junta todas as linhas que têm o mesmo valor
# nessa coluna e depois soma o valor_solicitado dentro de cada grupo.
soma_por_etapa = df.groupby("etapa_max_funil")["valor_solicitado"].sum()
 
 # com a soma, vemos que na etapa 3 é concentrada a maior soma de valores solicitados
print(soma_por_etapa)