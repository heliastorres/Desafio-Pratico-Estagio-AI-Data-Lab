# Recomendações — Diagnóstico do Funil (Etapa 3: Análise de Crédito)

**Contexto:** a etapa 3 (Análise de crédito) concentra a maior perda do funil,
tanto em quantidade de propostas quanto em dinheiro: 1.799 propostas e
R$ 703 milhões. Dentro dela, os 3 status de desfecho se dividem assim:

| Status | Propostas | Dinheiro solicitado |
|---|---|---|
| Desistiu | 614 | R$ 243.107.565 |
| Reprovada crédito | 608 | R$ 231.342.027 |
| Sem retorno | 577 | R$ 228.596.888 |

---

## Prioridade 1 — "Sem retorno" (577 propostas, R$ 228,6 milhões)

**O que os dados mostram:** o cliente parou de responder durante a etapa de
análise de crédito, sem recusa explícita.

**Suposição assumida (não confirmada pelos dados):** estamos supondo que boa
parte desses clientes ainda tem interesse real e só precisa de um contato
ativo do banco — não existe uma coluna na base que confirme o estágio exato
da conversa com cada cliente.

**Ação recomendada:** campanha ativa de recontato (telefone/WhatsApp/e-mail)
com esse grupo específico, priorizando quem tem score mais alto (maior
chance de aprovação se retomar o processo).

**Impacto estimado:** assumindo uma taxa de reengajamento de 15% (número de
referência de campanhas de recuperação de leads "mornos", não veio da nossa
base — é uma suposição explícita), recuperaríamos cerca de **87 propostas**
e **R$ 34,3 milhões** em crédito potencial.

**Por que é a prioridade 1:** é a ação mais barata e rápida de testar (não
exige mudar política, nem sistema) e o cliente nunca disse "não".

---

## Prioridade 2 — "Desistiu" (614 propostas, R$ 243,1 milhões)

**O que os dados mostram:** o cliente abandonou ativamente o processo
durante a análise de crédito.

**Testamos a hipótese de que a demora do banco causasse a desistência —
não se confirmou:** o tempo médio de análise de quem desistiu (29,1 dias)
é praticamente igual ao de quem foi reprovado (28,7 dias) ou não retornou
(29,7 dias), e até menor que a média geral da base (31,7 dias). Ou seja,
**não há evidência nos dados de que a demora do banco seja a causa.**

**Suposição assumida (não confirmada pelos dados):** mantemos como
hipótese de negócio, não comprovada, que uma parte desses clientes possa
ter desistido por causa da própria complexidade/burocracia do processo,
mesmo sem ele ter demorado mais que o normal em dias corridos. A base não
tem como confirmar isso.

**Ação recomendada:** contato para reabrir negociação, sem a ação
"agilizar a análise" que havia sido cogitada inicialmente — como os dados
não sustentam a causa de demora, essa ação específica não tem evidência
que a justifique. Recomendamos investigar qualitativamente (ex: pesquisa
de satisfação com quem desistiu) antes de investir em mudar o processo.

**Impacto estimado:** assumindo uma taxa de recuperação menor que a do
grupo "Sem retorno" (10%, pois aqui o cliente tomou uma decisão ativa de
sair — suposição nossa, não vem da base), recuperaríamos cerca de
**61 propostas** e **R$ 24,3 milhões**.

**Por que é a prioridade 2:** o potencial de recuperação é menor que o do
grupo 1 (cliente já decidiu sair ativamente), mas a ação ainda é
operacional e barata.

---

## Prioridade 3 — "Reprovada crédito" (608 propostas, R$ 231,3 milhões)

**O que os dados mostram:** reprovação é regra de negócio do banco — em
princípio, não é algo que se "conserta" só com uma campanha de contato.

**Achado que refina a recomendação:** dentro dos 608 reprovados, **168
propostas (27,6%) tinham score de crédito alto (acima de 700) E estavam
dentro do limite de LTV da política (até 60%)** — ou seja, num primeiro
olhar, pareciam propostas de baixo risco. Isso representa R$ 58,2 milhões.

**Ação recomendada:** não propomos flexibilizar a política de crédito de
forma geral (isso é uma decisão estratégica de risco que foge do escopo
desta análise). Propomos, de forma mais restrita: revisar manualmente
essas 168 propostas específicas com a área de risco, para entender se a
reprovação teve um motivo que não aparece nos dados que temos (ex:
restrição cadastral, histórico de outro produto) ou se são casos de
"falso negativo" que valeriam reavaliação.

**Impacto estimado:** não estimamos um número de recuperação aqui, porque
não temos dados suficientes sobre o motivo real da reprovação — qualquer
número seria um chute. O retorno dessa ação é uma investigação, não uma
mudança direta ainda.

**Por que é a prioridade 3:** é a ação de maior risco/complexidade (mexe
com política de crédito) e a que temos menos confiança sobre o impacto
real, por isso fica por último.
