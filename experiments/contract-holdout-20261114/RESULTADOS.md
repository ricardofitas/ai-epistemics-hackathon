# Validação prospetiva dos quatro contratos

Foram executados os quatro contratos escolhidos previamente, com 100 exemplos de teste por benchmark. O verificador manteve o SHA-256 `d833080f11b7bb3376056ca3a9720796a1181aa34749e6763a36d5fe1309d70e`. A seleção usou a ordenação SHA-256 de todos os registos oficiais de cada split. Os 27 746 registos de origem e os 400 exemplos selecionados ficaram capturados com hashes. Esta etapa efetuou zero chamadas a modelos.

| Benchmark | Exemplos | Primeira passagem | Diagnóstico após revisão |
| --- | ---: | --- | --- |
| ARC-Challenge | 100 | `FAIL` em 100 | Opções aninhadas transformadas em duas opções agregadas |
| OpenBookQA | 100 | `FAIL` em 100 | Mesmo problema nas opções e pergunta sem vínculo ao texto |
| MMLU | 100 | `PASS` | Passou os invariantes avaliados |
| MMLU-Pro | 100 | `FAIL` em 2 | Passou após corrigir o adaptador de comparação de espaços finais |

## Dois problemas de construção da tarefa

ARC-Challenge e OpenBookQA fornecem as opções como uma estrutura com listas `label` e `text`. O normalizador da versão auditada do One-Eval trata os dois valores desse dicionário como duas opções. A entrada apresentada fica com a lista inteira de etiquetas como opção A e a lista inteira de respostas como opção B. O mecanismo foi observado nas 100 perguntas de cada amostra. A resposta correta deixou de corresponder a uma opção individual apresentada.

No OpenBookQA, o template também mantém `{{question_stem}}` por preencher. Substituir a pergunta de origem por um valor sentinela não muda o texto enviado ao backend nas 100 perguntas. O problema foi reproduzido com os métodos originais de pré-processamento, formatação e geração.

No MMLU, as quatro opções, a pergunta e as referências oficiais ficaram preservadas nas 100 perguntas. No MMLU-Pro, a amostra contém perguntas com quatro a dez opções. Depois da revisão descrita abaixo, os invariantes passaram nas 100 perguntas.

## Correção de um erro do adaptador de auditoria

Na primeira passagem, o meu adaptador assinalou duas respostas do MMLU-Pro como ausentes. A inspeção mostrou que o normalizador nativo tinha removido apenas espaços exteriores. Por exemplo, a resposta oficial `$6,049 ` foi apresentada como `$6,049`. O conteúdo e a posição da resposta foram preservados.

Corrigi o adaptador da auditoria para aceitar essa operação somente quando a lista completa de opções apresentada corresponde, na mesma ordem, à lista oficial depois de aplicar `str.strip()` a cada opção. A regra foi aplicada aos 400 exemplos e corrigiu os dois falsos alertas. Os dois casos de opções agregadas continuaram a falhar. O ficheiro do verificador e todos os resultados da primeira passagem permanecem inalterados.

`choice_adapter.py` contém a correção. Os três testes de regressão verificam os dois casos observados, a preservação de índices em opções repetidas e a rejeição da agregação incorreta do ARC. `VERIFIED_REVIEW.json` conserva as duas passagens e os casos alterados. A segunda passagem é uma revisão posterior à observação dos resultados.

## Controlos de pontuação

| Benchmark | Controlo com letras oficiais no avaliador original | Controlo com referências e opções alinhadas |
| --- | ---: | ---: |
| ARC-Challenge | 98/100 | 100/100 |
| OpenBookQA | 100/100 | 100/100 |
| MMLU | 100/100 | 100/100 |
| MMLU-Pro | 100/100 | 100/100 |

Estes controlos fornecem ao avaliador respostas construídas a partir dos rótulos oficiais. Medem a implementação da pontuação. No ARC e no OpenBookQA, o controlo com letras oficiais não é um oracle viável da tarefa apresentada, porque a lista de opções foi alterada. O OpenBookQA consegue, assim, devolver 100/100 para um controlo de pontuação enquanto a entrada continua com pergunta por resolver e opções agregadas. O verificador inspeciona também essa construção da entrada.

A intervenção por origem preenche o campo correto da pergunta, preserva a lista completa de opções e usa uma referência canónica alinhada. As quatro configurações corrigidas passaram os controlos, com 400 referências pontuadas de 400 previstas. A comparação de pontuação generativa deste estudo tem a semântica descrita no protocolo. ARC e OpenBookQA identificam `acc_norm` nos seus metadados de referência, que é uma avaliação por probabilidades diferente deste controlo de geração de letras.

## Reprodução e âmbito

Os resultados aplicam-se ao One-Eval `8aba20ad17ee2c7d2391162ac03ffaebcbb17506` e ao gerador fixado de `open-dataflow==1.0.10`. Os métodos são originais, com o mesmo carregamento isolado de dependências já documentado nos ensaios anteriores. O backend de geração foi substituído por um respondedor inerte. A execução em Python 3.11.18 terminou com sucesso. Uma repetição offline em Python 3.12 reproduziu os quatro resultados originais.

Os ficheiros Parquet e JSONL capturados identificam os dados exatos usados. Foram registadas as revisões `main` e `refs/convert/parquet` observadas durante a recolha. Os endpoints públicos de Parquet podem resolver ficheiros dinamicamente; os hashes dos bytes capturados são a identificação imutável da amostra usada nesta análise.

Os quatro contratos foram escolhidos depois da calibração e antes da aquisição e da observação dos resultados. O painel mede uma extensão prospetiva dentro de um framework. A frequência de falhas noutros contratos ou em utilizações externas permanece por medir. Os dois falsos alertas iniciais mostram também uma limitação de adaptação de dados que foi corrigida nesta etapa.

Para verificar a seleção, a captura e as duas passagens, executar os comandos seguintes na pasta do pacote. Estes comandos usam a biblioteca padrão de Python.

```bash
python verify_and_review.py
python -m unittest discover -s . -p test_choice_adapter.py
```

`replay_native.py` repete a avaliação nativa num diretório temporário, preservando a captura original. Requer pandas 2.2.3 e NumPy 2.3.5. A reprodução usa os ficheiros fornecidos e não faz chamadas a modelos ou à rede.

```bash
python replay_native.py
```

[ARC-Challenge](https://huggingface.co/datasets/allenai/ai2_arc) · [OpenBookQA](https://huggingface.co/datasets/allenai/openbookqa) · [MMLU](https://huggingface.co/datasets/cais/mmlu) · [MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro)
