# Diário de Bordo - Parte 4

## a) Registro de uso de IA

**Ferramentas.** Claude (chat, Anthropic) como par de programação: exploração dos dados, código (pandas, plotly, reportlab), revisão e documentação. Gemini (`gemini-3.8-flash`, via API) não como assistente, mas como componente da solução da Parte 3, para extrair campos dos laudos.

**Onde a IA errou ou entregou algo inadequado, e o que foi feito:**

1. **Complexidade demais.** O primeiro gráfico do diagnóstico veio com 134 linhas, dois funis lado a lado e um HTML enorme; eu não conseguia explicar aquele código. Pedi simplificação e chegamos a 27 linhas (`go.Funnel`) e depois a 19 (`px.funnel`). Lição: pedir a versão mais simples primeiro.
2. **Código que só falhou ao rodar.** `SyntaxWarning` por uma regex desnecessária em `"R$"` (trocada por `regex=False`); exportação de PNG do plotly que falhou por falta do Chrome (mantive só o HTML); na Parte 3, dois blocos `if __name__` no mesmo arquivo (o terminal mostrava "17 laudos carregados" duas vezes) e funções definidas depois de serem chamadas (`NameError`). Todos corrigidos depois de rodar e ler a mensagem de erro.
3. **Informação desatualizada sobre a API.** O código usava o modelo `gemini-2.0-flash` e o parâmetro `temperature`. A API respondeu 404 (modelo descontinuado). Li a mensagem, conferi a documentação atual, troquei para `gemini-3.8-flash` e removi `temperature`, que foi descontinuado nos modelos 3.x.
4. **Erro do servidor confundido com bug.** Um 503 ("alta demanda") não era problema do código, e sim instabilidade temporária do Google. Em vez de só rodar de novo, passei a tentar automaticamente (até 3 vezes) apenas nesse tipo de erro.
5. **Prompt que perdeu dado.** Na conferência dos 7 resultados existentes contra o texto original, a "Área do terreno: 4,8 ha" do `laudo_05` não apareceu no JSON: o schema só aceita m² e o prompt proibia converter hectares. A IA não avisou dessa consequência. **Ainda não corrigido** na versão entregue (plano: campo `unidade`).
6. **Ideias minhas que precisaram de teste.** Propus tratar `data_entrada` com `.loc` e máscara booleana, em vez das duas conversões da IA; a primeira versão deu `TypeError` (a coluna de texto não aceita `datetime` misturado) e foi ajustada. Pedi também inspeção com `.unique()` em `canal_origem` antes de corrigir, e uma auditoria de coerência entre colunas, que achou uma data de assinatura anterior à de entrada (`PR-001556`).

## b) O que aprendi do zero

**Variável de ambiente para guardar a chave de API.** Eu achava que `os.environ.get("...")` recebia a chave entre as aspas, e por isso o script dizia que a chave não existia. Na verdade, o texto entre aspas é o *nome* de uma variável que o sistema guarda fora do código; a chave entra antes, no terminal, com `export GEMINI_API_KEY="..."`. A vantagem é que a chave nunca fica escrita no arquivo, então não vai parar no GitHub junto com o código.
Aprendi de forma autodidata e com tutorial simples do próprio site aistudio.google.com
testei com diferentes API's, utilizei diferentes tokens, pois só tinha limite para 20 
requisições com dia.


## c) Autocrítica

**O que sei que está fraco na minha entrega**

- **Parte 3 dependente de API.** O JSON é gerado por API GEMINI 3.8 Flash gratuitamente,
dito isto o servidor pode está inativo, não conseguindo extrair todos os laudos de forma
correta. Além disso temos limite de 20 requisições diárias, com isso nossa margem de erro 
é de apenas 3 tentativas extras, visto que temos 20 laudos para serem extraidos.

**O que eu faria com mais 40 horas**

1. Completar e medir a Parte 3: gabarito à mão dos 17 laudos, acerto por campo, salvar erros e resultados a cada laudo, e rodar duas vezes para medir a consistência.
2. Na Parte 2, capturar qualquer exceção e gravá-la no log, validar tipo e faixa por coluna e escrever testes com `pytest`.
3. Trocar a análise variável por variável por um modelo logístico (score, LTV, canal) e um teste de proporções.

**Perguntas que eu faria ao time de negócios antes de começar**

- "Conversão" é a assinatura do contrato ou o desembolso do crédito?
- A equipe possui alguma área de contato com o cliente, em que quando o lead não retorna
 o banco, ele recebe uma mensagem de feedback, possibilitando uma nova negociação, propostas e etc.
- Existe um motivo detalhado de reprovação de crédito fora deste CSV? E, se o valor do laudo divergir do `valor_imovel` do CSV, qual fonte vale?
- Quando o cliente não retorna na etapa 3, é porque a análise de crédito foi aprovada e
o lead não quis prosseguir com a contratação ?
- É possível ver qual foi a taxa de negociação da taxa de juros ? Com isso pode ser feito 
uma análise para justamente oferecer uma negociação diferente com os leads da etapa 3.