# Validação externa da hackathon de AI Epistemics

## Três experiências com a Adaption

| Experiência | Perguntas ou casos | Pedidos distintos | Respostas completas | Custo comunicado pela API |
|---|---:|---:|---:|---:|
| Quatro modelos × quatro condições, SQuAD e TabMWP | 200 | 3 200 | 3 086 | 2,8084 |
| Leitura cega de respostas históricas, incluindo 12 controlos | 112 | 224 | 223 | 0,1477 |
| Opção numérica correta ou falsa nos mesmos problemas | 24 | 192 | 178 | 0,4574 |
| **Total** | | **3 616** | **3 487** | **3,4135** |

Recalculámos as pontuações a partir dos registos individuais e obtivemos o mesmo resultado que a execução principal. Os valores da última coluna somam o campo de custo dos pedidos com utilização comunicada. A faturação e o saldo da conta não foram consultados.

## O formato altera a pontuação e a escolha possível do modelo

Fixámos 100 perguntas de compreensão de texto do SQuAD e 100 problemas numéricos do TabMWP, com as respetivas respostas de referência. Gemma-4-31B-IT, Qwen3.8-27B, DeepSeek-V4-Flash e GLM-5.2 responderam em quatro condições. Mantendo a instrução de escolha múltipla, acrescentar a única opção «A. None» reduziu a exatidão média em **50–63 pontos percentuais no SQuAD** e **67,5–79,25 no TabMWP**. Estes limites atribuem às respostas desconhecidas tanto o melhor como o pior resultado possível dentro das 200 perguntas. A análise por artigo no SQuAD e por pergunta no TabMWP avalia separadamente a variação associada à amostra. O SQuAD continua a mostrar uma queda de 61,83–74,83 pontos quando as respostas recebem crédito parcial por palavras corretas.

Com resposta livre e sem a opção fictícia, apenas o GLM pôde ficar em primeiro no SQuAD. Na condição de escolha múltipla com «A. None», Qwen, DeepSeek e GLM ficaram compatíveis com o primeiro lugar. Na avaliação numérica limpa, escolher DeepSeek deixaria 18–20 pontos por ganhar face ao melhor dos quatro modelos. Para Qwen, a diferença seria de 4–6 pontos, e para GLM, 0–2. Os dois conjuntos de possíveis vencedores incluem GLM.

## Um controlo separa o formato da resposta e a aceitação de uma opção falsa

Com a única opção numérica correta, os quatro modelos selecionaram a solução em 96/96 respostas sobre 24 problemas. A métrica de número isolado definida antes do ensaio aceitou 1/96. A leitura posterior dos registos encontrou 34 respostas «A», 61 com «A» seguido do número correto e uma com o número isolado. Quando a opção continha um número errado, os modelos escolheram-na em pelo menos 45/96 pedidos. Outros 30 deram o número correto, sete responderam com uma explicação e 14 ficaram incompletos. A solução foi mostrada no primeiro controlo. O que este teste mede é a capacidade do avaliador de reconhecer uma opção correta.

## Um efeito mensurável em resultados já publicados

Reproduzimos dez linhas da Tabela 3 de Lu et al. (ICLR 2023) sobre 7 686 perguntas, incluindo os 76 860 resultados individuais. Reconhecer uma opção indicada inequivocamente apesar das diferenças de maiúsculas ou espaços alterou 557 pontuações em 432 perguntas distintas. A hierarquia dos dez modelos manteve-se com esta correção. Quando o avaliador passou também a atribuir zero aos empates que continuavam sem correspondência, duas comparações inverteram a ordem publicada. O TAPEX base passou de 15,73% para 11,11%, ficando abaixo dos UnifiedQA small (12,01%) e base (14,23%). A auditoria abrange as baselines TAPEX e UnifiedQA da tabela. A conclusão principal do artigo sobre PromptPG e GPT-3 requer outra análise.

Na leitura cega, de 50 respostas antes consideradas corretas por desempate, dois modelos concordaram que 40 não indicavam uma opção, sete indicavam uma opção errada e duas a opção certa. Uma resposta ficou sem classificação conjunta. Ambos os modelos passaram os 12 controlos. Está preparado um conjunto sem rótulos para dois leitores humanos avaliarem 40 respostas independentemente.

[Resultados por modelo e intervalos](results/REPORT.md) · [Registos de proveniência](results/provenance.json) · [Controlo numérico e respetivos dados](../tabmwp-numeric-controls-20261114/RESULTS.md) · [Auditoria histórica e testes de sensibilidade](../tabmwp-archive-audit-20261114/FINDING.md) · [Leitura cega e material para revisão humana](../tabmwp-blind-reading-20261114/RESULTS.md).
