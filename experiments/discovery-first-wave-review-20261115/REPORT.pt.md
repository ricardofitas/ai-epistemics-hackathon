# Discovery Lab: inferência real confirmada e primeiros desconhecidos

15-11-2026. Observação independente e só de leitura. Sem novas filas, alteração de marcadores, credenciais, manuscrito ou revisão humana.

## Estado efetivamente verificado

Os runs43669289975/43669289986 do commitba9f1864 falharam antes de inferência, segundo o registo do responsável. O diagnósticoGET43669425472 concluiu e publicou um artefacto; o sucesso desse job significa execução do diagnóstico, não sucesso de inferência.

A evidência atual do GitHub supera aquele ponto de partida: o responsável lançou os runs43670043810(WinoGrande) e43670043793(SIQA), no commit3ff2e9f289fb0bf268cdcb94417987b3dbf54404 de rfitas-lab/rfdl-lab-os. Esse commit aplica uma entrega cifrada efémera com contexto do run e manifestos fixos. Isto foi feito pelo responsável/supervisor, não por esta revisão. Não se usou o commit órfão2ccdf4f para mover HEAD, nem esta revisão interveio no segredo. Não incluir chaves, envelopes ou ficheiros de entrega no pacote de investigação.

Conferidos os artefactos congelados contra os digests do GitHub e os payloads contra os recibos. Os manifestos continuam exatamente:

- WinoGrande1024: b7374835790f312c2730a959079e379f6eb81006dc9cdaba361acd295fa077c8.
- SIQA3200: 1a0b6f7bf7eefa5ef6240289191df0295e5214b098403c0879cf3ebc69abe131.

Quatro famílias por estudo,256/800células por família, cap8192tokens por pedido, tetos30/70créditos e cutoff10:15UTC. Os recibos de payload ainda contêm rótulos históricos PREPARED_NOT_EXECUTED_GITHUB_BILLING_BLOCK; esses rótulos não descrevem o estado vivo. Também os RESULTS dos artefactos congelados, com todos os outputs desconhecidos, são análises de pré-inferência, não novos resultados.

## Vagas autenticadas das03:00

|Estudo|Intents distintos|Terminais|Completos|HTTP504|Em curso no snapshot|Não iniciados|
|---|---:|---:|---:|---:|---:|---:|
|WinoGrande,03:00:05|36|32|24|8|4|988|
|SIQA,02:59:59|37|34|26|8|3|3163|

Conferidos corpo do pedido e SHA256, trialID/attempt, ficheiro raw e igualdade com terminal, ID de resposta, modelo devolvido, statusstop, integridade de stream, uso e cap. Isto confirma50respostas reais completas; não foram contadas como inferência regressões locais ou recibos de catálogo. Não houve retries nestes snapshots, nem HTTP429. São acumulados iniciais, não o total final dos estudos.

Wino: oito respostas completas de Gemma, oito de GLM e oito de Qwen; oito HTTP504 de DeepSeek. SIQA: Qwen10completas, Gemma9, GLM7; DeepSeek6HTTP504, Gemma1HTTP504 e GLM1HTTP504. Esta concentração é um problema operacional a acompanhar, não evidência de qualidade inferior do modelo. Os16HTTP504 permanecemunknown e não autorizam reenvio cego. Credencial válida para respostas reais já existe; não pedir outra chave com base nos errosGET antigos.

A contabilidade spent_or_committed do executor é0,030774616créditosWino e0,070620506SIQA nestes snapshots; não é um extrato de faturação nem moeda confirmada. Reservas em curso continuam separadas. Custo de inferência desta revisão:0; chamadas novas próprias:0.

## Interpretação científica permitida

O contador operacional de12pares em cada fila refere-se a dois braços por item/modelo. Em WinoGrande, isso corresponde a seis unidades completas de par natural×modelo (quatro outputs por unidade), em dois pares naturais e só três famílias. Ainda existem zero pares naturais com todos os16outputs conhecidos. Não chamar a isto12pares naturais confirmatórios.

Recalculei a análise Wino com implementação persistida antes destes outputs em835aa41cf1e3ce33a93fda61a631f0d02c3e213c. A projeção contém apenas as24previsões nativas completas; todos os restantes outputs entram como desconhecidos. Os hashes de fonte e pedido e as duas flags do mesmo output são conferidos. Os limites planeados do contraste são[-192,96875,+197,65625]pp, exatamente iguais aos da análise original. O efeito condicional dos seis pequenos blocos observados não é resultado confirmatório: o intervalo planeado continua a incluirzero e nenhuma unidade completa de quatro famílias suporta ainda um IC.

SIQA tem um conjunto inicial de pares mecânicos, mas zero classificações semânticas dos dois leitores mascarados fornecidas no artefacto. Não converter acerto do extrator nativo em confirmação de uma resposta semanticamente expressa; a interpretação principal que exige leitores continua pendente. Dupla leitura por assistentes também não será revisão humana.

## Passagem

1. Monitorizar os mesmos runs; recolher as novas vagas cumulativas e seus digests, sem relançar manifestos ou tocar em credenciais.
2. Acompanhar a distribuição dosHTTP504 por família sem os imputar como erros de conhecimento ou os reenviar.
3. Conferir identidades/custos e unidades de análise antes dos contrastes; manter64pares fonteWino e400perguntasSIQA, com famílias agrupadas.
4. Não concluir sucesso, ganho universal ou competitividadeICML a partir destes snapshots. Preservar os controlos, negativos e53unknowns do estudo compacto já encerrado.
5. Corte de novosPOSTs10:15UTC; análise até12:31:35. Nenhuma mudança de prazo ou autorização financeira nesta revisão.

Os originais congelados e as duas vagas acumuladas revistas estão no pacote, sem artefactos públicos de troca de chave nem segredos. Folha humana v1:64campos ainda vazios, sem alteração. Manuscrito/PDF/sourceZIP intactos.
