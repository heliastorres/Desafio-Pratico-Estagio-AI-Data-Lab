# PARTE 2 - RPA: rotina automática do relatório semanal do funil
# Construção peça por peça. Peça 1: ler o arquivo bruto, com log e
# tratamento de erro caso o arquivo não exista ou esteja vazio.

import logging
import sys
import pandas as pd

# Configuração do log: toda vez que a rotina rodar, ela escreve o que
# aconteceu em duas saídas ao mesmo tempo:
# 1) na tela (pra quem está rodando na hora ver)
# 2) num arquivo (relatorio_semanal.log), pra quem for investigar depois
# um problema que aconteceu numa execução passada.

logging.basicConfig(
    level=logging.INFO, # nível INFO = registra passos normais, não só erros
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("workspace/parte-2-rpa/relatorio/relatorio_semanal.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def ler_dados_brutos(caminho_arquivo):
    """
    Lê o CSV bruto de propostas de crédito.

    Por que essa função existe separada: se alguém trocar o arquivo de
    lugar, ou o arquivo chegar corrompido/vazio numa segunda-feira em que
    ninguém está olhando, queremos um erro CLARO no log, em vez do
    programa quebrar com uma mensagem técnica confusa do pandas.
    """
    try:
        df = pd.read_csv(caminho_arquivo)
    except FileNotFoundError:
        log.error(f"Arquivo não encontrado: {caminho_arquivo}")
        raise
    except pd.errors.EmptyDataError:
        log.error(f"Arquivo encontrado, mas está vazio: {caminho_arquivo}")
        raise

    if len(df) == 0:
        # Um caso diferente do "arquivo vazio": o arquivo tem cabeçalho,
        # mas nenhuma linha de dado. O pandas não considera isso um erro
        # sozinho, então checamos isso manualmente.
        log.error(f"Arquivo lido, mas não tem nenhuma linha de dado: {caminho_arquivo}")
        raise ValueError("Arquivo sem linhas de dados.")

    log.info(f"Arquivo lido com sucesso: {len(df)} linhas, {len(df.columns)} colunas.")
    return df


def validar_schema(df, colunas_esperadas):
    """
    Confere se o DataFrame tem as colunas que a rotina espera.

    Duas situações possíveis, com respostas DIFERENTES de propósito:

    1) Falta uma coluna esperada -> ERRO que interrompe a execução.
       Se faltar, por exemplo, valor_solicitado, não tem como calcular
       o funil corretamente - é melhor parar e avisar do que gerar um
       relatório errado sem ninguém perceber.

    2) Aparece uma coluna nova, que a gente não esperava -> só um AVISO
       no log, e a rotina continua normalmente. Uma coluna nova não
       quebra os cálculos que já fazemos; só significa que o sistema de
       origem mudou e alguém pode querer investigar depois.
    """
    colunas_do_arquivo = set(df.columns)
    colunas_esperadas = set(colunas_esperadas)

    faltando = colunas_esperadas - colunas_do_arquivo
    novas = colunas_do_arquivo - colunas_esperadas

    if faltando:
        log.error(f"Colunas esperadas que NÃO vieram no arquivo: {sorted(faltando)}")
        raise ValueError(f"Arquivo incompleto - faltam colunas: {sorted(faltando)}")

    if novas:
        log.warning(f"Colunas novas no arquivo, não esperadas (serão ignoradas): {sorted(novas)}")

    log.info("Validação de schema: todas as colunas esperadas estão presentes.")


# Lista das colunas que o arquivo bruto precisa ter, para a rotina
# funcionar (é a mesma lista de colunas do CSV original, antes do
# tratamento da Parte 1).
COLUNAS_ESPERADAS = [
    "id_proposta", "data_entrada", "canal_origem", "cidade", "uf",
    "tipo_imovel", "valor_imovel", "valor_solicitado", "prazo_meses",
    "score_credito", "idade_cliente", "renda_mensal_declarada",
    "flag_cliente_recorrente", "consultor_id", "etapa_max_funil",
    "status_final", "tempo_analise_dias", "data_assinatura_contrato",
    "taxa_juros_aa",
]


def tratar_dados(df):
    """
    Aplica as mesmas correções decididas na Parte 1 (ver
    REGISTRO_TRATAMENTO.md para a explicação completa de cada uma).

    Diferente do script da Parte 1 (feito para explorar e explicar), aqui
    a função precisa rodar sem supervisão, então cada correção é escrita
    de forma genérica (não amarrada a um id_proposta específico) e tudo
    que aconteceu vai pro log, em vez de print().

    Retorna: (df tratado, lista de textos com o resumo do que foi feito)
    """
    df = df.copy() # nunca mexe no DataFrame original recebido
    resumo = []

    # 1) valor_imovel: remover prefixo "R$" se existir, e converter p/ float
    qtd = df["valor_imovel"].astype(str).str.contains("R$", regex=False).sum()
    df["valor_imovel"] = (
        df["valor_imovel"].astype(str).str.replace("R$", "", regex=False)
        .str.strip().astype(float)
    )
    resumo.append(f"valor_imovel: {qtd} linha(s) com prefixo 'R$' corrigidas.")

    # 2) ltv: calcular (só se ainda não existir a coluna)
    if "ltv" not in df.columns:
        df["ltv"] = df["valor_solicitado"] / df["valor_imovel"]
        resumo.append("ltv: coluna calculada (valor_solicitado / valor_imovel).")

    # 3) idade_cliente: marcar como ausente se fora da faixa 18-100
    mask = (df["idade_cliente"] < 18) | (df["idade_cliente"] > 100)
    qtd = mask.sum()
    df.loc[mask, "idade_cliente"] = pd.NA
    resumo.append(f"idade_cliente: {qtd} linha(s) implausível(is) marcada(s) como ausente.")

    # 4) etapa_max_funil: corrigir valores acima de 6 para 6
    mask = df["etapa_max_funil"] > 6
    qtd = mask.sum()
    df.loc[mask, "etapa_max_funil"] = 6
    resumo.append(f"etapa_max_funil: {qtd} linha(s) fora do intervalo (>6) corrigida(s) para 6.")

    # 5) data_entrada: padronizar formato DD/MM/AAAA para AAAA-MM-DD, depois
    # converter a coluna inteira para datetime
    mask = df["data_entrada"].astype(str).str.contains("/", na=False)
    qtd = mask.sum()
    df.loc[mask, "data_entrada"] = pd.to_datetime(
        df.loc[mask, "data_entrada"], format="%d/%m/%Y"
    ).dt.strftime("%Y-%m-%d")
    df["data_entrada"] = pd.to_datetime(df["data_entrada"], format="%Y-%m-%d")
    resumo.append(f"data_entrada: {qtd} linha(s) com formato de data diferente, padronizada(s).")

    df["data_assinatura_contrato"] = pd.to_datetime(
        df["data_assinatura_contrato"], format="%Y-%m-%d", errors="coerce"
    )

    # 6) canal_origem: remover espaço e corrigir para a grafia mais comum
    # de cada grupo normalizado
    canal_original = df["canal_origem"].copy()
    df["canal_origem"] = df["canal_origem"].str.strip()
    normalizado = df["canal_origem"].str.lower()
    grafia_correta = df.groupby(normalizado)["canal_origem"].agg(
        lambda valores: valores.value_counts().idxmax()
    )
    df["canal_origem"] = normalizado.map(grafia_correta)
    qtd = (df["canal_origem"] != canal_original).sum()
    resumo.append(f"canal_origem: {qtd} linha(s) com grafia inconsistente, padronizada(s).")

    # 7) taxa_juros_aa para taxa_juros_am (só renomeia se a coluna antiga existir)
    if "taxa_juros_aa" in df.columns:
        df = df.rename(columns={"taxa_juros_aa": "taxa_juros_am"})
        resumo.append("taxa_juros_aa: renomeada para taxa_juros_am (nome incoerente com o dicionário).")

    # 8) data_assinatura_contrato: marcar como ausente se vier antes da
    # data de entrada (impossível)
    mask = (
        df["data_assinatura_contrato"].notna()
        & (df["data_assinatura_contrato"] < df["data_entrada"])
    )
    qtd = mask.sum()
    df.loc[mask, "data_assinatura_contrato"] = pd.NaT
    resumo.append(f"data_assinatura_contrato: {qtd} linha(s) com data impossível, marcada(s) como ausente.")

    for linha in resumo:
        log.info(linha)

    return df, resumo


# Teste rápido: rodar a função com o arquivo real, pra confirmar que
# funciona no caso "normal" antes de testar os casos de erro.

def calcular_metricas(df):
    """
    Calcula as métricas-chave do funil, já usadas no diagnóstico da
    Parte 1. Retorna um dicionário com cada métrica separada, pronto
    para o passo seguinte (exportar para o relatório em PDF).
    """
    metricas = {}

    # 1) Resumo geral: quantas propostas, quantas contrataram, taxa
    total_propostas = len(df)
    total_contratadas = (df["status_final"] == "Contratada").sum()
    metricas["resumo_geral"] = {
        "total_propostas": total_propostas,
        "total_contratadas": total_contratadas,
        "taxa_conversao": total_contratadas / total_propostas,
        "dinheiro_solicitado_total": df["valor_solicitado"].sum(),
        "dinheiro_contratado": df.loc[df["status_final"] == "Contratada", "valor_solicitado"].sum(),
    }

    # 2) Funil por etapa: quantas propostas e quanto dinheiro chegou
    # em cada uma das 6 portas (etapa_max_funil >= etapa)
    nome_etapa = {
        1: "1. Simulação", 2: "2. Lead", 3: "3. Análise de crédito",
        4: "4. Avaliação do imóvel", 5: "5. Formalização", 6: "6. Contratação",
    }
    linhas_funil = []
    for etapa in range(1, 7):
        chegou = df["etapa_max_funil"] >= etapa
        linhas_funil.append({
            "etapa": nome_etapa[etapa],
            "propostas": int(chegou.sum()),
            "dinheiro": df.loc[chegou, "valor_solicitado"].sum(),
        })
    metricas["funil_por_etapa"] = pd.DataFrame(linhas_funil)

    # 3) Conversão por canal de origem
    por_canal = df.groupby("canal_origem").agg(
        propostas=("id_proposta", "count"),
        contratadas=("status_final", lambda s: (s == "Contratada").sum()),
    )
    por_canal["taxa_conversao"] = por_canal["contratadas"] / por_canal["propostas"]
    metricas["conversao_por_canal"] = por_canal.sort_values("taxa_conversao")

    log.info(
        f"Métricas calculadas: {total_propostas} propostas, "
        f"{total_contratadas} contratadas ({metricas['resumo_geral']['taxa_conversao']:.1%})."
    )

    return metricas


def exportar_pdf(metricas, resumo_tratamento, caminho_saida):
    """
    Monta o relatório final em PDF, pronto para ser enviado à liderança.

    Usa reportlab (Platypus) porque ele monta o documento como uma lista
    de "blocos" (título, parágrafo, tabela...) que vão se organizando na
    página sozinhos - não precisamos calcular posição x/y na mão.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(caminho_saida, pagesize=A4)
    conteudo = [] # lista de "blocos" que vão entrar no PDF, em ordem

    # Título e data de geração
    conteudo.append(Paragraph("Relatório Semanal do Funil de Crédito", styles["Title"]))
    data_hoje = pd.Timestamp.now().strftime("%d/%m/%Y")
    conteudo.append(Paragraph(f"Gerado automaticamente em {data_hoje}", styles["Normal"]))
    conteudo.append(Spacer(1, 0.7 * cm))

    # Bloco 1: resumo geral
    rg = metricas["resumo_geral"]
    conteudo.append(Paragraph("Resumo Geral", styles["Heading2"]))
    texto_resumo = (
        f"Total de propostas: {rg['total_propostas']:,} &nbsp;|&nbsp; "
        f"Contratadas: {rg['total_contratadas']:,} &nbsp;|&nbsp; "
        f"Taxa de conversão: {rg['taxa_conversao']:.1%}<br/>"
        f"Dinheiro solicitado (total): R$ {rg['dinheiro_solicitado_total']:,.2f}<br/>"
        f"Dinheiro efetivamente contratado: R$ {rg['dinheiro_contratado']:,.2f}"
    )
    conteudo.append(Paragraph(texto_resumo, styles["Normal"]))
    conteudo.append(Spacer(1, 0.5 * cm))

    # Bloco 2: funil por etapa (tabela)
    conteudo.append(Paragraph("Funil por Etapa", styles["Heading2"]))
    funil = metricas["funil_por_etapa"]
    dados_tabela = [["Etapa", "Propostas", "Dinheiro solicitado (R$)"]]
    for _, linha in funil.iterrows():
        dados_tabela.append([
            linha["etapa"], f"{linha['propostas']:,}", f"{linha['dinheiro']:,.2f}"
        ])
    tabela_funil = Table(dados_tabela, hAlign="LEFT")
    tabela_funil.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    conteudo.append(tabela_funil)
    conteudo.append(Spacer(1, 0.5 * cm))

    # Bloco 3: conversão por canal (tabela)
    conteudo.append(Paragraph("Conversão por Canal de Origem", styles["Heading2"]))
    canal = metricas["conversao_por_canal"]
    dados_canal = [["Canal", "Propostas", "Contratadas", "Taxa de conversão"]]
    for nome_canal, linha in canal.iterrows():
        dados_canal.append([
            nome_canal, f"{int(linha['propostas']):,}", f"{int(linha['contratadas']):,}",
            f"{linha['taxa_conversao']:.1%}",
        ])
    tabela_canal = Table(dados_canal, hAlign="LEFT")
    tabela_canal.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    conteudo.append(tabela_canal)
    conteudo.append(Spacer(1, 0.5 * cm))

    # Bloco 4: registro de tratamento de dados dessa execução
    conteudo.append(Paragraph("Registro de Tratamento de Dados (desta execução)", styles["Heading2"]))
    for linha in resumo_tratamento:
        conteudo.append(Paragraph(f"• {linha}", styles["Normal"]))

    doc.build(conteudo)
    log.info(f"Relatório em PDF exportado com sucesso: {caminho_saida}")


# Teste rápido: rodar a função com o arquivo real, pra confirmar que
# funciona no caso "normal" antes de testar os casos de erro.

if __name__ == "__main__":
    df = ler_dados_brutos("workspace/propostas_credito.csv")
    validar_schema(df, COLUNAS_ESPERADAS)
    df, resumo_tratamento = tratar_dados(df)
    metricas = calcular_metricas(df)
    exportar_pdf(metricas, resumo_tratamento, "workspace/parte-2-rpa/relatorio/relatorio_semanal_funil.pdf")
