# Consequência causal confirmada em WinoGrande

14 de novembro de 2026. Reanálise das respostas já recolhidas: zero novas chamadas a modelos ou juízes. Manuscrito e folha humana sem alterações.

## Conclusão principal

Na configuração WinoGrande do One-Eval congelado em `8aba20ad17ee2c7d2391162ac03ffaebcbb17506`, corrigir apenas a codificação da resposta de referência inverte a comparação entre modelos quase perfeitos num painel e uma estratégia que responde sempre B. As perguntas, opções, respostas guardadas, parser e contrato de pontuação mantêm-se fixos. O resultado anterior não refletia o desempenho dessas respostas perante as referências da fonte.

Esta é uma consequência inequívoca na etapa de pontuação de um benchmark. Vai além de assinalar um pedido defeituoso. Parte do padrão já estava nos resultados anteriores; esta etapa isolou a intervenção na referência, sem mudar simultaneamente o parser.

## Comparação com saídas fixas

Mesmas 12 perguntas de validação, equilibradas entre A e B, mesmas 24 respostas arquivadas de dois modelos:

| Sistema | Pontuação original | Corrigindo só a referência |
|---|---:|---:|
| Gemma-4-31B-IT | 50% | 91,67%; uma resposta incompleta mantém o intervalo semântico em 91,67–100% |
| Qwen3.8-27B | 50% | 100% |
| Sempre B | 100% | 50% |

A conclusão «a constante é superior aos modelos» passa a «os modelos são superiores à constante». A inversão mantém-se mesmo contando a resposta incompleta do Gemma como errada.

O parser original interpreta as duas referências numéricas da fonte, `1` e `2`, como B. A correção transporta explicitamente a codificação com índices a partir de 1 da fonte para a letra correspondente, sem trocar a ordem das opções ou as previsões. Duas intervenções concordam:

1. Selecionar uma coluna de referência canónica adicional, mantendo as linhas e saídas idênticas.
2. Manter a chave de referência original e corrigir apenas o valor do campo `answer`.

O contrato completo e o parser configurado têm hashes iguais antes e depois. O parser configurado é `a3420f98f12da3da15239b03ec43b4dbbaa013d198a59be5f85cd09d6a16afb6`.

## Confirmação no conjunto de validação completo

Os 1.267 exemplos originais foram também avaliados com controlos construídos explicitamente, sem inferência de modelos:

| Controlo | Original | Referência corrigida |
|---|---:|---:|
| Resposta sempre igual à referência correta da fonte | 639/1267 = 50,4341% | 100% |
| Sempre B | 100% | 639/1267 = 50,4341% |

Estes controlos mostram o mecanismo no conjunto completo. Não são 1.267 novas respostas de LLM. Em HellaSwag, a mesma verificação mantém os resultados das 24 saídas arquivadas: 11/12 em cada modelo.

## Verificação independente

- O agente de revisão executou as classes originais MetricRunner, parser e BenchInfo através de imports normais e autenticou as fontes e os arquivos.
- O agente principal recalculou separadamente as referências diretamente de `answer`, as associações pergunta/pedido/resposta e os hashes das 24 saídas; confirmou 12 corretas no Qwen, 11 corretas e uma desconhecida no Gemma.
- A verificação cruzada final passou 39 condições sobre a intervenção mínima, as inversões, os denominadores, o controlo saudável e os limites das restantes análises.
- O parser e as métricas não foram substituídos por classificações humanas ou por um juiz LLM. Não há classificações humanas fabricadas.

## Limites da afirmação

A configuração seleciona explicitamente a validação, porque o teste predefinido não disponibiliza referências públicas. Os prompts das respostas arquivadas foram renderizados diretamente a partir da fonte; esta prova diz respeito a pontuar essas saídas, não à execução completa do gerador nativo One-Eval. Só o pré-processamento foi isolado por AST para evitar dependências de fornecedores; a métrica e o parser originais foram importados normalmente.

A galeria está assinalada `reference_mapped` e `smoke_passed=false`. A consequência foi reproduzida nesta configuração diagnóstica com fonte rotulada; não demonstra que um ranking publicado por terceiros foi afetado. Os 12 exemplos/modelo não estimam a precisão populacional dos modelos. O erro pertence à integração/configuração de avaliação examinada, não ao conjunto WinoGrande original. Novidade geral e superioridade ao GAMMAF não decorrem automaticamente desta prova.

## Outros dados existentes verificados em paralelo

| Via | Resultado efetivamente estabelecido | Âmbito |
|---|---|---|
| SQuAD | Scorer público oficial confirma os resultados de 1.539 saídas completas, com 61 desconhecidas. Inserir a única opção A.None sob instrução de escolha provoca respostas finais erradas, mesmo mantendo o texto-fonte e a pergunta. | Experiência controlada deliberada; não é uma falha natural do scorer SQuAD nem uma execução nativa completa do One-Eval. |
| ARC-Challenge / OpenBookQA | Nas 200 perguntas testadas, o avaliador dá 88 créditos a respostas C/D que os pedidos não ofereciam. Reparar a apresentação elimina essa contradição; o número agregado de pontos pode manter-se. MMLU saudável é preservado. | Gerador e métrica originais importados normalmente, pré-processamento arquivado; respostas de controlo construídas. Não é precisão de novos modelos. |
| CUPCase, trabalho paralelo existente | Verificação independente de artefactos completos de run_eval: a saída constante A obtém 3562/3562 sem receber nenhum caso clínico; uma reparação que preserva a fonte dá 905/3562. Todas as flags corrigidas de A coincidem com a verdade da fonte. | Fronteira de dependências carregada das fontes; o número selecionado pelo relatório é diagnóstico. A reparação B ainda tem seis créditos falsos, explicitamente conservados. Não há resultado clínico de um LLM ou ranking histórico validado. |

O resultado negativo anterior sobre a comparação PromptPG/GPT-3 permanece conservado. Não é contrariado pela consequência WinoGrande, que examina outro mecanismo e outro percurso de pontuação.

## Evidência e reprodução

- [Replay WinoGrande e instruções](review/README.md)
- [Resultados nativos completos](review/proof/RESULT.json)
- [Verificação independente das saídas](ROOT_FIXED_OUTPUT_VERIFICATION.json)
- [Verificação cruzada final](ROOT_CLOSURE_VERIFICATION.json)
- [Análise SQuAD](squad/REPORT.md)
- [Análise ARC/OpenBookQA](arc_openbook/REPORT.md)
- [Recontagem independente CUPCase](natural_review/REVIEW.md)

Os scripts e os identificadores/digests dos arquivos originais estão preservados. Os dados grandes permanecem nos arquivos de origem autenticados; não é preciso repetir a geração dos modelos.
