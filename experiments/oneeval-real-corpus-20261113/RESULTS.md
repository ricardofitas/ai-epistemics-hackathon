# One-Eval: medição da falha em respostas reais

**13 de novembro de 2026.** A falha de equivalência entre `choice_accuracy`, `accuracy` e `acc` reproduz-se em respostas reais. Neste conjunto, o efeito nas respostas finais dos sistemas é pequeno: até **0,0711 pontos percentuais**, sem inversões de ranking. A evidência atual justifica uma correção e um resultado complementar; não sustenta uma descoberta com impacto superior ao GAMMAF.

## Conjunto e seleção

Foram usados os 21 ficheiros públicos do GAMMAF, revisão `53be3249ebfa631d8e960c9fb1c931d526654697`, correspondentes aos sete sistemas em CSQA, MMLU e MMLU-Pro. Todos os ficheiros foram escolhidos antes de observar os valores das respostas ou os efeitos dos aliases nesta análise. A captura verificou a identidade Git de cada ficheiro, e a verificação foi repetida localmente.

O protocolo de análise foi registado no repositório privado antes do cálculo dos resultados: commit `f7ad2229baff32c22c7364fb3c9eda79a985e3ec`. Houve inspeção prévia dos nomes e tipos dos campos para definir a seleção. Não foram feitas novas chamadas a modelos.

Dos 25.200 registos de rondas, selecionou-se a última ronda real, não preenchida artificialmente, de cada par topologia/pergunta. Os 6.672 registos marcados `padded` não são novas respostas. O conjunto principal contém **8.400 respostas finais**, 400 por sistema e benchmark. O conjunto secundário contém **84.000 respostas individuais dos agentes** dessas mesmas rondas, incluindo agentes maliciosos. Este segundo conjunto é descritivo e não mede apenas a qualidade dos agentes benignos. As perguntas e topologias são partilhadas entre sistemas; estes totais não são números de observações independentes.

Não se filtrou pela correção, pelo campo `included` ou pela presença de respostas inválidas. Nenhuma resposta final selecionada tinha `included=false`. Os identificadores de grupos e as respostas de referência coincidem entre os sete sistemas de cada benchmark.

## Efeito medido

| Conjunto | Respostas | Respostas sem opção extraível ou vazias | Maior alteração absoluta | Pares com inversão estrita |
|---|---:|---:|---:|---:|
| Respostas finais dos sistemas | 8.400 | 18 | 0,0711 pp | 0 |
| Respostas individuais dos agentes | 84.000 | 8.458 | 0,0671 pp | 1 |

Os máximos abrangem a ordem original e dez permutações fixadas por SHA-256, com 1, 2, 4 ou 8 processos. Na ordem original, o maior efeito nas respostas finais foi **0,0700 pp**, em TAM/MMLU-Pro com oito processos. Não houve referências inválidas em nenhum dos dois conjuntos. No secundário houve 8.338 falhas de extração e 120 respostas vazias.

A única inversão de par ocorreu em **TAM versus XG-Guard, nas respostas individuais dos agentes em MMLU**, usando o denominador `valid_only`. Na ordem original, com oito processos:

| Sistema | Nome canónico | Alias `accuracy` |
|---|---:|---:|
| TAM | 68,972169% | 68,984759% |
| XG-Guard | 68,976808% | 68,939750% |

A diferença original é de apenas **0,004639 pp**. Foram encontradas seis combinações de número de processos/ordem que invertem este mesmo par e alteram o primeiro lugar do conjunto secundário. São **seis configurações da mesma comparação**, não seis descobertas ou replicações independentes. Não foi observada qualquer inversão nem mudança do conjunto vencedor no resultado principal dos sistemas.

Todas as alterações de pontuação e inversões observadas ocorreram com `valid_only`. Os controlos com denominador `total` e a rota dedicada `run_bench_with_contract` mantiveram a pontuação. A correção de despacho por identidade da função também restaurou a pontuação e a informação sobre o denominador nos casos verificados.

## Verificação e exposição

A reprodução usa o código público do One-Eval, revisão `8aba20ad17ee2c7d2391162ac03ffaebcbb17506`, com os mesmos adaptadores de importação documentados no pacote anterior. Foram verificadas **1.848 invocações reais** das rotas de cálculo originais, corrigidas e de controlo. Os **11.088 resultados de configuração** foram calculados pela redução exata dos grupos; as permutações verificadas por execução efetiva estão identificadas separadamente. Uma implementação independente com aritmética racional confirmou os 11.088 resultados e as 11.088 comparações de pares. Mais 12 invocações diretas confirmaram os exemplos extremos depois da análise. Esta auditoria aritmética não valida, de forma independente, a interpretação linguística do parser.

A galeria pública contém 121 benchmarks e 111 contratos com métrica principal. Os **111 usam `denominator=total`**; os 49 contratos de escolha múltipla usam o nome canónico `choice_accuracy`. O menu dinâmico fornecido ao recomendador também apresenta o nome canónico e não enumera aliases ou argumentos desta métrica. A documentação da interface de métricas refere os aliases, e a configuração explícita do utilizador pode encaminhar argumentos para a rota afetada. Isto estabelece a existência de uma configuração suportada, mas não a sua frequência em utilização real.

Estes resultados são uma reprodução controlada de respostas reais do GAMMAF através do One-Eval. **Não demonstram que os autores do GAMMAF usaram One-Eval nem que os seus relatórios originais sofreram esta falha.** A pesquisa dos títulos e descrições de 67 issues/PRs e duas pesquisas dirigidas não identificou uma descrição correspondente; isso não prova novidade científica.

## Decisão científica

O resultado principal é negativo quanto a uma consequência material neste conjunto: não há inversão no ranking dos sistemas e a maior alteração fica abaixo de 0,1 pp. A inversão secundária ocorre entre sistemas praticamente empatados. A combinação afetada não aparece nos contratos predefinidos inspecionados. Por isso, esta linha fica como correção técnica e evidência complementar, sem novas baterias extensas de chamadas a modelos por agora.

O exemplo construído anterior continua válido como demonstração da gravidade possível: a pontuação de um sistema passa de 98,0769% para 50,4950% ao mudar apenas o alias, com duas unidades de processamento. O ensaio atual acrescenta a medida do efeito observado em dados reais e limita a interpretação desse exemplo.

O próximo avanço com maior valor deve procurar uma falha de avaliação num percurso realmente usado e verificar a consequência numa conclusão científica preexistente. O critério de promoção é: fonte e configuração reproduzíveis, alteração relevante face à incerteza da comparação, controlo causal e correção que elimina o efeito. Uma diferença de pontuação em perguntas demasiado fáceis, ou uma inversão entre resultados quase empatados, não basta para promover um candidato acima do GAMMAF.

## Reproduzir

O arquivo inclui a captura original imutável, o código mínimo do One-Eval e dependências com licenças, os protocolos, o parser por linha, todas as comparações e as verificações. Na pasta extraída:

```bash
python3 oneeval_real_corpus_20261113/analyze_real_outputs.py
python3 oneeval_real_corpus_20261113/independent_arithmetic_audit.py
python3 oneeval_real_corpus_20261113/verify_selected_extrema.py
```

Fontes: [GAMMAF, revisão analisada](https://github.com/pmateo-uc3m/GAMMAF/tree/53be3249ebfa631d8e960c9fb1c931d526654697) e [One-Eval, revisão analisada](https://github.com/OpenDCAI/One-Eval/tree/8aba20ad17ee2c7d2391162ac03ffaebcbb17506).
