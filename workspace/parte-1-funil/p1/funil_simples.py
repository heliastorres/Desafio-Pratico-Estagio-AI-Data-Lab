# 1. Onde perde mais propostas = na etapa 3 
# se diminuirmos etapa 3 menos etapa 4 temos uma perda de 1.799 propostas
# gráfico simples: funil de propostas por etapa
import pandas as pd
import plotly.express as px

df = pd.read_csv("workspace/propostas_credito_tratado.csv")

nome_etapa = {
    1: "1. Simulação",
    2: "2. Lead",
    3: "3. Análise de crédito",
    4: "4. Avaliação do imóvel",
    5: "5. Formalização",
    6: "6. Contratação",
}

# tabela pequena (uma linha por etapa), recebe um dataframe pronto
funil = pd.DataFrame({
    "etapa": nome_etapa.values(),
    "propostas": [(df["etapa_max_funil"] >= e).sum() for e in nome_etapa],
})

# px.funnel: definindo qual é o rótulo (y) e qual é o valor (x).
fig = px.funnel(funil, x="propostas", y="etapa", title="Funil de propostas por etapa")
fig.write_html("workspace/parte-1-funil/p1/funil_propostas.html")
print("Gráfico salvo!")
print(funil)