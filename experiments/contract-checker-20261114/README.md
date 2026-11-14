# Verificação de contratos de avaliação

Este pacote verifica o vínculo da pergunta e do contexto ao texto enviado, a presença da resposta correta nas opções, a preservação da referência oficial e conflitos entre rótulos de textos idênticos. O verificador funciona com a biblioteca padrão de Python e pode ser colocado antes de uma função de geração.

## Resultados desta etapa

| Grupo | Configurações | Resultado esperado observado |
| --- | ---: | --- |
| One-Eval com as falhas já documentadas | 7 | 7 `FAIL` |
| One-Eval original, controlo MedMCQA | 1 | 1 `PASS` |
| One-Eval com a correção por origem | 7 | 7 `PASS` |
| EvalScope original | 6 | 6 `PASS` |

São 21 configurações e 64 119 registos, com perguntas reutilizadas nas variantes original e corrigida. Este painel foi construído a partir das falhas conhecidas e dos controlos anteriores. Os resultados verificam regressões nesse painel. A precisão do verificador em tarefas novas permanece por medir.

No WinoGrande de validação, o verificador identifica 628 referências alteradas, 1 267 perguntas sem influência no texto e 300 grupos de textos iguais com rótulos oficiais diferentes. Calcula os mesmos 309 erros determinísticos inevitáveis obtidos pela análise independente anterior. No SciQ, identifica seis referências inválidas ou alteradas, 884 contextos exigidos pelo template sem influência e o facto de a primeira posição ser correta em todas as perguntas. No LAB-Bench, assinala a ausência da resposta correta nas 33 perguntas.

O gate foi exercitado nas 21 configurações com um backend de contagem. Nas sete configurações rejeitadas, o backend teve zero invocações. Cada configuração aprovada efetuou uma invocação com a lista de textos esperada. Foram também executados 15 testes de regressão, incluindo rótulos com valor zero, opções com texto repetido, avaliação livre de PubMedQA, verificações ausentes e preservação dos argumentos da função de geração. Esta etapa fez zero pedidos novos a modelos.

## Execução

O comando seguinte grava e apresenta o relatório do caso original.

```bash
python check_contract.py panels/oneeval__winogrande__validation.jsonl.gz --output resultado.json
```

O código de saída é 0 para `PASS`, 1 para `FAIL` e 2 para `INCOMPLETE`. A configuração original produz `FAIL`. A configuração corrigida abaixo produz `PASS`.

```bash
python check_contract.py panels/repaired__winogrande__validation.jsonl.gz --output corrigido.json
python -m unittest discover -s . -p test_contract.py
```

Para integrar a verificação numa avaliação local com referências disponíveis, o adaptador prepara os registos e as suas provas de transformação. A função `generate` recebe a lista de textos somente depois de o conjunto passar.

```python
from check_contract import guarded_inference

respostas = guarded_inference(registos_normalizados, generate)
```

`guarded_inference` devolve o resultado de `generate` sem o alterar. Uma falha ou verificação incompleta levanta `InvalidContract`, cujo atributo `report` contém o diagnóstico. Um teste cego que dependa de pontuação num servidor externo exige um adaptador próprio para esse protocolo. O esquema deste pacote destina-se a verificar avaliação local com respostas oficiais disponíveis.

## Esquema dos registos

Cada linha JSON representa uma pergunta dentro de uma única configuração. `schema_version` é 1 e `row_id` identifica a linha nesse conjunto.

| Campo | Conteúdo |
| --- | --- |
| `kind` | `choice` ou `freeform` |
| `prompt` | Texto visível efetivamente produzido pelo avaliador |
| `choices` | Opções efetivamente apresentadas, ou `null` em resposta livre |
| `correct_text` | Resposta oficial da origem, ou `null` quando indisponível |
| `expected_reference` | Rótulo oficial alinhado com a ordem apresentada, ou veredito canónico na resposta livre |
| `reference` | Referência normalizada pelo avaliador real |
| `question_probe_changed` | Resultado medido de substituir a pergunta por um valor sentinela, conservando os restantes campos |
| `context_required` | Se o contrato declarado exige o contexto fornecido |
| `context_probe_changed` | Resultado da substituição do contexto quando exigido |

Uma prova de transformação ausente produz `INCOMPLETE`. O adaptador precisa de obter as respostas oficiais e as provas a partir do código e dos dados que estão a ser avaliados. O verificador depende dessa proveniência. Uma posição correta constante é assinalada para revisão, uma vez que uma distribuição de classes desequilibrada pode ser intencional.

Os adaptadores fornecidos reexecutam os métodos fixados de pré-processamento e de formatação do One-Eval e conferem os hashes dos textos contra a captura anterior. Para o EvalScope, reutilizam as amostras e as provas de mutação medidas na instalação original. O código de geração do EvalScope foi executado na etapa anterior. Esta etapa volta a verificar os seus dados capturados. Os contextos opcionais do SciQ no EvalScope são tratados segundo o template desse avaliador.

## Procura de uma utilização externa afetada

A extensão da procura examinou as três outras branches públicas do One-Eval, os seis workflows públicos listados e os seus artefactos, referências indexadas ao repositório e um projeto que usa a sua galeria como referência. Os workflows listados são revisões de código e não disponibilizaram artefactos de avaliação. As outras branches não continham os tipos de registos de execução procurados.

O projeto `OrangeViolin/01fish-llm-radar` declara uma comparação de 19 modelos. O seu código implementa os próprios loaders, prompts e pontuação e cobre sete benchmarks diferentes dos casos auditados aqui. O README indica que as respostas e relatórios ficam numa pasta local. Os ficheiros correspondentes estão no `.gitignore` e não foram encontrados nas duas revisões públicas do projeto. Há evidência de uso externo da galeria. Uma execução afetada pelas falhas específicas deste estudo continua por verificar. [Projeto externo](https://github.com/OrangeViolin/01fish-llm-radar/tree/2a3c915665514a2b7f2ccd1068047c4d176ba841)

`EXTERNAL_EVIDENCE.json` conserva os locais consultados, revisões, hashes de fontes, candidatos excluídos e limites da procura. A frequência de utilização privada ou local permanece desconhecida. Não foram enviadas mensagens, issues ou PRs a terceiros.

## Reprodução e âmbito científico

`replay_validation.py` repete os 21 comandos públicos sobre os registos fornecidos e verifica os relatórios, códigos de saída e decisões do gate. Usa somente a biblioteca padrão. `verify_panels.py` acrescenta a comparação com as contagens independentes anteriores quando essa captura existe. `build_snapshot_panels.py` regista a preparação dos dados e permite regenerá-los na estrutura dos pacotes anteriores, com pandas e NumPy.

A linha agora contém uma auditoria causal, 200 pedidos reais do ensaio anterior, limites para respostas desconhecidas, um controlo noutro avaliador e uma intervenção verificável. Uma contribuição de investigação sobre estes mecanismos pode ser desenvolvida com essa evidência. A demonstração de uma conclusão externa alterada acrescentaria evidência de impacto. A generalidade da ferramenta precisa de uma avaliação prospetiva em novos contratos, escolhidos antes de se conhecerem os resultados.

[Auditoria One-Eval](https://chatgpt.com/library?file_id=libfile_c7f1d74116248191ba0a1c6d0c0e79b1&account_id=personal) · [Controlo EvalScope](https://chatgpt.com/library?file_id=libfile_b02b93d19548819196828b7c31a83eb4&account_id=personal) · [Ensaio de 200 pedidos](https://chatgpt.com/library?file_id=libfile_2f29df619b388191a07e8e4904ae1e60&account_id=personal)
