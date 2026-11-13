# One-Eval e o próximo ensaio do Epistemics

O One-Eval continua a ser a prioridade de investigação do Epistemics. O GAMMAF mantém a vantagem em impacto externo demonstrado. Na reanálise dos registos divulgados pelos autores do GAMMAF, o controlo sem defesa em MMLU recebeu 8% de crédito na terceira ronda, apesar de os registos mostrarem zero deteções. No One-Eval já conseguimos quantificar exatamente quanta informação um modelo perde ao receber um prompt incompleto. Continua por demonstrar que uma utilização independente produziu uma decisão afetada.

## Efeito de apagar a pergunta

Usámos a validação do WinoGrande, que disponibiliza os rótulos oficiais das 1 267 perguntas. Este é um diagnóstico com escolha explícita da validação. A configuração predefinida do One-Eval seleciona o teste, cujos rótulos são vazios. Verificámos pergunta, opções, rótulo e ordem entre os dois avaliadores. Recuperámos os textos originais da versão auditada do One-Eval e confirmámos os 1 267 hashes registados na auditoria anterior. O controlo EvalScope usa os textos capturados no avaliador instalado.

| Texto apresentado | Textos distintos | Grupos com respostas oficiais contraditórias | Erros inevitáveis | Máximo possível no conjunto |
| --- | ---: | ---: | ---: | ---: |
| One-Eval original | 895 | 300 | 309 | 958/1 267 = 75,61% |
| One-Eval com os campos da origem preenchidos | 1 267 | 0 | 0 | 1 267/1 267 = 100% |
| EvalScope original | 1 267 | 0 | 0 | 1 267/1 267 = 100% |

Ao responder sempre da mesma forma ao mesmo texto, o maior número de acertos em cada grupo é o número de ocorrências da opção oficial mais frequente. Somámos esses máximos para obter o limite. Os 300 grupos contraditórios abrangem 655 perguntas. Assim, com as referências oficiais já corrigidas, o gerador do One-Eval ainda impõe 309 erros a qualquer regra determinística que só veja o prompt. O limite de 100% nas outras duas condições significa que esta fonte de erro desapareceu. A precisão dos modelos nessas condições requer inferência. Esta análise é exploratória e refere-se a este conjunto finito.

## Utilização real

A busca incluiu o repositório de origem, os 67 itens públicos devolvidos pelo registo de issues e PRs, as árvores das branches predefinidas de 26 forks públicos confirmados e pesquisas de código por campos dos resultados. Não encontrámos uma execução de terceiros com versão, configuração efetiva e resultados individuais que demonstre o efeito. Este inventário mede o alcance da busca. O número total de utilizações permanece desconhecido.

O artigo dos autores descreve um exemplo de utilização do sistema. A experiência de 100 pedidos da secção 4.2 termina antes da avaliação dos modelos. As pontuações de referência no repositório vêm de fontes externas e não fornecem previsões originais produzidas pelo One-Eval. O ficheiro `public_exposure_search.json` regista os critérios, resultados e revisões consultadas. [Artigo dos autores](https://arxiv.org/html/2603.09821v1#S4)

## Experiência preparada

O painel tem 50 perguntas novas, distintas das usadas no piloto Adaption e sem reutilização de um texto nativo visto pelo piloto. Quinze pares têm o mesmo prompt original e rótulos opostos. As vinte perguntas de controlo têm prompts originais únicos. Ambos os subconjuntos equilibram os rótulos A e B. Esta seleção permite testar o mecanismo. A frequência das colisões deve ser calculada no conjunto completo.

O manifesto prevê 200 pedidos, resultantes de 50 perguntas, dois modelos e duas versões do prompt. O modelo recebe o texto produzido pelo gerador nativo e, numa chamada separada, o texto reparado. A ordem das opções e os parâmetros de inferência mantêm-se. A principal medida é a variação da precisão com os rótulos oficiais dentro de cada modelo e subconjunto. As respostas de cada condição também serão pontuadas pelos dois avaliadores do One-Eval, original e corrigido. As respostas incompletas entram nos limites de incerteza. Os pares que partilham o prompt são analisados em conjunto. O manifesto está congelado e ainda não foi executado.

Uma execução externa com resultados recuperáveis permitiria repetir a pontuação antes e depois da correção e identificar uma decisão concreta. Entretanto, o ensaio controlado pode medir o efeito nos modelos e a eficácia da correção. O EvalScope fornece o controlo em que os testes devem passar quando transformarmos esta auditoria numa verificação reutilizável.

## Verificação

Depois de descompactar, `python verify_result.py` verifica os textos capturados, as contagens e o manifesto com a biblioteca padrão de Python. `analyze_prompt_collisions.py` regista como as capturas imutáveis foram processadas. Para refazer essa etapa, usar a estrutura dos dois pacotes anteriores e o nome local `second_engine_contracts_20261113` para a pasta que contém `capture`. `prepare_confirmatory_panel.py` regista como se escolheram as perguntas antes de qualquer resposta nova de um modelo.

[Auditoria One-Eval](https://chatgpt.com/library?file_id=libfile_c7f1d74116248191ba0a1c6d0c0e79b1&account_id=personal) · [Controlo EvalScope](https://chatgpt.com/library?file_id=libfile_b02b93d19548819196828b7c31a83eb4&account_id=personal) · [Reanálise GAMMAF](https://chatgpt.com/library?file_id=libfile_9799f917bfa88191a60fabc51e8beb3e&account_id=personal)
