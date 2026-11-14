# WinoGrande: perda verificável de identificabilidade no pedido nativo

Auditoria privada iniciada em14-11-2026. Não altera o ensaio em curso, o manuscrito nem a folha humana. Zero novas chamadas a modelos ou juízes; nenhuma resposta dos ensaios ativos foi lida nesta etapa.

## Avanço efetivo

Autenticámos os dois artefactos de desenho publicados pelos jobs em curso, incluindo o recibo da instalação e do gate HTTP local WinoGrande. O gate original declara10136 pedidos nativos comparados com o manifesto antes de chamar fornecedores. Isso confirma a passagem do gate segundo os recibos; não é uma repetição independente da instalação nem prova de respostas reais já completadas.

A conferência independente do desenho preservado encontrou21336 IDs únicos:10136WinoGrande,9600do verificador e1600do suplemento. Cada célula WinoGrande modelo×braço contém1267perguntas, e cada configuração prospetiva contém200perguntas×4modelos. Os1600pares de contexto ligam corretamente IDs, modelos, linhas e hashes dos pedidos. Nenhum desses pares reutiliza payload literalmente idêntico: são1600pedidos adicionais planeados. Não confundir estas contagens do desenho com chamadas efetivamente enviadas ou concluídas.

## Consequência estrutural adicional

| Braço WinoGrande | Perguntas | Pedidos distintos por modelo | Grupos com ouro incompatível | Erros mínimos de uma função determinística do pedido | Máximo atingível dessa função |
|---|---:|---:|---:|---:|---:|
| Galeria original, enunciado ausente |1267|895|300|309|958/1267=75,6117%|
| Enunciado ligado, mesmas fontes/opções |1267|1267|0|0|1267/1267=100% como limite, não desempenho previsto|
| Original, excluindo o painel anterior |1255|890|296|305|950/1255=75,6972%|
| Corrigido, excluindo o painel anterior |1255|1255|0|0|1255/1255=100% como limite|

Há655perguntas em grupos contraditórios no painel completo. Os valores são iguais nas quatro famílias porque recebem o mesmo desenho textual; não são quatro descobertas independentes. A conferência agrupa o payload inteiro, incluindo modelo, sistema, mensagens e parâmetros, não só uma string de pergunta. Fontes e ouro são idênticos entre os braços; a correção apenas restaura o enunciado.

Prova curta: para um grupo de pedidos idênticos com nA respostas corretasA e nB corretasB, uma função determinística do pedido só pode escolher a mesma resposta; acerta no máximo max(nA,nB). Somar esse máximo sobre os grupos dá958, e escolher a maioria em cada grupo atinge o limite. A mesma desigualdade vale para a exatidão esperada de uma distribuição de respostas idêntica dentro de cada grupo. O princípio matemático é conhecido; não reivindicamos um novo teorema.

**Este não é um limite rígido de uma realização finita de respostas estocásticas.** Também não se aplica se o sistema receber índices, IDs, estado ou outros canais além do pedido. Não significa que os modelos atinjam100% após a reparação, nem que qualquer ganho observado lhes aumente a capacidade. O ensaio real permanece necessário para medir o efeito.

Esta perda de informação é distinta da referência numérica1/2 interpretada sempre comoB. Corrigir só a referência restaura a verdade da pontuação, mas não devolve o enunciado ao modelo. As duas falhas devem ser separadas nos resultados dos mesmos outputs, como prevê o protocolo principal.

## Verificação e limites

Protocolo secundário242717533e2b9642ded15adae53387013bc7d437 fixado antes do cálculo e de este executor ler outputs, mas depois do lançamento de inferência. O operador conhecia os12casos anteriores, a calibração de1267fontes e inspecionou as duas primeiras linhas do manifesto. Não é uma hipótese globalmente cega nem substitui as análises primárias.

A implementação independente usa ordenação dos bytes canónicos do payload e agrupamento, em vez dos hashes e dicionários do analisador principal:16coortes e dois digests de ZIP passaram. Os recibos nativos são autenticados como artefactos do job; os corpos capturados no loopback não estão neste artefacto congelado, só os seus digests. A comparação independente corpo-a-corpo do loopback continua dependente do artefacto final. Não foi executado código de inferência, instalação ou geração nesta revisão.

Na observação final desta etapa, os dois jobs estavam em inferência e só publicavam os artefactos congelados; nenhum total de respostas/custo estava verificável. Os logs ativos não estavam disponíveis pela API(404BlobNotFound), sem inferir falha do job. Limites dos estudos:60créditosWino/40verificador, quatro pedidos concorrentes em cada job segundo a política original; não são recursos novos lançados por esta revisão.

Folha humana v1:64classificações ainda vazias; lida e preservada. Manuscrito/PDF/sourceZIP sem alterações. PromptPG negativo e os resultados anteriores intactos. Isto acrescenta uma consequência analítica do pedido natural, não prova superioridade ao GAMMAF nem impacto num ranking histórico.

## Próxima passagem

1. Recolher os artefactos por ondas e terminais dos runs43655191625 e43655344258 sem relançar os manifestos.
2. Reconciliar intents/attempts/terminais/custos e retries429 antes de resultados científicos. Autenticar o analisador final fixado no checkpoint, não a versão supersedida.
3. Conferir o gate e o replay nativo das respostas reais no artefacto final. Relatar efeitos de referência e de presença do enunciado separadamente, com unknowns e exclusão dos12casos prévios.
4. Usar a partição de pedidos contraditórios como descrição pré-output do mecanismo. Não usar75,61% como limiar de aprovação/reprovação de resultados estocásticos.
