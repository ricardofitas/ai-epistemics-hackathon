# Seguimento do impacto externo

A pesquisa dirigida não confirmou uma conclusão externa afetada. Foi identificada uma pista concreta adicional no artigo DataFlow, cuja Tabela 2 publica resultados ARC-C e WinoGrande. O texto e o repositório consultados não ligam essa tabela à versão do avaliador nem a pedidos e respostas por pergunta. A sobreposição de benchmarks exige verificar essa proveniência antes de atribuir qualquer efeito.

O PR #63 do One-Eval, integrado em 1 de julho de 2026, já reconhecia correções de extração/pontuação e mudava o destaque dos relatórios para a métrica primária. Isto deve entrar no enquadramento da novidade. A inspeção não estabelece que os autores tivessem identificado os defeitos específicos agora medidos.

Foram ainda examinadas consultas dirigidas, a árvore pública fixada do LoopAI, a release e comentários de demonstração. Os novos resultados do índice eram scripts próprios, configurações de outros avaliadores ou metadados. Continuam em falta a configuração executada, a versão do código e as saídas ligadas a uma conclusão publicada.

Fontes primárias

- https://github.com/OpenDCAI/One-Eval/pull/63
- https://github.com/OpenDCAI/DataFlow/blob/84863d868fa91bd6169001af33b25e127bce709d/README.md
- https://arxiv.org/html/2512.16676v1
- https://github.com/OpenDCAI/Dataflow-LoopAI/tree/30d078f36bb95508088f0ea229cbd804105b41f9

O ficheiro EXTERNAL_FOLLOWUP.json guarda as consultas, contagens, identidades Git e limites da inspeção. Não houve chamadas a modelos nem comunicações a terceiros.

