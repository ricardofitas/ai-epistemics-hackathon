# Resultados de execução dos conselhos e novos testes

A confirmação nas 16 famílias novas produziu 191 respostas corretas e uma incompleta, em 192 respostas previstas. A distorção ficou limitada a 0–6,25 pontos percentuais para DeepSeek–Gemma-31B e foi zero para Qwen–Gemma-26B. O critério previamente definido de pelo menos 10 pontos não foi atingido. O desempenho próximo de 100% limita a informação desta amostra sobre diferenças entre os modelos.

Ao longo dos dois conjuntos novos foram avaliadas 20 famílias e 240 respostas de modelos. Foram obtidas 236 respostas corretas e quatro incompletas. As primeiras quatro famílias pertencem ao conjunto inicial; a confirmação seguinte excluiu-as.

As duas leituras por modelos concordaram sobre as propriedades de execução de 15 dos 26 conselhos completos. Três receitas permitiram uma reprodução restrita nos registos matemáticos anteriores: SR-01, SR-17 e SR-20. A escolha de recurso dessas receitas amplia a diferença DeepSeek–Gemma em 33,33–63,33 pontos no conjunto anterior de 30 famílias. As estatísticas exigidas por receitas com dados de origem, filtros ou novas paráfrases precisam dos respetivos elementos adicionais. Todos os 36 pedidos originais permanecem na contagem, incluindo dez respostas incompletas.

O primeiro leitor de anotações rejeitava JSON entre blocos Markdown e números JSON sem aspas. Essa limitação foi corrigida numa análise derivada, preservando a recolha e análise iniciais. A regra de qualidade das perguntas continuou a exigir concordância nos valores, clareza e transformação. A confirmação adicional usou as 16 famílias ainda sem resultados. As 48 respostas oficiais dessa confirmação foram também recalculadas aritmeticamente pelo coordenador.

O serviço devolveu HTTP 429 em 142 pedidos da confirmação. Foi feita uma recuperação documentada desses pedidos, com um pedido de cada vez e intervalo mínimo de cinco segundos. Os 50 resultados já completos foram preservados. Uma implementação aritmética separada verificou os resultados, a identidade dos pedidos e o registo de recuperação.

# Novo candidato na implementação pública do One-Eval

O código publicado em OpenDCAI/One-Eval, revisão 8aba20ad17ee2c7d2391162ac03ffaebcbb17506, regista choice_accuracy, accuracy e acc como nomes da mesma função. Com mais de 100 registos, o caminho run_bench trata os aliases como elegíveis para processamento paralelo. Quando o denominador configurado é valid_only, a redução paralela usa pesos incompatíveis com os denominadores dos grupos.

| Conjunto construído | choice_accuracy | accuracy com dois processos | Com a correção |
|---|---:|---:|---:|
| A, 51 corretas, 1 errada e 49 abstenções | 98,0769% | 50,4950% | 98,0769% |
| B, 76 corretas e 25 erradas | 75,2475% | 75,2475% | 75,2475% |

O vencedor desta comparação muda apenas com o alias. O exemplo foi reproduzido na função publicada ScoreCalcAgent.run, incluindo a gravação dos resultados da fase de cálculo, com um adaptador local para as dependências de orquestração. A correção proposta restaura a equivalência em 60 combinações de tamanho, número de processos e nome da métrica, além de 20 permutações e da verificação da fase de cálculo.

O exemplo usa respostas construídas. A rota dedicada run_bench_with_contract e o denominador total passaram os controlos de invariância. Os contratos primários inspecionados na galeria usam o nome canónico. A frequência do problema em configurações e respostas reais, a revisão humana externa e a análise de novidade mais ampla continuam por estabelecer.

A próxima verificação com maior valor é aplicar a reprodução do One-Eval a resultados de modelos já registados e medir se os aliases ou as escolhas automáticas de configuração afetam uma conclusão real. O ensaio de transferência do GSM-Plus fica documentado como resultado negativo no critério definido.
