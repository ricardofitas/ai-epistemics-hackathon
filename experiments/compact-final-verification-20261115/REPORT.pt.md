# Estudo compacto: pares finais verificados

15-11-2026. Run43659857781 concluído com sucesso às01:07. Painel congelado antes de consultar acertos, sem mudança de seleção. A fila grande não foi retomada:636células têm terminal,583completas e53HTTP504desconhecidos. A expressão “pares completos” refere-se a228dos256pares de contexto;115/128no núcleo e113/128na expansão. Não são228perguntas independentes:64perguntas de contexto repetidas em4famílias.

## Efeitos primários nas mesmas perguntas

Os intervalos de desconhecidos abaixo distribuem0/1 aos resultados em falta e usam todos os casos planeados. São diferentes dos intervalos bootstrap95%, condicionados aos pares completos e agrupados por conteúdo-fonte. São amostras finitas pequenas, não efeitos populacionais.

|Tarefa/estrato|Modelo|Pares completos/planeados|Vitórias reparação/original|Limites por desconhecidos (pp)|Bootstrap95% nos completos (pp)|
|---|---|---:|---:|---:|---:|
|SIQA contexto|qwen3.8-27b|27/32|5/2|[0.00, 15.62]|[-7.41, 29.63]|
|SIQA contexto|gemma-4-31b-it|30/32|7/3|[9.38, 15.62]|[-6.67, 33.33]|
|SIQA contexto|deepseek-v4-flash|24/32|7/5|[-3.12, 25.00]|[-20.83, 37.50]|
|SIQA contexto|glm-5.2|23/32|5/2|[0.00, 31.25]|[-8.70, 34.78]|
|ScienceQA com pista|qwen3.8-27b|14/16|4/0|[25.00, 37.50]|[7.14, 57.14]|
|ScienceQA sem pista|qwen3.8-27b|16/16|0/0|[0.00, 0.00]|[0.00, 0.00]|
|ScienceQA com pista|gemma-4-31b-it|15/16|3/0|[12.50, 18.75]|[0.00, 40.00]|
|ScienceQA sem pista|gemma-4-31b-it|16/16|0/0|[0.00, 0.00]|[0.00, 0.00]|
|ScienceQA com pista|deepseek-v4-flash|16/16|6/0|[37.50, 37.50]|[12.50, 62.50]|
|ScienceQA sem pista|deepseek-v4-flash|16/16|0/0|[0.00, 0.00]|[0.00, 0.00]|
|ScienceQA com pista|glm-5.2|15/16|2/0|[12.50, 18.75]|[0.00, 33.33]|
|ScienceQA sem pista|glm-5.2|16/16|0/0|[0.00, 0.00]|[0.00, 0.00]|

As16perguntas ScienceQA sem pista têm16pares completos por modelo, todos empatados. Ambos os braços já acertavam nessas perguntas: controlo com efeito de teto, não prova geral de ausência de efeitos de formato. Nos16casos com pista, ganhos permanecem positivos nos limites finitos dos quatro modelos, mas nem todos os ICs bootstrap excluem zero. Em SIQA, nem todos os modelos têm ganho robusto aos desconhecidos/ICs; conservar esse negativo. Comparações exploradas múltiplas, sem teste confirmatório de uma alegação universal.

## Referência e inventário de opções, mesmas saídas

Redux:12/12saídas completas nos3casos assinalados, mais45/48nos12controlos saudáveis por modelo. Corrigir apenas a referência com o mesmo parser altera8flags (duas por modelo);4respostas do terceiro caso continuam erradas. Os45controlos completos preservam pontuações;3unknowns. Não são12questões corrigidas:3questões×4modelos.

SuperGPQA:44/64respostas completas. Há9respostas corretas explícitas na fonte cuja referência o parserA-D exclui (Qwen1,Gemma2,DeepSeek4,GLM2). São outputs reais retidos; não controles construídos. Preservar exclusão nativa: não transformar9exclusões em0%modelo. Comparação com o contrato de fonte muda inventário de letras e referência; não chamar referência-only. Os20unknowns continuam no denominador científico64.

## Testemunho exploratório de extração

Uma resposta completa Gemma em SIQA diz literalmente que não consegue determinar a resposta sem contexto. O extrator original retornaC porque a última maiúscula é a inicial de “Carson”, e o ouro éC. O par primário fica1→0 (a reparação dáANSWER:B, errada). Não reescrevemos esse resultado: a leitura de escolha explícita mostra que o1original vem de uma letra dentro de um nome, não de uma opção expressa. Há seis respostas sem rótulo explícito analisadas; apenas esta recebe crédito. Diagnóstico escolhido após ver outputs, não nova hipótese prospetiva ou validação humana.

Fonte exata confirmada byte-a-byte em modelscope/evalscope@59bb367bd8565f347266a48ac1230af0b5131b97, evalscope/utils/multi_choices.py, blobfbeb457119168b114e6a8f7833ac553512c51724. Executado o módulo-folha inteiro inalterado com três holders de tipos declarados; não instalação/CLI do framework. Mecanismo geral de extração permissiva é conhecido; não reivindicamos primeira descoberta.

## Identidades, recursos e fronteira

Conferidos636registos normalizados,583completos com hash/corpo/modelo/uso/cap;577rótulos explícitos conferidos por implementação separada. Os seis restantes são recusas de responder sem contexto: extrator-fonte executado à parte, não adjudicação factual humana. O núcleo, expansão e todas as flags/vitórias/derrotas/empates e limites foram reconciliados sem importar o analisador primário. Os ICs bootstrap são os originais, não uma nova simulação independente.

Recibos finais das filas antigas autenticados e reconciliados com intents/attempts. Nenhum antigo órfão ou504 foi reenviado. O compacto tem574POSTs novos:518completos,52HTTP504,4HTTP429. Mais68attempts-semente (65completos,1unknown,2recusas429). As seis429, incluindo duas antigas, tiveram apenas retries explícitos; os terminais finais são583stop/53HTTP504, sem órfãos novos. Todos os requests dentro do cutoff e do manifesto fixado. Nenhum POST novo por esta revisão.

A contabilidade spent_or_committed do executor é1,393001772créditos, incluindo reutilizações e reservas de unknowns. Não é fatura confirmada, moeda ou custo exclusivamente novo. Sem juiz. As filas grandes continuam canceladas; não retomar.

Fronteira: prompts/parsers nativos carregados das fontes, transporte externo Adaption; não CLI completa dos dois frameworks para o compacto. A execução instalada HTTPWino foi verificada separadamente e os dados pausados têm relatório próprio; não misturar denominadores. Fonte/casos/contratos já expostos em parte; nova validação por configuração e outputs, não globalmente cega.

Artefacto final14139829847, SHA256649c1ab2870df6642382e1e9c819d9529f0d1ce000dc8b19ac9b9a7184495847. Final imutável e artefacto congelado incluídos no pacote juntamente com os ledgers finais das duas filas canceladas. Snapshots das vagas não são atómicos entre ficheiros; os resultados finais usam o NORMALIZED.jsonl exato.

## Próximos passos e prazo

Consolidar a conclusão por mecanismo, quantificar o efeito na decisão de avaliação sem forçar rankings e rever novidade contra os antecedentes. Já não é necessário completar benchmarks nem repetir os28pares com desconhecidos: muitos contêm504ambíguos e não podem ser reenviados. Uma experiência nova só se resolver lacuna diferente explicitamente protocolada; nada automático após este bloco. Hard cutoff para novosPOSTs10:31:35; trabalho experimental/testes termina12:31:35. Depois, só consolidar evidência existente.

O compacto cobre quatro configurações dirigidas aos mecanismos já assinalados; não valida a precisão prospetiva do checker nas12configurações nem todos os oito controlos saudáveis do plano grande.

Manuscrito/PDF/sourceZIP e folha humana sem alterações;64classificações humanas continuam vazias. Preservados PromptPG negativo, CUPCase residual e limites de todos os estudos. Não estabelecemos automaticamente superioridade ao GAMMAF.
