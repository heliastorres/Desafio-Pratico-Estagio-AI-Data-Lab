# Desafio Bari — Diagnóstico do Funil de Crédito

Solução das 4 partes do desafio prático. Todos os dados são sintéticos, fornecidos pelo Bari.
O CSV bruto nunca é alterado: todo tratamento gera um arquivo novo.

## Status da entrega

| Parte | O que é | Status |
|---|---|---|
| 1 | Diagnóstico do funil + registro de tratamento de dados | Concluída (ver "Limitações conhecidas") |
| 2 | Rotina automática do relatório semanal (PDF) | Concluída (ver "Limitações conhecidas") |
| 3 | Extração de campos dos 17 laudos com IA (Gemini) | **Parcial**: o `resultados_extracao. |
| 4 | Diário de bordo | `DIARIO.md` |
| - | Resumo executivo de 1 página |

## O que tem em cada arquivo

```
case_bari/
├── README.md
├── DIARIO.md
└── workspace/
    ├── propostas_credito.csv            base bruta (não é alterada)
    ├── propostas_credito_tratado.csv    saída do tratamento
    ├── REGISTRO_TRATAMENTO.md           o que estava errado na base, o que foi feito e por quê
    ├── analise_csv.py                   Parte 1: tratamento do CSV, comentado passo a passo
    ├── parte-1-funil/
    │   ├── p1/   soma_etapa.py, funil_simples.py, funil_propostas.html, nota.txt   (pergunta 1)
    │   ├── p2/   conversao_canal.py, conversao_correspondente_tempo.py             (pergunta 2)
    │   ├── p3/   conversao_score.py, conversao_ltv.py                              (pergunta 3)
    │   └── p4/   recomendacoes.md                                                  (pergunta 4)
    ├── parte-2-rpa/
    │   ├── rpa_relatorio_semanal.py     rotina: ler -> validar -> tratar -> métricas -> PDF
    │   └── relatorio/                   relatorio_semanal_funil.pdf e relatorio_semanal.log
    ├── laudos_avaliacao/                os 17 laudos .txt (entrada da Parte 3)
    └── parte-3-extracao/
        ├── extrair_laudos_gemini.py     extração com a API do Gemini
        └── resultados_extracao.json     resultado da extração
```

## Como rodar

Testado com Python 3.9 no macOS. Todos os comandos partem da pasta `case_bari/`, porque os caminhos dos scripts são relativos a ela.

```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas plotly reportlab pydantic google-genai
```

(Em Python 3.9 aparecem `FutureWarning` do `google-auth`; são avisos, não erros.)

### Parte 1

```bash
python3 workspace/analise_csv.py # gera propostas_credito_tratado.csv
python3 workspace/parte-1-funil/p1/soma_etapa.py # R$ que fica em cada etapa
python3 workspace/parte-1-funil/p1/funil_simples.py # funil em HTML (plotly)
python3 workspace/parte-1-funil/p2/conversao_canal.py
python3 workspace/parte-1-funil/p2/conversao_correspondente_tempo.py
python3 workspace/parte-1-funil/p3/conversao_score.py
python3 workspace/parte-1-funil/p3/conversao_ltv.py
```

Conclusões (detalhes em `p1/nota.txt` e `p4/recomendacoes.md`):

- **Pergunta 1:** a etapa 3 (Análise de crédito) é onde mais se perde, em propostas (1.799) e em dinheiro (R$ 703,0 milhões). Os dois rankings coincidem porque o ticket médio de quem se perde é parecido em todas as etapas (~R$ 385 mil).
- **Pergunta 2:** o canal Correspondente converte 14,3%, contra 20,7% a 22,3% dos outros quatro canais. Na série mensal, ele fica abaixo dos demais em 21 dos 24 meses (as exceções são jan/24, fev/24 e out/25): parece um problema antigo, não uma piora recente.
- **Pergunta 3:** score e LTV são os sinais mais fortes. Score baixo (até 600) converte 9,8% e muito alto (800+) 37,3%. LTV acima de 60% (limite da política) converte 13,5%, e acima de 70%, 7,3%.
- **Pergunta 4:** três recomendações sobre os desfechos da etapa 3 (Sem retorno, Desistiu, Reprovada crédito), com impacto estimado e suposições explícitas, em `p4/recomendacoes.md`.

### Parte 2

```bash
python3 workspace/parte-2-rpa/rpa_relatorio_semanal.py
```

Lê `workspace/propostas_credito.csv`, aplica o mesmo tratamento da Parte 1, calcula as métricas (resumo geral, funil por etapa, conversão por canal) e gera `relatorio/relatorio_semanal_funil.pdf` e `relatorio/relatorio_semanal.log`.

O que acontece quando o arquivo de entrada muda:

| Situação | O que a rotina faz |
|---|---|
| Arquivo não existe, está vazio ou só tem cabeçalho | Grava `[ERROR]` no log e para |
| Falta uma coluna esperada | Grava `[ERROR]` nomeando a coluna e para (melhor parar do que gerar relatório errado) |
| Aparece uma coluna nova | Grava `[WARNING]`, ignora a coluna e segue |
| Problemas de dados já conhecidos (prefixo "R$", data DD/MM/AAAA, canal com espaço etc.) | Corrige, e o número de linhas corrigidas vai para o log e para o PDF |
| Formato novo que a rotina não conhece (ex.: data `2025/04/11`) | **Para com erro no terminal e não grava nada no log** (testado; ponto a melhorar) |

### Como alguém que não sou eu rodaria isso toda segunda-feira

1. Colocar o CSV da semana em `workspace/propostas_credito.csv` (mesmo nome, substituindo o anterior).
2. Rodar `venv/bin/python workspace/parte-2-rpa/rpa_relatorio_semanal.py` a partir da pasta `case_bari/`.
3. Conferir se `relatorio/relatorio_semanal_funil.pdf` tem a data de hoje. Se tiver, deu certo; é só enviar.
4. Se não tiver, abrir `relatorio/relatorio_semanal.log` e ler a última linha `[ERROR]`, que está em português (ex.: "Arquivo não encontrado", "faltam colunas: [...]"). Se não houver `[ERROR]` novo, o erro apareceu no terminal (ver tabela acima): encaminhar a mensagem para quem mantém a rotina.

Para não depender de ninguém lembrar, dá para agendar com `cron` (Mac/Linux). Em `crontab -e`:

```
0 8 * * 1 cd /caminho/para/case_bari && venv/bin/python workspace/parte-2-rpa/rpa_relatorio_semanal.py
```

- `0 8 * * 1` = toda segunda-feira às 8h.
- Usar o `python` de dentro do `venv/` é importante: o `cron` não ativa o ambiente virtual, e o `python3` do sistema não tem o pandas.
- No macOS, se o `cron` não conseguir ler a pasta (por exemplo dentro de `Documents`), pode ser necessário dar "Acesso total ao disco" ao `cron` ou mover o projeto para outra pasta.
- No Windows: Agendador de Tarefas, gatilho semanal às segundas, ação "iniciar programa" apontando para o Python do `venv`.

### Parte 3

Requer uma chave da API do Gemini:

```bash
export GEMINI_API_KEY="sua-chave"
python3 workspace/parte-3-extracao/extrair_laudos_gemini.py
```

Os laudos são lidos de `workspace/laudos_avaliacao/` e o resultado é salvo em `workspace/parte-3-extracao/resultados_extracao.json`. Sem a variável definida, o script só carrega os laudos e avisa que pulou a chamada.

Como funciona e como responde ao que o case pede:

- **Mesmo formato sempre:** o Gemini é chamado com `response_schema` (uma classe Pydantic, `LaudoExtraido`), que o obriga a devolver um JSON com os mesmos campos em todos os laudos.
- **Campo que não existe no documento:** vira `null` (ou lista vazia). O prompt proíbe estimar ou completar. Exemplo: se o laudo só diz "idade aparente: 11 anos", o `ano_construcao` fica `null` e o número vai para `idade_aproximada_anos`, sem calcular o ano.
- **Ônus com 3 estados**, não 2: `sem_onus`, `com_onus` e `nao_verificavel`. "Não foi possível verificar" não é a mesma coisa que "sem ônus".
- **Áreas:** lista de pares rótulo + valor, mantendo o nome que cada laudo usa ("área privativa", "área do terreno" etc.), sem forçar todos numa mesma coluna.
- **Erros de API:** erro temporário do servidor (503) é tentado de novo até 3 vezes; e um laudo que falha não interrompe os demais.
- **Como medir se está certo:** ainda não há um gabarito com taxa de acerto. Até agora, os 17 resultados existentes foram conferidos à mão contra o texto original.

## Tempo levado

Preencher com o tempo real de cada parte:

| Parte | Tempo |
|---|---|
| 1. Diagnóstico e tratamento de dados | 20h |
| 2. Automação / relatório semanal | 12h |
| 3. Extração com IA | 10h |
| 4. Diário e documentação | 6h |

## Limitações conhecidas

- **Parte 3 frágil:** o `resultados_extracao.json` aprensenta a extração dos 17 laudos 
em Json, porém essa extração é feita por uma API do GEMINI 3.8 Flash, por isso pode ter
inconstâncias com o servidor, pois nem sempre podem estar ativos, além de terem um
limite de 20 requisições por dia.
- **Limitação técnica:** as etapas do case foram feitas de forma que os códigos apresentem
a resposta solicitada por cada pergunta de forma intuitiva, porém pode ter passado detalhes, 
regra de negócios específicas não explicitadas.
- **Comunicação com equipe:** todas as decisões foras feitas conforme achei que seria melhor 
para o projeto, conversei com pessoas mais experientes a respeito das regras de negócio do projeto, mas mesmo assim sei que na realidade é um pouco diferente, pois cada banco tem suas peculiaridades, dinâmicas diferentes, apenas quem trabalha no meio bancário do Bari vai saber as melhores escolhas para cada situação.