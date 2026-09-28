# Registro de Tratamento de Dados

Este documento responde ao pedido do case: **o que encontrei de errado na
base, o que fiz com cada problema, e por quê**. Toda decisão de limpeza
aqui é também uma decisão de negócio — nenhuma linha foi descartada sem
justificativa.

## Resumo

| Coluna afetada | Linhas tratadas | Tipo de problema |
|---|---|---|
| `valor_imovel` | 3 | Formato (texto com prefixo "R$") |
| `ltv` | 6.400 (coluna inteira) | Coluna ausente no arquivo, criada |
| `idade_cliente` | 1 | Valor implausível |
| `etapa_max_funil` | 1 | Valor fora do intervalo válido |
| `data_entrada` | 3 | Formato de data inconsistente |
| `canal_origem` | 4 | Inconsistência de texto (espaço/maiúscula) |
| `taxa_juros_aa` -> `taxa_juros_am` | 6.400 (nome da coluna) | Nome da coluna incoerente com o dicionário |
| `data_assinatura_contrato` | 1 | Impossibilidade lógica entre datas |

---

## 1. `valor_imovel` — formato de texto

**Encontrado:** 3 linhas vinham como `"R$ 574857.06"` em vez de `"574857.06"`.
Isso obrigava o pandas a tratar a coluna inteira como texto, mesmo as outras
6.397 linhas sendo números "limpos".

**O que fiz:** removi o prefixo `"R$"` e os espaços, e converti a
coluna inteira para número (float).

**Por quê:** não é uma invenção de valor — é só remover um texto que não
deveria estar ali. Sem essa correção, nenhuma conta (LTV, somas, médias)
funcionaria nessa coluna.

---

## 2. `ltv` — coluna ausente

**Encontrado:** o dicionário de dados descreve uma coluna `ltv`, mas ela não
existe no arquivo real.

**O que fiz:** calculei a coluna do zero, com a própria definição do
dicionário: `ltv = valor_solicitado / valor_imovel`.

**Por quê:** em vez de assumir que era um erro sem solução, usei os dados
que já tinha (valor solicitado e valor do imóvel, ambos presentes) para
reconstruir a informação que faltava.

**Exemplo do resultado:**

| id_proposta | valor_solicitado | valor_imovel | ltv |
|---|---|---|---|
| PR-000001 | 313.370,07 | 461.158,85 | 0,6795 |
| PR-000002 | 1.016.814,02 | 2.264.057,22 | 0,4491 |
| PR-000003 | 296.412,10 | 646.299,62 | 0,4586 |

---

## 3. `idade_cliente` — valor implausível

**Encontrado:** 1 linha (proposta `PR-000079`) com idade de cliente = 14
anos — incompatível com alguém assinando um contrato de crédito imobiliário.

**O que fiz:** troquei o valor por ausente (NaN/NA).

**Por quê:** não tive como saber qual seria a idade real dessa pessoa.
Chutar um valor "plausível" distorceria qualquer análise futura por faixa
etária, e descartar a linha inteira jogaria fora informações válidas de
outras colunas dessa mesma proposta. Assumir "não sabemos" é mais honesto do
que inventar.

---

## 4. `etapa_max_funil` — valor fora do intervalo válido

**Encontrado:** 1 linha (proposta `PR-000081`) com `etapa_max_funil = 7`,
fora do intervalo válido (1 a 6) descrito no dicionário.

**O que fiz:** corrigi o valor para 6.

**Por quê:** diferente do caso da idade, aqui existe uma forma segura de
saber o valor certo: toda proposta com `status_final = "Contratada"` sempre
tem `etapa_max_funil = 6` no resto da base (mais de 1.200 casos confirmam
esse padrão). Como essa linha também é "Contratada", o valor 7 só pode ser
erro de digitação de "6". Não é chute — é uma correção apoiada numa regra
que se repete consistentemente no restante dos dados.

---

## 5. `data_entrada` — formato de data inconsistente

**Encontrado:** 3 linhas vieram no formato `DD/MM/AAAA` (ex: `11/04/2025`),
enquanto o restante da base usa `AAAA-MM-DD` (ex: `2025-04-11`).

**O que fiz:** identifiquei essas 3 linhas (procurando por `"/"` no
texto) e converti para o mesmo padrão `AAAA-MM-DD` do resto da base,
antes de transformar a coluna inteira em datetime.

**Por quê:** datas em formatos diferentes numa mesma coluna quebram qualquer
ordenação, comparação ou cálculo de intervalo de tempo (ex: agrupar por mês,
como fiz no diagnóstico do funil).

---

## 6. `canal_origem` — inconsistência de texto

**Encontrado:** 4 linhas com grafia fora do padrão: `"mídia paga "` (2x),
`"indicação "` (1x) e `"organico "` (1x) — todas com espaço sobrando no
final e letra minúscula, diferente da grafia predominante na base.

Valores únicos **antes** do tratamento:
`['Correspondente', 'Indicação', 'Mídia paga', 'Organico', 'Parceria', 'indicação ', 'mídia paga ', 'organico ']`

Valores únicos **depois** do tratamento:
`['Correspondente', 'Indicação', 'Mídia paga', 'Organico', 'Parceria']`

**O que fiz:** primeiro removi os espaços nas pontas; depois
agrupei os valores por uma versão normalizada (tudo minúsculo) e
corrigi cada linha para a grafia mais frequente dentro do seu grupo (ex:
`"mídia paga"` com 1.270 ocorrências venceu `"mídia paga "` com só 2).

**Por quê:** antes de aplicar qualquer correção, conferi com `.unique()`
que essas eram as únicas 8 grafias existentes na coluna inteira — garantindo
que não ficou nenhuma outra inconsistência escondida. A correção automática
(pela grafia mais comum) evita escrever um mapa de correção manual, que
seria mais sujeito a erro e menos fácil de auditar depois.

---

## 7. `taxa_juros_aa` -> `taxa_juros_am` — nome da coluna incoerente

**Encontrado:** o nome da coluna sugere "ao ano" (`_aa`), mas o dicionário de
dados descreve a coluna como **"Taxa contratada (% a.m.)"** — ao mês. Os
valores confirmam o dicionário: variam de 0,94% a 1,73%, com média de 1,32%
— compatível com juros **mensais** de crédito com garantia de imóvel no
Brasil (que giram em torno de 1% a 1,5% ao mês). Se fosse realmente ao ano,
seria uma taxa impossivelmente barata para qualquer tipo de crédito.

**O que fiz:** renomeei a coluna para `taxa_juros_am`.

**Por quê:** entre o nome da coluna e a descrição do dicionário + a faixa
real dos valores, só o nome da coluna estava incoerente. Corrigi o que
estava provadamente errado, sem alterar nenhum valor.

---

## 8. `data_assinatura_contrato` — impossibilidade lógica entre datas

**Encontrado:** 1 linha (proposta `PR-001556`) com data de assinatura de
contrato **anterior** à data de entrada da proposta — fisicamente
impossível (não dá pra assinar um contrato antes de pedir o crédito).

**O que fiz:** testei se os campos poderiam estar trocados, ou se
`tempo_analise_dias` bateria com alguma combinação das datas — nenhuma
combinação fez sentido. Marquei `data_assinatura_contrato` como ausente
(NaT) só nessa linha, mantendo os demais campos como estão.

**Por quê:** mesmo princípio usado na idade do cliente: não há como saber
com segurança qual campo está errado, então não chutei uma data. Fixei
apenas o campo que causa a impossibilidade lógica.

---

## Resultado final

Arquivo tratado salvo como `propostas_credito_tratado.csv`, com **6.400
linhas** (nenhuma linha foi descartada) e **20 colunas** (as 19 originais,
menos `taxa_juros_aa` renomeada, mais a coluna `ltv` calculada).