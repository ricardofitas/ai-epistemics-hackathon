# Auditoria da consequência científica no TabMWP

14 de novembro de 2026. Investigação retrospetiva com respostas públicas fixas. Zero novas chamadas a modelos ou juízes. Manuscrito e ficheiro original de revisão humana sem alterações nesta auditoria.

## Resultado

A inversão entre TAPEX base e UnifiedQA base depende da política de pontuação. Não ficou demonstrada uma inversão robusta da sua capacidade matemática. O teste mais diretamente ligado à conclusão central do artigo deu um resultado negativo para a hipótese de a vantagem do PromptPG ser explicada por este mecanismo: na única execução pública comparável, a vantagem mantém-se mesmo sob os limites mais desfavoráveis dos casos abrangidos.

Isto retira força à utilização deste candidato como argumento para superar a descoberta GAMMAF. É um resultado da investigação, não motivo para escolher outra regra de pontuação até obter a inversão pretendida.

## Ligação a uma conclusão publicada

Fonte: Lu et al., ICLR 2023, [artigo, secção 4.2 e Tabela 3](https://arxiv.org/pdf/2209.14610). Os autores relacionam o desempenho das baselines TAPEX face ao UnifiedQA de dimensão semelhante com o pré-treino tabular. A comparação base é uma parte concreta dessa interpretação. A principal contribuição compara PromptPG com GPT-3 e usa uma média de três execuções. A presente auditoria só tem acesso a uma execução pública comparável dessa comparação principal e não reproduz a média de três execuções.

## 1. Comparação de baselines, mesmas 7.686 perguntas

| Política, respostas mantidas fixas | TAPEX base | UnifiedQA base | Diferença de respostas corretas |
|---|---:|---:|---:|
| Original publicado | 15.73% | 14.56% | +90.00 |
| Reconhecimento de opções explícitas | 15.66% | 14.56% | +85.00 |
| Opções explícitas + zero nos restantes empates | 11.11% | 14.23% | -240.00 |
| Opções explícitas + crédito esperado do desempate uniforme | 15.73% | 14.56% | +90.33 |
| Opções explícitas + desempate lexicográfico | 15.60% | 14.56% | +80.00 |

As regras uniforme e lexicográfica tratam os casos sem correspondência como desempates. São análises de sensibilidade da política, não pontuações humanas corretas. Apenas o tratamento dos empates residuais de similaridade zero varia; os outros resultados ficam fixos.

Nas 256 ordens comuns de desempate, fixadas por hash antes desta análise, TAPEX base ficou à frente em **256/256**. A margem variou de **45 a 140** respostas. Estas são perturbações do avaliador sobre respostas guardadas, não 256 novos ensaios dos modelos.

Mantendo os outros julgamentos históricos fixos e tratando as respostas residuais como desconhecidas, a diferença TAPEX menos UnifiedQA pode variar de **-320 a 730** respostas. Respostas normalizadas idênticas à mesma pergunta recebem uma incógnita partilhada. A ordem continua por identificar nesse âmbito.

A partir da política residual-zero, basta uma diferença líquida de **240** interpretações corretas adicionais para empatar e **241** para o TAPEX voltar à frente. Este número explicita o problema que uma validação semântica teria de resolver; não transforma a amostra de 64 casos numa avaliação completa.

## 2. Comparação PromptPG/GPT-3 que estava por testar

Foram autenticados os ficheiros públicos da execução seed 2 e as funções originais de extração. Em 7.686 perguntas, as pontuações guardadas são **70.22%** para PromptPG e **63.52%** para few-shot-CoT GPT-3, uma diferença de **515** respostas (**6.70 pontos percentuais**).

Identificaram-se 14 respostas residuais sem correspondência no PromptPG e 402 no comparador. Mesmo permitindo que todas essas incógnitas favoreçam o comparador tanto quanto possível, a vantagem fica entre **295 e 709** respostas: limite inferior **3.84 pontos percentuais**. Todas as 256 perturbações comuns preservam a vantagem do PromptPG.

Numa extensão exploratória ainda mais conservadora, incluem-se também as respostas com letra de opção fora do intervalo, para as quais o extrator usa uma escolha aleatória. O intervalo continua positivo: **247 a 764** respostas, limite inferior **3.21 pontos percentuais**.

Estes limites só variam os casos deste mecanismo. Não certificam a correção semântica de todas as respostas, nem a média publicada de três execuções. Contudo, mostram que corrigir apenas estes casos não consegue inverter esta execução pública da comparação central.

## 3. O contexto das tabelas altera a interpretação

Uma extensão exploratória associou uma resposta numérica ao nome de uma opção quando esse valor ocorre uma única vez nas linhas correspondentes de uma tabela com duas colunas. Outra regra só aceitaria inferir sim/não a partir de um montante se este fosse exatamente a soma dos dois produtos pedidos; não se infere sim só por um número ser inferior ao orçamento.

No TAPEX base, a regra da correspondência entre valor e linha permitiu interpretar **291** respostas residuais, das quais **88** correspondem à opção de referência. As 203 restantes apontam para uma opção diferente. Não surgiram recuperações no UnifiedQA base. Os montantes das perguntas de compras não produziram recuperações sob a regra restrita da soma.

Se estas interpretações forem aceites e os outros resíduos receberem zero, a diferença passa de **-240 para -152** respostas. A inversão mantém-se nessa política, mas ainda restam respostas por interpretar. As 291 decisões são interpretações mecânicas com contexto, não classificações humanas. Os cinco controlos do descodificador e as 291 associações foram verificados; o resultado primário sem contexto continua preservado.

## 4. Verificação e limites

- 23 ficheiros autenticados pelo Git blob SHA, incluindo dados, respostas e código original.
- 107.604 flags de pontuação reconciliadas nos 14 ficheiros elegíveis para a análise; 19.920 escolhas das baselines também reproduzidas por uma implementação independente da similaridade.
- 110 casos de letra fora do intervalo tratados como conjuntos de saídas possíveis do fallback aleatório, sem inventar o estado histórico do gerador aleatório.
- Um ficheiro separado de zero-shot-CoT tem seis discrepâncias entre a extração atual e a previsão guardada, cinco com efeito na flag. Foi excluído da atribuição de efeitos àquele extrator, mantendo-se o ficheiro e os casos testemunha. Não é um resultado contra a comparação principal. O nome contém seed_2, mas os metadados dizem seed 1.
- 327 verificações aritméticas, de identidade e de testemunhos concluídas. Verificador separado escrito pelo mesmo assistente; não é revisão humana independente.
- Zero classificações humanas fabricadas. A revisão dos 64 casos continua distinta desta análise e não estima, por si só, a pontuação humana de todo o teste.

## Próxima decisão científica

A hipótese de este mecanismo eliminar a vantagem central do PromptPG fica fechada com resultado negativo para a execução disponível. Repetir as mesmas chamadas ou acrescentar regras semelhantes não responde a uma nova pergunta.

Para a comparação entre baselines, o próximo trabalho pertinente é avaliar as interpretações com contexto e quantificar os resíduos que poderiam alterar a margem. A hipótese e o critério de correção devem ficar explícitos antes de extrapolar resultados de leitores para o conjunto inteiro. Para sustentar uma consequência mais forte, será preciso outro efeito relevante identificado em resultados reais; não basta aumentar a contagem de benchmarks ou integrar este resultado no manuscrito.

Dados completos da análise: [results.json](results/results.json), [sensibilidade com contexto](results/context-sensitivity.json), [testemunhos com tabelas, JSON comprimido](results/context-witnesses.json.gz), [verificação](results/verification.json).
