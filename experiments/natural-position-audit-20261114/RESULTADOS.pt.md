# Falha natural de validade da avaliação no One-Eval

14 de novembro de 2026. Investigação privada; sem alterações ao manuscrito.

**Um programa que devolve sempre `<answer>A</answer>` recebe entre 96,49% e 100% no seletor de pontuação do relatório do percurso API publicado do One-Eval, sobre 5 010 perguntas oficiais.** A configuração coloca o campo da resposta correta primeiro em todos os casos. No CUPCase e no GPQA, os textos produzidos pelo gerador nem incluem o próprio enunciado. Não foram acrescentadas opções ou perguntas artificiais.

O resultado foi executado sobre o método completo original `DataFlowEvalTool.run_eval`, com `FileStorage`, `BenchAnswerGenerator`, `UnifiedBenchDatasetEvaluator`, o parser e a métrica originais, e a função original que escolhe a pontuação do relatório. A fronteira de inferência contém apenas o programa constante, instalado na cache de serving original. As classes são carregadas do código verificado, com dependências de registo, bases abstratas e logging declaradas. **Não é uma execução da CLI instalada nem um relatório gerado por um LLM; não houve chamadas a modelos reais.**

## Resultado sobre configurações e fontes inalteradas

| Conjunto | Perguntas de origem | Acertos/pontuáveis de «sempre A» | Pontuação escolhida para relatório | Enunciados presentes no texto do gerador |
| --- | ---: | ---: | ---: | ---: |
| CUPCase, test | 3 562 | 3 562/3 562 | 100,00% | 0/3 562 |
| SciQ, test | 1 000 | 994/997 | 99,70% | 1 000/1 000 |
| GPQA, main dos autores | 448 | 412/427 | 96,49% | 0/448 |
| MMLU, all/test: controlo da ordem e enunciado | 14 042 | 3 222/14 042 | 22,95% | 14 042/14 042 |

SciQ exclui três referências e GPQA exclui 21. Mantivemos esses denominadores nativos. Nos 5 010 registos afetados, a resposta correta ocupa a primeira posição; os desvios de 100% vêm da interpretação das referências pelo parser. MMLU preserva os enunciados e tem ouro distribuído pelas quatro posições. É um controlo saudável **destas propriedades**, não de todas as etapas.

O programa constante B recebe 0/3 562 no CUPCase, 0/997 no SciQ e 2/427 no GPQA. A etapa `MetricRunner` devolve zero nestas execuções, incluindo MMLU. A função `_resolve_report_score` escolhe explicitamente a `accuracy` do DataFlow, embora os próprios resultados estejam marcados `role=diagnostic` e `display_as_primary=false`. Por isso, não substituímos silenciosamente a métrica zero por uma pontuação nossa: guardámos ambas e executámos o seletor original que explica a pontuação apresentada.

## Correção com as mesmas perguntas e opções

No CUPCase completo, restaurámos o placeholder do enunciado e baralhámos apenas a ordem das quatro opções existentes, com seed 20261114. A referência continua a ser exatamente o diagnóstico original. Os autores do CUPCase também baralham opções no seu código de avaliação por geração.

**«Sempre A» passa de 3 562/3 562 para 905/3 562 = 25,4071%.** Todos os 3 562 enunciados chegam então ao gerador. O verificador independente de artefactos confirma igualdade dos casos, dos diagnósticos corretos e dos conjuntos de opções antes/depois. Esta queda mede o efeito da ordem da resposta sobre um programa constante; não mede a melhoria de raciocínio causada por recuperar o enunciado.

Retivemos duas limitações que impedem chamar a esta configuração uma correção integral:

- A primeira tentativa ainda deu 100%: mudámos as opções visíveis, mas deixámos `choice_text_fields` do parser na ordem antiga, com ouro primeiro. A previsão de 905 acertos falhou. Esse resultado e os artefactos foram preservados. Na segunda tentativa, alinhámos também esta declaração com a lista exibida.
- Mesmo na segunda tentativa, o parser elimina textos de opções repetidos ao resolver a referência. Há 54 casos com opções repetidas e 21 em que essa operação desloca a letra correta. A previsão para B era 882; a pontuação nativa foi 888. O verificador regista 882 respostas semanticamente alinhadas com as opções exibidas e seis créditos adicionais. A previsão para A, 905, verificou-se exatamente. Não modificámos o algoritmo para fazer passar a previsão de B.

## O que muda na investigação

Esta é uma consequência natural e grande de uma configuração publicada: uma avaliação de diagnóstico ou ciência pode atribuir uma pontuação quase perfeita sem resolver nenhuma pergunta, e em dois conjuntos sem sequer apresentar a pergunta. O controlo MMLU e a correção do CUPCase localizam a falha no transporte da tarefa e da posição das respostas, sem depender de um efeito desejado num LLM.

A auditoria das respostas originais do PromptPG segue como resultado negativo para a hipótese de anular o ganho principal: na seed publicada, mantém-se a vantagem de 515/7 686 = 6,7005 pontos percentuais sobre o GPT-3 com CoT nas correções testadas. Não procurámos uma regra que invertesse essa conclusão.

Este resultado é mais direto do que os ensaios construídos com uma opção «A. None». **Ainda não permite afirmar superioridade científica ao GAMMAF.** A causalidade local e a consequência na pontuação estão demonstradas; a novidade geral, a reprodução externa independente e o efeito em usos ou resultados históricos publicados continuam por estabelecer. A existência de viés de posição ou de erros de extração em geral não é uma alegação de novidade nossa.

## Reprodução e fontes

Código, protocolos prévios, fontes e verificação estão nesta pasta. `scientific_summary.json` contém as contagens e fronteiras; `verification-final.json` conserva a recontagem sem importar código do avaliador, incluindo as 21 referências residuais. Não há conteúdo das perguntas GPQA neste relatório.

| Etapa | Execução GitHub Actions | Artefacto |
| --- | ---: | ---: |
| Métodos nativos, todos A/B/C/D | 43644200923 | 14132899113 |
| Método completo original e MMLU | 43645404107 | 14132959007 |
| Primeira correção incompleta, previsão rejeitada | 43645621491 | 14134126317 |
| Segunda correção, queda de A e resíduo do parser preservados | 43645998862 | 14133559844 |

```bash
python3 verify_artifacts.py entrypoint-evidence.zip repair2-evidence.zip \
  66de2030edca15d53c8318b59821d2e8ef06c31f3e94f8e7cba6d2bd4b5378fe
```

Revisão One-Eval: `8aba20ad17ee2c7d2391162ac03ffaebcbb17506`. Dependência: wheel PyPI `open-dataflow==1.0.10`, SHA256 verificado antes de executar. Os hashes das fontes e dos dados oficiais estão em `sources.json`, `scientific_summary.json` e nos artefactos.

Fontes primárias: [configurações One-Eval](https://github.com/OpenDCAI/One-Eval/blob/8aba20ad17ee2c7d2391162ac03ffaebcbb17506/one_eval/utils/bench_table/bench_gallery.json), [entrada de avaliação](https://github.com/OpenDCAI/One-Eval/blob/8aba20ad17ee2c7d2391162ac03ffaebcbb17506/one_eval/toolkits/dataflow_eval_tool.py), [seleção do resultado no relatório](https://github.com/OpenDCAI/One-Eval/blob/8aba20ad17ee2c7d2391162ac03ffaebcbb17506/one_eval/agents/report_gen_agent.py#L254), [parser e eliminação de duplicados](https://github.com/OpenDCAI/One-Eval/blob/8aba20ad17ee2c7d2391162ac03ffaebcbb17506/one_eval/metrics/parsers/choice.py#L62), [avaliação dos autores do CUPCase](https://github.com/nadavlab/CUPCase/blob/898d77c1c6da71e852b7090c482ff1c82c403dd7/gpt_and_med_lm_evaluation/gpt_qa_eval.py).

A pesquisa restrita de issues e PRs One-Eval por CUPCase/SciQ/GPQA/shuffle devolveu zero correspondências; isso não prova novidade. O [PR 63](https://github.com/OpenDCAI/One-Eval/pull/63), já integrado, reconhece problemas anteriores de prompts, métricas e extração. A nossa reprodução refere-se ao código atual acima, sem atribuir automaticamente as falhas aos números históricos do artigo.

Recursos novos: **zero chamadas Adaption, zero judges, zero classificações humanas e zero alterações ao manuscrito**. A revisão humana já preparada mantém o seu próprio objetivo e pode continuar em paralelo. Próximo passo: reprodução independente por uma instalação normal e validação do percurso API com respostas reais, seguida de análise do impacto e da novidade; nenhuma inversão de ranking será exigida como condição de sucesso.
