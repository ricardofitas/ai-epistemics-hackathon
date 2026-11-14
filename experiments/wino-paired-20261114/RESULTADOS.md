# One-Eval — ensaio emparelhado com modelos reais

Foram executados 200 pedidos novos à Adaption em 14 de novembro de 2026. Ficaram completas 194 respostas. O desenho contém 50 perguntas de validação do WinoGrande, dois modelos e duas versões do texto. As condições mantêm a mesma ordem de opções e os parâmetros de inferência. 

## Precisão com os rótulos oficiais

| Modelo | Texto original | Texto corrigido | Ganho observado | Limites do ganho com respostas desconhecidas |
| --- | ---: | ---: | ---: | --- |
| gemma-4-31b-it | 6,0% a 98,0% | 88,0% | +82,0 pp | -10,0 pp a +82,0 pp |
| qwen3.8-27b | 46,0% a 52,0% | 88,0% a 94,0% | +42,0 pp | +36,0 pp a +48,0 pp |

O ganho observado atribui zero às respostas incompletas ou sem uma única etiqueta final válida. Os limites permitem que cada uma dessas respostas tenha contribuição entre zero e um. As mesmas 50 perguntas entram nos dois percursos de cada modelo.

No Qwen, o ganho mantém-se positivo em toda a análise de sensibilidade dos resultados desconhecidos. No Gemma, 46 das 50 respostas completas ao texto original não apresentam uma única opção final válida. Assim, a grande diferença sob a convenção de zero inclui uma mudança da capacidade de produzir uma resposta avaliável. O intervalo conservador do ganho do Gemma abrange zero. Nas duas condições corrigidas, a pontuação observada é 44/50; o Qwen conserva ainda três respostas incompletas nessas 50 perguntas.

## Comparações definidas antes das respostas

| Modelo | Subconjunto | Perguntas | Ganho observado | IC bootstrap 95% | Limites do ganho |
| --- | --- | ---: | ---: | --- | --- |
| gemma-4-31b-it | Pares com rótulos opostos | 30 | +86,7 pp | +70,0 pp a +100,0 pp | -13,3 pp a +86,7 pp |
| gemma-4-31b-it | Controlos com texto único | 20 | +75,0 pp | +55,0 pp a +95,0 pp | -5,0 pp a +75,0 pp |
| qwen3.8-27b | Pares com rótulos opostos | 30 | +36,7 pp | +23,3 pp a +46,7 pp | +33,3 pp a +43,3 pp |
| qwen3.8-27b | Controlos com texto único | 20 | +50,0 pp | +25,0 pp a +75,0 pp | +40,0 pp a +55,0 pp |

Os intervalos usam 10 000 reamostragens de grupos dentro de cada subconjunto, com semente 20261113. Há 15 grupos de duas perguntas com o mesmo texto original e 20 controlos individuais. Os intervalos são condicionais à convenção de pontuar respostas desconhecidas com zero e à amostra observada. O JSON apresenta também o envelope de sensibilidade. O painel global combina os subconjuntos com pesos 30/50 e 20/50.

## Efeito da referência no mesmo texto de resposta

A tabela seguinte reutiliza as respostas obtidas com o texto corrigido. A função original de pontuação e o seu parser são executados em ambos os percursos. O campo de referência muda dos rótulos numéricos da origem para etiquetas oficiais canónicas.

| Respondedor | Referência original | Referência corrigida |
| --- | ---: | ---: |
| gemma-4-31b-it | 46,0% | 88,0% |
| qwen3.8-27b | 48,0% | 88,0% |
| Sempre A | 0,0% | 50,0% |
| Sempre B | 100,0% | 50,0% |

As pontuações desta tabela seguem o parser heurístico original, incluindo texto parcial que tenha sido capturado. A medida principal da primeira tabela exige uma resposta completa com uma única etiqueta válida. Os dois cálculos e os respetivos denominadores estão conservados no ficheiro de resultados.

## Âmbito e decisão científica

A seleção foi congelada antes das chamadas e exclui todos os textos do piloto anterior. Trinta perguntas foram escolhidas por terem rótulos opostos em pares de textos idênticos e vinte como controlos. Esta seleção permite avaliar o mecanismo em condições diagnósticas. A frequência da falha na utilização externa continua por medir.

A intervenção repõe a pergunta e remove chavetas que o formatter deixara por resolver. O efeito medido refere-se à correção conjunta do texto. A validação foi uma alteração explícita do split, pois a configuração predefinida do One-Eval usa o teste sem rótulos públicos. A versão auditada é 8aba20ad17ee2c7d2391162ac03ffaebcbb17506 com open-dataflow 1.0.10. Os textos enviados à API são exatamente os capturados ou reparados previamente. O replay das métricas usa os métodos originais e o carregamento isolado de dependências documentado na auditoria anterior.

O controlo anterior no EvalScope passou os seis conjuntos para os invariantes testados. A busca pública anterior em 26 forks não identificou uma execução externa com resultados individuais afetados verificáveis. A comparação de impacto com o GAMMAF continua a depender desse tipo de evidência.

O passo seguinte é aplicar as verificações já executadas aos registos de uma utilização externa identificável e medir a mudança da conclusão. A correção e os controlos do EvalScope permitem preparar a ferramenta de verificação com casos que devem falhar e casos que devem passar. A revisão da novidade deve comparar estes mecanismos com os trabalhos existentes sobre reprodutibilidade de avaliação.

## Captura e reprodução

A execução 43533000838 foi verificada por uma implementação independente que reconstrói os corpos dos pedidos, os eventos terminais, o texto final e os hashes dos ficheiros de streaming. Intervalo mínimo observado entre inícios de pedidos de 4.997 segundos. Cada pedido teve uma tentativa. As respostas incompletas permaneceram nos denominadores.

Depois de descompactar o pacote, executar `python oneeval_paired_20261114/verify_capture.py` e `python oneeval_paired_20261114/analyze_paired.py`. O segundo comando requer as versões indicadas em `requirements.txt`. Os fontes mínimos e os dados necessários ao replay acompanham o pacote. 

[Código One-Eval auditado](https://github.com/OpenDCAI/One-Eval/tree/8aba20ad17ee2c7d2391162ac03ffaebcbb17506) · [Protocolo e resultados privados](https://github.com/ricardofitas/ai-epistemics-hackathon/tree/experiment/advice-execution-transfer-20261113/experiments/wino-paired-20261114)
