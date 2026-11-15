# WinoGrande confirmatório terminado; SIQA parcial — 15-11-2026

WinoGrande terminou com sucesso às03:51 UTC no run43670043810; SIQA permanece na mesma fila43670043793. Não foram lançadas chamadas, filas ou alterações de credencial por esta revisão. O manuscrito e a folha humana permanecem intocados.

## Resultado WinoGrande

Foram enviados os1024slots distintos previamente fixados:949respostas elegíveis e75HTTP504, conservados como desconhecidos. Houve1033tentativas devido a9HTTP429; as únicas repetições foram após429, nunca após504. Não há slots pendentes ou em voo no arquivo final. Existem463pares adjacentes item/modelo e32pares naturais completos nas quatro famílias, cada qual com16outputs. Estes denominadores são diferentes.

A interação principal previamente fixada é: **ganho ao restaurar o enunciado segundo a referência oficial, menos o ganho segundo a referência defeituosa original**. A unidade é a resolução correta dos dois membros de um par natural, mantendo o parser e as mesmas saídas para ambas as referências. Enumerar os valores possíveis de todos os outputs desconhecidos em todos os64pares planeados dá **[+48,828125,+79,296875] pontos percentuais**, com peso igual às quatro famílias. A recontagem por código separado, preparado antes destes outputs, coincide exatamente com a análise de produção.

Nos32blocos completos, a média condicional é+67,96875pp e o bootstrap por bloco condicional dá[+50,78125,+83,59375]pp. Este intervalo depende da disponibilidade; não substitui os limites do painel completo. Os limites não são um intervalo de confiança populacional nem medem ganho geral de capacidade.

Este resultado sustenta a previsão de mascaramento pelo contrato de referência neste painel finito. A seleção de pares, quatro famílias fixas e intervenção que restaura o enunciado delimitam o alcance. Não prova uma conclusão histórica de terceiros afetada nem superioridade sobreGAMMAF. A verificação independente de aritmética reutiliza a extração nativa congelada; não é adjudicação semântica humana.

## SIQA — snapshot03:50:08 UTC

594slots iniciados,592terminais distintos:500elegíveis,90HTTP504 e2HTTP200sem texto final;2em voo e2606não iniciados. As602tentativas incluem8repetições após429, sem reenviar504. Os502statusstop não são502respostas elegíveis: as duas respostas vazias mantêm-se desconhecidas apesar de statuscompleted e uso de tokens comunicado. Há230pares nativos adjacentes completos. **Zero classificações semânticas fornecidas**; nenhuma conclusão semântica primária nem evidência humana é declarada.

## Autenticação e reprodução

Execução imutável3ff2e9f289fb0bf268cdcb94417987b3dbf54404 em rfitas-lab/rfdl-lab-os. Manifestos b7374835…Wino e1a0b6f7b…SIQA conferidos integralmente; pedidos, modelos, hashes dos textos, estados, caps8192tokens e identidades intent/attempt/raw conferidos. Todos os1633registos de tentativa dos dois snapshots têm captura bruta correspondente e idêntica. Fonte→pedido e referência→pontuação são conferidos pelo analisador separado para949outputs Wino elegíveis.

Arquivo final Wino14145870067,121247166bytes,SHA256eaddd195b37732da72dce4a96ce573ffcb4ad9a7a38a951e21a9721ce70c8a39. A última vaga14145575877 tem o mesmo intent,attempts e ledger byte a byte; RESULTS difere apenas em analyzed_at_utc, progress muda os relógios; resultados primários e contagens terminais coincidem. O pacote retém esta vaga original cumulativa autenticada, a vaga SIQA14145074595 e os dois congelamentos originais; o ZIP final completo permanece no GitHub privado. Nenhum material de entrega de credenciais faz parte do pacote.

Contabilidade conservadora do executor:1,136332041créditos Wino;1,154082967SIQA no snapshot, com reserva SIQA0,00251804separada. Não são fatura final nem moeda confirmada. Caps30+70=100inalterados. Novos pedidos desta revisão:0; novos juízes:0. Apenas validações offline de artefactos já obtidos.

## Próximos passos

1. Não retomar Wino terminado nem os75HTTP504. Preservar arquivo e resultado finito; aguardar eventual conciliação do dono.
2. Observar apenas SIQA43670043793, autenticar vagas seguintes e no fim conciliar todos os intents/terminais; rótulos semânticos continuam uma lacuna separada.
3. Manter corte de novosPOST10:15UTC e consolidação até12:31:35UTC; nenhuma alteração ao manuscrito ou revisão humana.

`reproduce.py` permite refazer sem rede as verificações e limites a partir dos quatroZIPs incluídos. `SUMMARY.json`, `FINAL_ARCHIVE_RECEIPT.json` e `OBSERVATION_VERIFICATION.json` conservam denominadores, hashes e limites exatos.
