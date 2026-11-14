# Auditoria natural: semântica da ordem e antecedentes

14 de novembro de 2026. Este seguimento é uma revisão primária e uma conferência independente dos registos já capturados. Não executa novamente métodos nativos, CLI, modelos ou juízes. Não altera o manuscrito, PDF, sourceZIP, folha humana nem a branch ativa da conversa direta.

## Resultado efetivamente conferido

O ZIP original do run43644200923 foi autenticado pelo SHA256 `ed328b8026f49436f0ab13e821c7ad87e2d3187737bcdb705f4b2625a63ede54`. O verificador independente confere os 5 010 registos de origem e as quatro séries constantes A/B/C/D: mesmas colunas de origem entre séries, saída constante literal, denominadores, rótulos de referência, pontuação guardada e origem escolhida pelo seletor do relatório.

| Painel original | Linhas de origem / ouro na primeira opção | Constante A no seletor do relatório | Referências excluídas |
|---|---:|---:|---:|
| CUPCase test | 3 562 / 3 562 | 3 562 / 3 562 | 0 |
| SciQ test | 1 000 / 1 000 | 994 / 997 | 3 |
| GPQA main | 448 / 448 | 412 / 427 | 21 |

As diferenças entre a posição de origem e a pontuação são reais: três referências SciQ e quinze GPQA válidas são interpretadas como letras diferentes de A pelo parser. As pontuações não devem ser arredondadas para “100% em tudo”. Os números do quadro são do seletor de pontuação do relatório, que escolhe `dataflow_eval:accuracy`; os estágios ordinário e de contrato registam zero noutro percurso de representação. São estágios distintos. O verificador não substitui um pelo outro.

O artefacto contém métodos carregados da fonte, adaptadores de armazenamento e respostas constantes. Não é prova de CLI completo, de comportamento observado de um LLM ou de uma conclusão publicada afetada. A conversa direta é responsável pelo ensaio do ponto de entrada original e pelo controlo MMLU; não foram duplicados aqui.

## O mecanismo é específico; a ideia geral já tem antecedentes

Ter um campo `Correct Answer` separado dos distratores é uma representação legítima. Um índice correto fixo também é legítimo quando o avaliador calcula separadamente a verosimilhança de cada continuação. O problema aparece ao transportar essa ordem dependente do ouro para uma lista A-D mostrada num pedido de geração, sem permutar e remapear a resposta correta.

Os avaliadores dos autores de CUPCase e GPQA baralham opções e ajustam o índice correto. O YAML SciQ do harness oficial usa verosimilhanças independentes e candidato correto na última posição. Estas implementações são controlos de semântica; não demonstram que os resultados dos autores estejam afetados.

**Não é defensável reivindicar a primeira descoberta do mecanismo geral.** A issue pública [Tinker Cookbook#978](https://github.com/thinking-machines-lab/tinker-cookbook/issues/978), de17/10/2026, secção6, já descreve a cadeia de campos corretos primeiro, alvo A e política constante A com crédito integral. A [PR#994](https://github.com/thinking-machines-lab/tinker-cookbook/pull/994), de06/11/2026, propõe uma permutação determinística e testes de ambiente. A issue limita a sua prova a registos sintéticos e não confirma a aquisição do conjunto real; a PR não recalcula os números históricos. São antecedentes próximos, não uma reprodução independente dos números One-Eval.

Sun et al., [arXiv2506.04734v1](https://arxiv.org/html/2506.04734v1), secção2.6, já discutem avaliações com ouro sempre A e comparam posições e aleatorização. Não identificam naquela passagem os frameworks referidos. Trabalhos de sensibilidade à ordem e extração também antecedem a presente investigação; não equivalem automaticamente à exposição determinística da resposta ou à atribuição causal num percurso concreto.

O resultado que permanece delimitado é a instanciação no One-Eval fixado, sobre dados oficiais concretos, com transporte da ordem para geração e seleção de uma pontuação diagnóstica pelo relatório. A novidade e a consequência de ponta a ponta têm de ser avaliadas nesse nível específico, não pela contagem de benchmarks nem por uma alegação genérica sobre enviesamento posicional.

## Limites que condicionam a conclusão

- Os448registos GPQA são `gpqa_main.csv`; a aquisição predefinida da galeria aponta para GPQA-Diamond. Este painel não demonstra a aquisição predefinida Diamond.
- A ausência das perguntas CUPCase/GPQA e do suporte SciQ decorre de placeholders/nomes de campos e é distinta da exposição da posição correta. O wheel DataFlow1.0.10 foi recuperado e o seu SHA256 e duas classes foram conferidos separadamente.
- `_mark_stats_diagnostic` marca a pontuação como diagnóstica e não primária; `_resolve_report_score` escolhe a sua accuracy sem consultar esses sinalizadores ou a métrica recebida. Esta é uma cadeia de código verificada; o CLI e o relatório completo pertencem ao ensaio da conversa direta.
- A comparação histórica PromptPG–GPT-3 concluída pela conversa direta é negativa para a hipótese de eliminar o ganho seed2. Não foi repetida nem reinterpretada como uma inversão.
- A revisão humana continua separada, sem classificações inventadas. A folha corrigida por outra conversa não foi alterada.

## Próximo passo derivado

Reconciliar os resultados do `run_eval` e MMLU já assumidos pela conversa direta. Se confirmarem a cadeia, testar a correção mínima que preserva fonte e conjunto de opções, com referência remapeada e identidade explícita da métrica realmente publicada. Qualquer ensaio com respostas reais deve comparar o percurso natural e a reparação sem novas opções falsas. Uma consequência em resultados históricos ou na seleção de modelos só pode ser afirmada com saídas, versões e configuração correspondentes; a constante A, isoladamente, não prova essa consequência.

Fontes imutáveis, hashes, localizações de código, revisão de antecedentes e verificador estão incluídos no pacote. Dados GPQA não são reproduzidos neste relatório; apenas o artefacto original privado os contém.
