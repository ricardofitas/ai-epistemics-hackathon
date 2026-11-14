# MixEval — a pontuação pode esconder a perda do denominador

14 de novembro de 2026. Trabalho privado. Protocolo e implementação fixados no commit `fe6c1952e913391cd424825d8e703cc85d1375c7`, antes de executar a pontuação.

Este ensaio reutiliza os mesmos 200 registos oficiais anteriormente selecionados, 100 de resposta livre e 100 de escolha múltipla. Quatro famílias de respostas construídas e três condições produzem 2 400 registos de condição. As respostas são idênticas entre condições para cada fonte. Assim, o efeito do avaliador fica isolado da geração e da recuperação da pergunta. Não são respostas de modelos nem uma nova amostra independente.

## Resultado principal

O método original de pontuação One-Eval rejeita todas as referências em lista nos dois painéis. Continua a devolver `accuracy=0.0`, com `valid_samples=0`. Este valor é **não avaliável**, não uma observação de 0% de acerto. Uma resposta oficial, uma resposta errada, uma resposta vazia e a resposta constante A recebem o mesmo número apresentado, porque nenhuma referência entra no denominador.

| Condição, resposta construída a partir da referência | Livre, referências válidas | Escolha, referências válidas | Resultado nos controlos |
| --- | --- | --- | --- |
| Parser nativo, targets originais em lista | 0/100 | 0/100 | Ambos não avaliáveis; número apresentado 0,0 |
| Apenas extrair o elemento de listas unitárias | 0/100 | 100/100 | Livre continua não avaliável; escolha 98/100 |
| Despacho por tipo com funções oficiais do modo por regras | 100/100 | 100/100 | Livre 98/100; escolha 100/100 |

Os resultados do modo por regras dizem respeito a esta alternativa oficial, não ao modo predefinido com juiz de linguagem. Também não são uma pontuação oficial do benchmark completo ou uma precisão de modelo.

## Mecanismos e contraexemplos preservados

1. **Referências em lista tratadas como letras.** O parser original tenta interpretar a lista inteira como uma única resposta de escolha e exclui a referência. Corrigir apenas a geração não altera este problema.
2. **Número de opções e base dos índices.** Dois casos com resposta correta E perdem o acerto após a simples extração do índice. A configuração A–D rejeita E e o índice oficial zero-based 4 cai numa alternativa one-based, tornando-se incorretamente D. O despacho oficial usa todas as opções e o índice original.
3. **Limites do próprio modo oficial por regras.** `Government of D.C.` perde o ponto final apenas no lado da resposta; `Tomorrow is another day` é reduzido a `another day`. Ambas são respostas literais presentes nas referências aceites. Os dois casos são mantidos como falhas desse modo heurístico, sem correção retroativa.
4. **Vazio não significa necessariamente zero no modo por regras.** A implementação oficial de escolha sorteia uma opção quando não consegue interpretar a resposta. Com seed42 e a ordem fixada, as 100 respostas vazias geram 100 palpites e 25 acertos. Este resultado descreve o fallback, não desempenho de um modelo. As respostas deliberadamente erradas com uma letra legal têm zero acertos.

Uma conferência física da fonte também corrigiu uma suposição da revisão. Nos 100 registos livres, `options=["None"]` já vinha nos dados. O motor exibiu esse marcador como `A. None` por escolher a família de tarefa errada. A evidência não demonstra que o pré-processamento tenha criado o valor.

## Verificação e reprodução

Um agente distinto conferiu 22 ficheiros congelados, as 200 fontes, os 2 400 registos, 24 painéis, 800 grupos com respostas invariantes e 16 pares de capturas/estatísticas. Reexecutou separadamente as 800 chamadas aos auxiliares oficiais e 1 600 pares de parsing nativo, incluindo todos os sorteios. `VERIFICATION.json` e `COUNTEREXAMPLES.json` guardam os detalhes e as correções das suposições do próprio verificador.

Executar `python run_score_replay.py` recria as capturas; `python verify_replay.py` confere os artefactos. `FROZEN_IMPLEMENTATION.json` contém os hashes anteriores aos resultados. `scoring_adapter.py` fornece uma interface com validação de fonte e modo explicitamente identificado, sem substituir o comportamento oficial. A sua conferência fica separada em `ADAPTER_VERIFICATION.json`.

O percurso executado usa os corpos exatos dos métodos nativos e os módulos originais do parser, com extração AST para isolar dependências. O estudo não executa o motor instalado completo, tokenizadores, transporte de fornecedor ou modelos. Nenhum pedido de inferência foi feito.

## Impacto externo

Um terceiro agente encontrou uma pista nova nos demos públicos da issue29 upstream: os vídeos mostram scores e relatórios finais sobre GSM8K/AIME. Esta evidência é mais concreta do que o log de utilização do componente. Continua sem revisão executável confirmada, saídas por pergunta ou ligação causal às falhas aqui demonstradas. São demos dos próprios autores e não uma conclusão independente afetada. Os originais, hashes e lacunas estão em `EXTERNAL_NEW_LEADS.json` e `external/PRIMARY_RETRIEVALS.json`.

## Próximos passos

1. Integrar o adaptador validado e a recusa de scores sem cobertura no percurso ordinário instalado. Conservar o modo de pontuação, a fonte e o denominador junto de cada resultado.
2. Executar um pequeno ensaio emparelhado com respostas reais para separar os efeitos de geração dos efeitos de pontuação. Reconciliar primeiro os acessos, recursos e limites registados. Comparar pergunta ligada + configuração antiga com geração e pontuação tipadas, sem trocar os casos; conservar respostas incompletas.
3. Integrar esta consequência e os contraexemplos nas mesmas identidades do manuscrito. Distinguir efeito medido em controlos, efeito em modelos e utilização externa.
4. Seguir a pista dos demos apenas se aparecer uma ligação primária nova à configuração e aos resultados originais. Não inferir falha a partir da diferença entre métricas.

O resultado reforça uma conclusão geral delimitada: verificar que os campos existem e que a execução devolve um número não demonstra que a tarefa ou o conjunto de casos pontuados foram preservados.
