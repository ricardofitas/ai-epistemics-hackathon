# Próxima etapa, após esta auditoria

1. Congelar uma bateria de invariantes antes de olhar para novos resultados: presença e influência da pergunta/contexto, cobertura das referências, inclusão da resposta correta, preservação dos rótulos e baseline de posição. O adaptador atual é uma proposta por origem; ainda não é um validador geral de todos os contratos.
2. Aplicar essa bateria a um segundo avaliador e a um painel de benchmarks definido previamente, incluindo casos em que se espera funcionamento correto. O objetivo é testar a generalidade do problema e do método, sem selecionar apenas os sistemas com falhas.
3. Procurar artefactos de utilizações efetivas das versões afetadas. Uma configuração predefinida disponível não prova exposição de utilizadores nem invalida automaticamente um resultado publicado. Não contactar terceiros ou publicar issues sem instruções para isso; o rascunho local está pronto para revisão.
4. Se a validade e a exposição justificarem, avançar de12 para50 perguntas novas por benchmark no ensaio com modelos, excluindo as36 perguntas deste piloto. Comparar de forma emparelhada os percursos nativos e corrigidos, preservar chamadas incompletas e analisar por pergunta, com dependência entre condições e modelos explícita.
5. Rever a novidade e as alternativas de explicação antes de redigir uma alegação de descoberta para um paper. A contribuição proposta é uma auditoria causal de contratos de avaliação e uma intervenção verificável. A presença de vários bugs num só software, por si, não demonstra generalidade ou impacto superior ao GAMMAF.

Os96 pedidos originais ficam congelados. A reprodução em Python3.11 não fez novas chamadas a modelos. Não foram publicados relatórios, issues ou PRs externos.
