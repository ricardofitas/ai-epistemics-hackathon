# One-Eval: contratos de avaliação que alteram a tarefa e a conclusão

**13 de novembro de 2026. Resultado de investigação exploratória com confirmação prospetiva pequena.**

Esta auditoria encontrou falhas materialmente maiores do que o problema anterior dos aliases: rótulos distintos que passam a representar a mesma opção, atalhos de posição, omissão da resposta correta, perguntas que desaparecem do prompt e pontuações emitidas sem referências válidas. Foram examinados **22.562 exemplos de sete benchmarks**, com controlos positivos e negativos. Um ensaio posterior recolheu **96 respostas de dois modelos**, de que 94 ficaram completas, e confirmou uma inversão entre modelos e um respondedor constante.

A evidência aplica-se ao One-Eval na revisão `8aba20ad17ee2c7d2391162ac03ffaebcbb17506` e, para o gerador, ao `open-dataflow==1.0.10` fixado no respetivo lock. Não é uma avaliação da qualidade dos benchmarks originais nem prova de que resultados anteriormente publicados por terceiros sofreram estas falhas.

## Resultado principal com modelos reais

Foram escolhidas por SHA-256, antes das respostas, 12 perguntas por benchmark em WinoGrande, SciQ e HellaSwag. A seleção foi estratificada por classe em WinoGrande e HellaSwag. No SciQ, as mesmas 12 perguntas foram apresentadas em duas ordens de opções. Isto corresponde a **36 perguntas de origem, 48 condições e dois modelos**, não a 96 perguntas independentes.

Os modelos foram `gemma-4-31b-it` e `qwen3.8-27b`, obtidos pelo serviço Adaption. O catálogo foi conferido antes das chamadas. Cada pedido teve uma tentativa, sem histórico ou ferramentas e com intervalo mínimo de cinco segundos. A captura independente verificou os 96 corpos de pedido, os registos de streaming e o texto terminal. Duas respostas atingiram o limite de 4.096 tokens e permaneceram como incompletas; não foram repetidas nem retiradas dos denominadores.

| WinoGrande, 12 perguntas com referências públicas | Gemma | Qwen | Responder sempre B |
|---|---:|---:|---:|
| Avaliador com o mapeamento original | 50,0% | 50,0% | **100,0%** |
| Referências corrigidas segundo a origem | **91,7–100%** | **100,0%** | 50,0% |

O intervalo de Gemma preserva uma resposta incompleta. Mesmo atribuindo-lhe zero acertos, a preferência entre modelo e constante inverte-se após a correção. São duas comparações de modelos com o mesmo baseline e as mesmas perguntas; não são duas replicações independentes do benchmark.

O motivo é verificável sem modelos: no parser original, os rótulos de origem `"1"` e `"2"` são ambos interpretados como `B`. Nas **1.267 perguntas de validação**, um respondedor que segue perfeitamente os rótulos oficiais recebe **639/1267 = 50,4341%**, enquanto o constante B recebe 100%. O constante B só acerta 639/1267 segundo a origem. A validação é um **diagnóstico com alteração explícita do split**: a galeria escolhe por defeito o teste, cujas 1.767 referências estão vazias.

## Atalho de posição no SciQ

O contrato coloca `correct_answer` na primeira opção nas 1.000 perguntas de teste. Responder A sem ler a pergunta tem 100% de acerto face à posição da resposta na origem. O avaliador original reporta **994/997 = 99,6991%**: exclui três referências numéricas válidas e interpreta outras três como índices de opção.

Na experiência com modelos, os dois modelos e o constante A obtiveram 100% nas 12 perguntas com a ordem original. Depois de uma rotação equilibrada das opções, com as referências alinhadas com a ordem apresentada, **os dois modelos mantiveram 12/12 e o constante A caiu para 3/12**. No controlo de dados com as 1.000 perguntas, a mesma intervenção equilibrada dá 25% aos quatro constantes e mantém o oracle em 100%.

O YAML de referência do lm-evaluation-harness usa uma tarefa de escolha por continuação, com `doc_to_target:3` e sem expor letras de opção no texto da pergunta. A nossa interpretação é que transportar uma ordem fixa para uma tarefa de geração de letras exige uma verificação adicional contra atalhos de posição. Este estudo não equipara a nossa accuracy generativa à métrica oficial por probabilidades `acc_norm`.

O replay do contrato antigo sobre a condição com opções rodadas também produz uma inversão artificial, por manter a referência ligada à ordem anterior. Esse resultado está identificado como diagnóstico no JSON; não é contado como uma utilização predefinida observada.

## Uma pontuação perfeita para respostas erradas no LAB-Bench

Na configuração predefinida CloningScenarios, a lista apresentada contém apenas `distractors`. A resposta `ideal` falta nas **33 perguntas**. O constante A escolhe, portanto, uma resposta incorreta em todas elas.

Apesar disso, a função pública de cálculo devolve **100%**, com **apenas 1 pergunta pontuada e 32 referências excluídas**. Não se trata de 100% sobre 33 referências válidas. A reprodução invoca a função original `run_metrics.run_metrics` e confirma a gravação do ficheiro Step3.

Quando a resposta correta é incluída, a referência é tipada e a ordem é permutada de forma determinística, o oracle mantém 100% sobre as 33 referências; o constante A fica em **6/33 = 18,18%** nesta permutação. O conjunto tem entre quatro e oito opções por pergunta, o que também exige evitar um número fixo de quatro opções no parser.

## O gerador nativo pode perder a pergunta

Uma auditoria separada executou os métodos originais de resolução de prompt, formatação e geração do pacote fixado, substituindo apenas o backend por um respondedor inerte e o armazenamento por um adaptador em memória. Não houve chamadas adicionais a modelos.

| Percurso de geração API, com o código fixado | Exemplos | Texto da pergunta presente | Mudar a pergunta altera o prompt |
|---|---:|---:|---:|
| WinoGrande, teste predefinido | 1.767 | 0 | 0 |
| WinoGrande, validação diagnóstica | 1.267 | 0 | 0 |
| HellaSwag, validação predefinida | 10.042 | 0 | 0 |
| SciQ | 1.000 | 1.000 | 1.000 |
| MedMCQA, controlo | 4.183 | 4.183 | 4.183 |

No SciQ, os **884 contextos de apoio não vazios** não entram no prompt, e substituí-los não altera o texto enviado. O gerador passa campos genéricos `question/context`, enquanto alguns templates pedem campos de origem como `sentence/ctx/support`. A normalização para chavetas duplas é também incompatível com a substituição literal do formatter fixado. Os placeholders ficam por resolver sem um erro que obrigue à correção.

**O ensaio com modelos acima usa o template pretendido, renderizado diretamente a partir dos campos de origem. Testa a camada de pontuação e a ordem das opções. Não mede o desempenho dos modelos sob estes prompts nativos defeituosos.** Esta distinção estava prevista no protocolo do ensaio antes das respostas e permanece explícita nos resultados.

## Outros controlos e limites de cobertura

BoolQ e PubMedQA tratam os valores literais `true/false` e `yes/no/maybe` como nomes de colunas. O pré-processamento não resolve as opções e o gerador fixado regressa antes de chamar o backend. Estes bloqueios não são apresentados como experiências de modelos com pontuação zero.

Os controlos com rótulos iniciados em zero, **MedMCQA, 4.183 perguntas, e HellaSwag, 10.042**, pontuam o oracle em 100% e os constantes segundo a distribuição de referências esperada. No ensaio de modelos em HellaSwag, o avaliador original e o corrigido mantêm a mesma pontuação: 11/12 para Gemma e 11/12 acertos conhecidos mais uma resposta incompleta para Qwen.

O painel foi escolhido após inspeção dos esquemas e das hipóteses de falha. Não estima a percentagem de contratos defeituosos no One-Eval ou noutros sistemas. Das dez combinações origem/split previstas, oito foram recolhidas. A tentativa de PIQA com a configuração `plain_text` falhou na aquisição e não permite uma conclusão sobre o seu contrato; GPQA exigiu autenticação e não foi contornado. Ambos permanecem no registo.

A galeria identifica estes contratos como `reference_mapped`, `smoke_passed=false`, e avisa que não foram verificados com golden cases. A auditoria respeita essa ressalva. A frequência de uso, a exposição em instalações reais, a revisão por terceiros e a novidade científica continuam por estabelecer. As pesquisas dirigidas nas issues/PRs não encontraram uma descrição correspondente, o que não constitui prova de novidade.

## Correção executável e decisão

O módulo `source_contracts.py` propõe referências com semântica explícita por origem, opções completas, valores literais distinguidos de nomes de colunas, referências canónicas sem ambiguidade de texto/índice e vinculação direta dos campos do template. O teste com **28 configurações válidas** preserva as pontuações esperadas, incluindo opções variáveis no LAB-Bench; os dois testes do split sem referências são rejeitados antes de inferência. A correção dos prompts preserva e verifica a dependência da pergunta e do contexto em **20.795 exemplos com referências disponíveis**.

Uma implementação aritmética separada confirmou os resultados principais a partir dos dados brutos. Há também uma reprodução da função pública de métricas e uma auditoria independente dos pedidos e respostas reais. Os métodos foram executados num ambiente isolado, com adaptações de importação documentadas, e não numa instalação completa da aplicação. A reprodução integral adicional em Python3.11 terminou com sucesso, sem novas chamadas a modelos; 18 ficheiros de resultados coincidem com a análise local. As versões e os recibos estão registados nos ficheiros de execução.

**Decisão: promover esta linha a candidato principal para a próxima validação.** Tem consequência grande, mecanismo causal e correção verificável. Ainda não está demonstrado que ultrapassa o GAMMAF em impacto externo. O passo seguinte deve replicar os testes num segundo sistema ou em artefactos de execuções efetivamente usadas, e depois ampliar o ensaio emparelhado com modelos. Aumentar apenas o número de benchmarks não substitui essa demonstração.

## Fontes e proveniência

- [One-Eval, revisão analisada](https://github.com/OpenDCAI/One-Eval/tree/8aba20ad17ee2c7d2391162ac03ffaebcbb17506).
- [WinoGrande, documentação dos autores](https://github.com/allenai/winogrande), incluindo a ausência de referências públicas no teste.
- [SciQ no lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness/blob/d6de81643928d653435c431bae19945d41d32520/lm_eval/tasks/sciq/sciq.yaml).
- As revisões exatas dos dados Hugging Face, ficheiros Parquet, hashes, capturas de modelos e fontes do wheel encontram-se nos recibos das capturas imutáveis. Os commits de protocolo e os identificadores de execução estão em `PERSISTENCE_RECEIPT.json`.
