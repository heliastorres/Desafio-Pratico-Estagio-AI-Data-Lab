import pandas as pd 

df = pd.read_csv("workspace/propostas_credito.csv")

log_tratamento = [] # vetor para log básico para os tratamentos de dados

# 1. valor_imovel: 3 linhas vieram com incoerência de registro, apresentando "R$" em vez
# de apenas números, causando o problema do pandas considerar essa coluna com registros
# string, mesmos as outras 6.397 linhas serem números. 
# Decisão de tratamento: remover o prefixo "R$" e os espaços, para assim converter a
# coluna para float.

# retorna o número de linhas onde "R$" está presente.
qtd_antes = df["valor_imovel"].astype(str).str.contains("R$", regex=False).sum() 

df["valor_imovel"] = (
    df["valor_imovel"]
    .astype(str)
    .str.replace("R$", "", regex=False) # remove o "R$"
    .str.strip() # remove espaços que sobraram
    .astype(float) # converte a coluna em float
)

# log 1: primeiro decisão de tratamento
log_tratamento.append(f"valor_imovel: {qtd_antes} linhas tinham o prefixo 'R$ '"
"e impediam a coluna de virar número. Prefixo removido e coluna convertida para float.")

print("valor_imovel agora é do tipo:", df["valor_imovel"].dtype)


# 2. adicionar uma coluna ltv: apesar de ter no dicionário de dados, a coluna ltv não 
# existe no csv.
# decisão: calcular o ltv. valor_solicitado / valor_imovel
# importante que todos os registros de valor_imovel sejam float. 

# cria a coluna "ltv" e guarda o esultado dessa divisão no formato decimal. Como estou 
# utilizando pandas para tratar os dados, o próprio pandas faz divisão linha por linhas,
# substituindo aplicar um laço for para todos os registros. 
df["ltv"] = df["valor_solicitado"] / df["valor_imovel"] 

# log 2: adicionar a coluna "ltv"
log_tratamento.append("ltv: a coluna nao existia no csv, apesar de indicar no csv,"
"a coluna foi adicionada com o cálculo correto.")

print("Exemplo de LTV calculado:")
print(df[["id_proposta", "valor_solicitado", "valor_imovel", "ltv"]].head(3))

# 3. idade_clinte: 1 linha com idade = 14 (ilegível para contrato de crédito imobiliário)
# decisão: marcar célula como ausente (NaN), seria a melhor escolher, ao invés de chutar
# uma idade qualquer, ou pior, descartar o registro. 

# atribui valores booleanos a variável com intervalo de 18 até 100 anos. 
idade_invalida = (df["idade_cliente"] < 18) | (df["idade_cliente"] > 100) 

# soma os valores booleanos, resulta no número de registros com idades incopatíveis. 
qtd_idade_invalida = idade_invalida.sum() 

# percorre a coluna idade_cliente localizando onde 18 > idade > 100 e substituindo a 
# célula por NA (dado ausente). 
df.loc[idade_invalida, "idade_cliente"] = pd.NA 

log_tratamento.append(f"idade_cliente: {qtd_idade_invalida} linha com idade"
"incompatível. Valor trocado por ausente (NA), pois não faz sentido chutar um valor,"
"ou descartar o registro")

# 4. etapa_max_funil: 1 linha com valor 7 (fora do intervalo esperado de 1 a 6)
# decisão: corrigir de 7 para 6, pois temos uma forma segura de afirmar que essa 
# proposta foi efetivada, pois toda proposta com status_final = "Contratada" sempre tem 
# etapa_max_funil = 6. Por isso, 7 só pode ser um erro de digitação, sendo observado 
# a partir das 1241 linhas que se repetem esse padrão, que seria justamente a quantidade
# de contratos assiandos. 

# variável recebe valor booleano dos registros etapa_max_funil maiores que 6. 
etapa_invalida = df["etapa_max_funil"] > 6 
# soma os valores booleanos, retornando a quantidade de linhas em que etapa_max_funil é
# maior que 6. 
qtd_etapa_invalida = etapa_invalida.sum()

# localiza registro true e sobreescreve com 6.
df.loc[etapa_invalida, "etapa_max_funil"] = 6 

log_tratamento.append(f"etapa_max_funil: {qtd_etapa_invalida} linha com valor 7"
"( fora do intervalo 1 a 6) Corrigida para 6, pois a linha é 'Contratada'")

# 5. data_entrada: 3 linhas vieram em formato DD/MM/AAAA, o resto em AAAA-MM-DD
# decisão: usar uma máscara booleana (true/false por linha) para achar só as linhas 
# com "/" no texto, e reescrever apenas essas linhas no mesmo padrão de texto das demais
# (AAAA-MM-DD). Só depois que a coluna inteira estiver no mesmo padrão de texto é que 
# convertemos tudo de uma vez para datetime (fazer isso antes dá erro, porque não dá pra
# misturar texto e datetime numa mesma coluna que ainda não foi convertida).

# cria a máscara para verificar os valores com "/", lê tudo como string
# na=False, se data_entrada for NaN, seja considerado como False, assim como os demais
# registros que estão na formatação correta: AA-MM-DD
barras = df["data_entrada"].str.contains("/", na=False) # retorna valores booleanos
qtd_data_mista = barras.sum() # quantidade de registros com data mista
 
# percorre a coluna data_entradas lendo as datas sabendo que o dia vem primeiro
df.loc[barras, "data_entrada"] = pd.to_datetime(
    df.loc[barras, "data_entrada"], format="%d/%m/%Y"
).dt.strftime("%Y-%m-%d")  # devolve como texto, no padrão AAAA-MM-DD
 
# converte as strings de data para datetime do pandas.
df["data_entrada"] = pd.to_datetime(df["data_entrada"], format="%Y-%m-%d")
 
log_tratamento.append(f"data_entrada: {qtd_data_mista} linhas vieram no formato "
"DD/MM/AAAA em vez de AAAA-MM-DD. Convertidas para o mesmo padrão de data do pandas.")

# converte a data de assinatura, que já está no formato AAAA-MM-DD. 
df["data_assinatura_contrato"] = pd.to_datetime(
    df["data_assinatura_contrato"], format="%Y-%m-%d", errors="coerce")

# 6. canal_origem: 4 linhas com escritas inconstantes (minúsculas, maiúsculas e espaços
# extras.)
# decisão: padronizar início com maiúscula e remover espaços extras. 

# exploração exploratória de todos os registros para confirmar quantas incontâncias e 
# quais os textos que não mantém o padrão. 
print("\nValores únicos de canal_origem antes do tratamento:")
print(sorted(df["canal_origem"].unique()))

canal_original = df["canal_origem"].copy() # faz cópia do original para comparação

# remove espaços extras das strings
df["canal_origem"] = df["canal_origem"].str.strip()

# cria uma versão "normalizada", apenas para identificar quais os canais_origem temos
normalizado = df["canal_origem"].str.lower()

# variável que recebe a grafia correta das strings que aparece mais vezes, isso evita
# ter que escrever o mapa de correção manualmente
grafia_correta_por_grupo = (
    df.groupby(normalizado)["canal_origem"]
    .agg(lambda valores: valores.value_counts().idxmax()))

# aplica a grafia correta no canal_origem de acordo com o grupo normalizado. 
df["canal_origem"] = normalizado.map(grafia_correta_por_grupo)

# mostra a contagem de inconstâncias, compara a cópia do canal_origem com o normalizado
qtd_canal_inc = (df["canal_origem"] != canal_original).sum() # inc = incontante

print("\nValores únicos de canal_origem depois do tratamento:")
print(sorted(df["canal_origem"].unique()))

log_tratamento.append(f"canal_origem: {qtd_canal_inc} linhas com espaços extras e "
    "letras minúscula. Corrigidas automaticamente para a grafia mais frequente do "
    "seu grupo, após conferir com .unique() que não havia nenhuma outra inconsistência.")

# 7. renomear a coluna de taxa_juros_aa para taxa_juros_am, pois os pontos percentuais
# está ao mês, visto que no Brasil a taxa de juros ao mês varia entre 1,0% a 1,5% ao mês
# desisão: renomear apenas o nome da coluna, o dicionário de dados está correto, apenas 
# o nome da coluna está errada.
df = df.rename(columns={"taxa_juros_aa": "taxa_juros_am"})

log_tratamento.append("taxa_juros_aa: renomeada para taxa_juros_am, pois o dicionário "
"de dados descreve coluna sendo taxa de juros ao mês, porém o nome da coluna é ao ano")

# 8. a proposta PR-001556 tem data_assinatura_contrato: 1 linhas incoerente, pois a data
# de assinatura é anterior a data de entrada da proposta, o que seria impossível, não 
# tem como assinar um contrato antes da proposta. 
# data_entrada = 2025-09-11 e data_assinatura_contrato = 2025-05-08
# decisão: marcar data_assinatura_contrato como ausente e verificar se existe alguma 
# data de assinatura de contrato antes da data de entrada. 

data_impossivel = (
    df["data_assinatura_contrato"].notna()
    & (df["data_assinatura_contrato"] < df["data_entrada"]))

qtd_data_impossivel = data_impossivel.sum()
 
df.loc[data_impossivel, "data_assinatura_contrato"] = pd.NaT

log_tratamento.append(f"data_assinatura_contrato: {qtd_data_impossivel} linha com data de"
"assinatura anterior à data de entrada, valor trocado por ausente")

# 9. registro de tratamento de dados (log)
print("\nRegistro dos tratamentos de dados: \n")
for linha in log_tratamento:
    print(linha,"\n")

# 10. cria outro documento e salva a base de dados tratada. 
df.to_csv("workspace/propostas_credito_tratado.csv", index=False)
print("\nArquivo tratado salvo em propostas_credito_tratado.csv")
print("Formato final:", df.shape)