# PARTE 3 - Extração com IA (Gemini): schema de saída e leitura dos laudos
import glob
import json
import os
import re
import time
from typing import Optional, List
from pydantic import BaseModel

MODELO = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


class Area(BaseModel):
    rotulo: str # o nome que o proprio documento usa
    valor_m2: float


class ResponsavelTecnico(BaseModel):
    nome: Optional[str]
    registro: Optional[str] # ex: "CREA-SP 5061234567"


class LaudoExtraido(BaseModel):
    tipo_imovel: Optional[str]
    endereco: Optional[str]
    areas: List[Area] # lista vazia se nenhuma área for encontrada
    ano_construcao: Optional[int] # só quando o ANO exato é dito
    idade_aproximada_anos: Optional[int] # só quando vem "idade aparente/aproximada"
    valor_avaliacao: Optional[float]
    matricula: Optional[str]
    onus_situacao: str # "sem_onus" | "com_onus" | "nao_verificavel"
    onus_detalhe: Optional[str]
    data_vistoria: Optional[str] # formato ISO: AAAA-MM-DD
    responsavel_tecnico: Optional[ResponsavelTecnico]
    contradicoes: List[str] # vazio se o documento não se contradiz


class CotaDiariaEsgotada(Exception):
    """A cota diária da API acabou: tentar de novo hoje não adianta."""


def ler_laudos(pasta):
    laudos = {}
    for caminho in sorted(glob.glob(f"{pasta}/*.txt")):
        nome_arquivo = caminho.split("/")[-1]
        with open(caminho, encoding="utf-8") as f:
            laudos[nome_arquivo] = f.read()
    return laudos


INSTRUCOES_SISTEMA = """
Você é um extrator de dados de laudos de avaliação de imóveis. Sua única
tarefa é ler o texto do laudo e preencher os campos pedidos, seguindo estas
regras SEM EXCEÇÃO:

1. Extraia SOMENTE o que está explicitamente escrito no texto. Nunca
   calcule, estime ou "complete" uma informação que não esteja lá.

2. Se um campo não aparece no documento, devolva null (ou lista vazia,
   quando o campo for uma lista). Não adivinhe.

3. ano_construcao: preencha SOMENTE se o documento disser um ano exato de
   construção. Se o documento disser apenas uma "idade aparente" ou
   "idade aproximada" (ex: "aproximadamente 18 anos"), NÃO calcule o ano -
   preencha idade_aproximada_anos com esse número e deixe ano_construcao
   como null.

4. areas: para CADA área mencionada no texto, crie um item com o rótulo
   exatamente como o documento descreve (ex: "área privativa", "área do
   terreno", "área construída") e o valor em metros quadrados. Não
   converta hectares para m² nem tente unificar rótulos diferentes.

5. onus_situacao: use "sem_onus" apenas quando o documento afirma
   claramente que NÃO há ônus (com alguma verificação, como consulta a
   certidão). Use "com_onus" quando qualquer tipo de gravame, penhora,
   alienação, hipoteca ou servidão for mencionado como existente. Use
   "nao_verificavel" quando o documento disser que não foi possível
   verificar, que a informação não consta, ou quando a fonte da
   informação for só uma declaração não confirmada (ex: "segundo o
   proprietário", sem certidão anexada).

6. contradicoes: se o PRÓPRIO documento apresentar informações
   conflitantes sobre o mesmo dado (ex: dois valores diferentes de área,
   ou uma data mencionada de duas formas diferentes que não batem),
   descreva o conflito em texto neste campo E deixe o campo relacionado
   como null, em vez de escolher um dos dois valores por conta própria.

7. Datas: sempre no formato AAAA-MM-DD, mesmo se o texto usar outro
   formato ou escrever a data por extenso.

8. Valores em reais: se o valor vier escrito por extenso junto com o
   número (ex: "seiscentos e oitenta mil reais (R$ 680.000)"), extraia
   apenas o valor numérico.
""".strip()


def _segundos_sugeridos(erro, padrao=30):
    """Lê o 'Please retry in 5.59s' da mensagem de erro do Google."""
    m = re.search(r"retry in ([\d.]+)s", str(erro))
    return int(float(m.group(1))) + 2 if m else padrao


def extrair_laudo(texto_laudo, api_key, tentativas=4, espera_base=10):
    """
    Extrai os campos de UM laudo. Tratamento de erros:

    - 503 (ServerError): temporário. Tenta de novo com backoff exponencial
      (10s, 20s, 40s...). Cuidado: no plano gratuito cada tentativa gasta cota.
    - 429 por cota DIÁRIA: não adianta esperar -> levanta CotaDiariaEsgotada.
    - 429 por limite por MINUTO: espera o tempo que a API sugere e tenta de novo.
    - Outros ClientError (400/404...): erro de configuração, repassa na hora.
    """
    from google import genai
    from google.genai import types, errors

    client = genai.Client(api_key=api_key)

    for tentativa in range(1, tentativas + 1):
        try:
            resposta = client.models.generate_content(
                model=MODELO,
                contents=texto_laudo,
                config=types.GenerateContentConfig(
                    system_instruction=INSTRUCOES_SISTEMA,
                    response_mime_type="application/json",
                    response_schema=LaudoExtraido,
                ),
            )
            return resposta.parsed

        except errors.ServerError:
            if tentativa == tentativas:
                raise
            espera = espera_base * (2 ** (tentativa - 1))
            print(f"  Servidor indisponível (tentativa {tentativa}/{tentativas}). "
                  f"Aguardando {espera}s...")
            time.sleep(espera)

        except errors.ClientError as e:
            if "429" not in str(e) and getattr(e, "code", None) != 429:
                raise
            if "PerDay" in str(e):
                raise CotaDiariaEsgotada(str(e))
            if tentativa == tentativas:
                raise
            espera = _segundos_sugeridos(e)
            print(f"  Limite por minuto atingido. Aguardando {espera}s...")
            time.sleep(espera)


def carregar_resultados_existentes(caminho):
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_resultados_json(dados, caminho_saida):
    os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def processar_todos_os_laudos(laudos, api_key, caminho_saida, pausa_entre=4):
    """
    - Pula laudos que já estão no JSON (não gasta cota à toa).
    - Salva o JSON depois de CADA laudo (nada se perde se cair no meio).
    - Se a cota diária acabar, para e avisa (continuar seria inútil).
    """
    resultados = carregar_resultados_existentes(caminho_saida)
    erros = {}

    pendentes = [n for n in laudos if n not in resultados]
    print(f"{len(resultados)} já extraídos, {len(pendentes)} pendentes.")

    for nome_arquivo in pendentes:
        print(f"Processando {nome_arquivo}...")
        try:
            resultado = extrair_laudo(laudos[nome_arquivo], api_key)
            resultados[nome_arquivo] = resultado.model_dump()
            salvar_resultados_json(resultados, caminho_saida)
            time.sleep(pausa_entre) # evita estourar o limite por minuto

        except CotaDiariaEsgotada:
            print("\n  COTA DIÁRIA ESGOTADA. Parando aqui.")
            print("  Rode o script de novo depois que a cota renovar (meia-noite,")
            print("  horário do Pacífico), ou ative o faturamento / troque o modelo")
            print("  (variável GEMINI_MODEL). Ele retoma de onde parou.")
            break
        except Exception as e:
            print(f"  ERRO em {nome_arquivo}: {type(e).__name__}: {e}")
            erros[nome_arquivo] = str(e)

    faltando = [n for n in laudos if n not in resultados]
    print()
    print(f"Concluído: {len(resultados)}/{len(laudos)} laudos extraídos. "
          f"Faltando: {faltando if faltando else 'nenhum'}")
    return resultados, erros


if __name__ == "__main__":
    laudos = ler_laudos("laudos_avaliacao")
    print(f"{len(laudos)} laudos carregados.")

    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        print("Sem GEMINI_API_KEY definida - pulando a chamada real da API.")
    else:
        processar_todos_os_laudos(
            laudos, chave, "workspace/parte-3-extracao/resultados_extracao.json"
        )