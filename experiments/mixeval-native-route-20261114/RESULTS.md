# MixEval — integração e consequência em novas respostas

14 de novembro de 2026. Trabalho privado.

O ensaio com respostas novas confirma um efeito dependente do modelo. Nos mesmos20casos e com o mesmo avaliador, a correção do formato produz um ganho de50a75pontos percentuais no Qwen sob tratamento conservador das respostas incompletas. No Gemma, o intervalo de-5a+25pontos permanece inconclusivo.

## Ensaio emparelhado

O protocolo e a implementação foram fixados antes dos resultados. As20perguntas são as primeiras da ordemSHA256 já selecionada, com16TriviaQA,3DROP e1BBH. O conteúdo já era conhecido; as80respostas são novas. Os dois pedidos preservam a pergunta e o contexto. Binding-only mantém a instrução errada de escolha com o marcadorNone; o pedido tipado usa o construtor oficial de resposta livre. A intervenção muda o tipo de instrução e a formatação conjuntamente.

| Modelo | Binding-only, corretas/completas | Tipado, corretas/completas | Incompletas B/T | Ganho nos20pares |
| --- | --- | --- | --- | --- |
| Gemma | 11/18 | 12/16 | 2/4 | -5a+25pp |
| Qwen | 2/18 | 14/17 | 2/3 | +50a+75pp |

As frações sobre respostas completas são descritivas. O resultado principal usa os20pares por modelo, permitindo a cada resposta incompleta qualquer pontuação entre0e1. Estes intervalos são limites de sensibilidade no painel fixo, não intervalos de confiança populacionais. As mesmas20perguntas repetidas nos dois modelos não são40perguntas independentes.

O avaliador comum é o modo oficial opcional por regras, sem alteração retroativa nem chamadas a um juiz. As limitações desse modo continuam preservadas. Os resultados são pontuações atribuídas pelo avaliador explícito, não uma estimativa da capacidade geral dos modelos ou do modo oficial predefinido com juiz.

## Captura e recursos

Execução privada `ricardofitas/swarm-adaption-hackathon`, run43606982014, attempt1. Protocoloaf6a19b7a39643cc57d6dcf4fb1e7e9a1be319b6; análise comum38f2b3d556e0d5376cf14dfcb7e2b10db7f85075; lançamento676f3b618948253a9ff4f01f400e8ab1a2971a13.

Foram observadas80tentativas e80IDs de resposta únicos, sem reenvios. Todas as80utilizações estão contabilizadas:8062tokens de entrada e66304de saída. O campo de custo soma0.057821010000000003215unidades, com moeda por confirmar. O catálogo confirmou os dois modelos fixados antes das chamadas. A cadência mínima observada é5.000076s e a concorrência é1.

As11respostas desconhecidas atingiram4096tokens, com estado internoincomplete e motivomax_output_tokens. O tipo do evento terminal SSE foiresponse.completed, incluindo nesses11casos. A captura e a análise verificaram também o estado da resposta, evitando transformar truncagem em resposta completa.

O arquivo original do Actions temSHA256410ff3c8ddc534e65c5056db49f4a3cc3ecd37344b12b969f710e29ef148830c, conferido antes da extração. `reviewer/REAL_GENERATION_VERIFICATION.json` e `REAL_TERMINAL_REVIEW.json` conferem fontes, emparelhamento, hashes, modelos, registos de chamadas, recursos e limites de sensibilidade por código separado.

## Integração na orquestração nativa

Uma experiência separada usa as49respostas públicas anteriores,17livres e32de escolha. Os módulos originais de `run_eval`, `generator.run`, `evaluator.run` e `FileStorage` são importados e executados. Os limites são explícitos: facades de importação isolam dependências opcionais, o fornecedor é uma reprodução local, e os métodos de pontuação delegam no adaptador oficial por regras. O retorno nativo continua diagnóstico, sem execução do estágio de métrica primária.

Os49casos mantêm13/17e20/32acertos, com zero chamadas a dependências opcionais. Dez controlos de associação/cobertura inválida são bloqueados antes do envio. Não são novas observações de precisão ou uma nova amostra independente.

A revisão preserva uma errata de proveniência: um campo do hash do código de pontuação sobrescreveu o rótulo destinado ao hash do registo em49capturas. Os resultados originais permanecem intactos. O verificador recupera e separa ambos os hashes a partir das fontes congeladas, sem alteração das pontuações. Existe um patch de metadados para execuções futuras, não aplicado ao código da experiência congelada.

## Reprodução

- `real-generation/` contém os80pedidos, as respostas originais, os registosSSE, o protocolo e a análise congelada.
- `integration/` contém módulos completos fixados, fronteiras declaradas, inputs, resultados e recibo de execução.
- `reviewer/` contém verificadores independentes, controlos e erratas. A verificação da integração passou também numa pasta nova, sem repetir o percurso nativo.
- `public-replay/CAPTURES.jsonl.gz` e `public-replay/input/SELECTED.jsonl.gz` preservam a ligação às fontes e respostas públicas anteriores.

Executar a análise local não envia pedidos. Não voltar a lançar o workflow nem repetir chamadas para reconstruir o pacote.

## Próximos passos

1. Auditar a interpretação das respostas e a dependência do avaliador por regras, com critérios fixos e amostragem que retenha erros e incompletas. Distinguir resposta factual, formato final e texto de raciocínio.
2. Testar transferência numa nova amostra ou configurações pertinentes, separando a mudança mínima de instrução das restantes diferenças de formatação. Fixar o protocolo antes dos resultados e alargar apenas se acrescentar evidência.
3. Fechar a integração com dependências instaladas e fornecedor real, mantendo as mesmas verificações de fonte, identidade, cobertura e estado terminal. A integração por reprodução não prova esta etapa.
4. Prosseguir impacto externo apenas perante uma nova ligação primária entre configuração executada, pedidos, saídas e conclusão afetada. Os demos existentes continuam evidência parcial.

O manuscrito v1.4 mantém os limites e contraexemplos. Nada foi submetido ou publicado externamente.
