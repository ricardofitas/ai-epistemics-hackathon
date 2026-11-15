# Revisão da replicação natural e da sua contribuição científica

15-11-2026. Esta etapa é revisão metodológica e implementação de análise, sem novas respostas de modelos. O compacto continua concluído; as filas grandes não foram retomadas. Manuscrito e revisão humana intactos.

## O que foi efetivamente conferido

A especificação de64pares foi recuperada do pacote persistente original. Conferi128fontes,1024células planeadas e todos os hashes dos pedidos contra o manifesto autenticado do gate instalado. Os64pares diferem exatamente em um token lexical/pontuação, mantêm opções na mesma ordem e têm respostas corretas opostas. Todos geram pedidos originais idênticos dentro do par, porque o enunciado desaparece; os pedidos reparados são distintos.

A seleção permaneceu byte-a-byte a mesma: SHA256canónico08277c7248d61fa35d4a546ed34ff0848963c4698155875c67c63ee58dbb8da9. Nenhum dos128índices coincide com os117índices excluídos por intents anteriores ou pelo painel anterior de12respostas. Isto é exclusão de exposição documentada a chamadas, não garantia de dados globalmente inéditos ou ausência no pré-treino. Não substituí pares após a revisão de minimalidade.

1024células têm apenas768hashes de payload distintos:256células originais repetem o corpo de outro item. Uma futura execução não pode fazer cache/deduplicação de RESPOSTAS apenas pelo hash: a especificação pede uma chamada distinta por item/modelo/braço. Cache de tokens de entrada no fornecedor não equivale a reutilizar uma resposta. Os doisIDs de tentativa e os terminais precisam ser mantidos separados.

## Inferência implementada antes de quaisquer respostas desta replicação

O novo analyse_pair_replication.py consome o ledger de previsões do analisador nativo autenticado, sem substituir o parser. Confere fonte, pedido, ouro e as duas pontuações do mesmo output; mantém respostas completas não parseáveis como erros conhecidos e incompletas/ausentes como desconhecidos.

Para cada par e modelo, o contraste fixado é:

    Δ = [ganho da reparação na precisão conjunta com referência da fonte]
        − [ganho da reparação na precisão conjunta com referência nativa].

Um par só acerta se os dois itens acertarem. Os dois sinais de pontuação usam as MESMAS quatro respostas. Enumerar em conjunto A/B/não-parseável nos outputs em falta preserva essa dependência. Há81estados completos possíveis e16máscaras de desconhecidos por estado;1296controlos de desenvolvimento passaram. O contraste pode ser−2,−1,0,+1,+2: não foi construído para ser inevitavelmente positivo. Estas contagens são controlos construídos de código, não observações de modelos.

O estimando principal pesa igualmente64pares e quatro famílias fixas. Limites de identificação usam todos os64grupos planeados. O bootstrap de casos completos conserva as quatro famílias e os braços juntos dentro do par; esse IC é condicionado à disponibilidade e não substitui os limites do painel planeado. Devido aosHTTP504 anteriores, o número de pares com todos os16outputs pode ser pequeno: reportar cobertura em vez de descartar silenciosamente grupos.

## Qualificação analítica

Se os dois pedidos originais de um par têm a mesma distribuição marginal de respostas e as gerações são independentes, a probabilidade de acertar ambos perante os ouros opostos é pA×pB≤1/4. A referência nativaB/B pode dar1a uma política sempreB. Sem independência, mas mantendo marginais iguais, o limite geral para acertar o padrão ordenado é1/2. Estes limites são condicionais; não são limites rígidos de uma realização estocástica nem valem com informação sobre ID, ordem ou outro canal. A ausência de duplicação de respostas por cache importa para distinguir os regimes. A matemática é conhecida, não um novo teorema.

## Originalidade: o que esta revisão resolve e o que não resolve

A métrica de pares naturais é antecedente de Elazar et al., “Back to Square One”, EMNLP2021, DOI10.18653/v1/2021.emnlp-main.819, cuja fonte primária confirma o uso de frases gémeas na avaliação: https://aclanthology.org/2021.emnlp-main.819/ . Não apresentar group scoring como invenção nossa.

A nova coleta preparada pode transformar uma análise retrospectiva condicionada à disponibilidade numa previsão testada em pares sem chamadas anteriores documentadas. Não cria, só pelo número de pares, um mecanismo novo, outro framework independente ou uma vantagem incremental do verificador. A comparação já registada no estado encontrou os mesmos384alertas no checker e no comparador que partilha a normalização semântica: não repetir essa calibração ou afirmar superioridade do auditor.

A alegação candidata mais delimitada é uma interação de medição: quanto uma correção que restaura a pergunta melhora a consistência factual, mas esse ganho fica ocultado ou distorcido pela referência incompatível. O contraste permite resultados nulos/negativos e não exige inverter rankings. A força de novidade dessa aplicação específica ainda precisa ser posicionada contra os antecedentes, não resolvida com mais chamadas do mesmo erro.

**Não lancei1024pedidos nesta etapa.** A auditoria de fontes e o analisador estão completos; a replicação continuaPREPARED_NOT_RUN. Se essa extensão for escolhida pelo ganho científico esperado, congelar também o executor, o catálogo atual, o teto efetivo e o protocolo de captura antes de despachar. A autorização geral existente mantém-se; isto não cria uma exigência genérica de nova permissão. Não repetir saídas anteriores ou tentativas ambíguas. Manter cutoff10:31:35e fim de testes12:31:35.

Recursos desta revisão:0chamadas de modelo,0juízes,0novas gerações nativas,0custo de inferência. Conferidos dois artefactos de origem e o pacote persistente da análise anterior. A folha humana foi lida sem alterações e mantém64campos vazios. Nenhuma afirmação de superioridade ao GAMMAF ou alteração editorial.
