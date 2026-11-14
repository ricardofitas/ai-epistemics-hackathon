# Transferência do verificador para Social IQa

O protocolo, adaptador e os dois verificadores foram congelados no commit832422aeb7429ba0dd29852c148a83514e940237 antes da aquisição das perguntas e da execução. Base de investigação23ad77201d59f241562268f2c7f881e3a62fb7ed. Não houve alteração de critérios, substituição de casos nem nova inferência.

Fonte oficial: allenai/social_i_qa, revisão8835ceb9141d7896d9d968634a9b21ae440e3ec5, arquivo AI2 socialiqa-train-dev.zip SHA256ee073914a0fc33265cfbcfc50ec20df9b2e07809c3f420f599138d1f394ef5c3. A amostra contém os100 primeiros registos do dev por ordenação SHA256 canónica do par pergunta/rótulo, num total de1954. Conservam-se fonte, rótulos, loader, seleção e resultados.

| Condição | Registos | v1 | v2 |
|---|---:|---|---|
| Contrato preservado |100|100 PASS|100 PASS|
| Permutação coerente |100|100 PASS|100 PASS|
| Distrator removido, resposta correta preservada |100|100 PASS|100 FAIL|
| Pergunta omitida |100|100 FAIL|100 FAIL|
| Contexto omitido |100|100 FAIL|100 FAIL|
| Prova da fonte ausente |100|100 PASS|100 INCOMPLETE|

São100 pares contexto/pergunta e100 contextos distintos,600 variantes condicionais, zero pedidos a modelos e zero erros. As funções locais de contagem foram chamadas400vezes no v1 e200 no v2; estas chamadas não representam inferência. As expectativas fixadas foram satisfeitas. A conferência separada reconciliou a fonte, a ordem, as referências, as variantes, os denominadores e os bloqueios.

## Limites

Os mecanismos de falha já eram conhecidos; a fonte é nova relativamente aos painéis documentados de desenvolvimento do verificador. A revisão de exposição excluiu PIQA porque já figurava num protocolo anterior. Não foi realizado um censo de hashes de todas as perguntas de todos os pilotos e executores privados. Por isso, não se afirma validação globalmente cega ou independente de todo o histórico.

Os contratos saudáveis e as alterações foram produzidos por um adaptador determinístico próprio; não se auditou aqui o comportamento nativo de um novo avaliador. A transferência de mecanismos construídos não mede prevalência nem sensibilidade a defeitos naturais. Não há medição de precisão de modelos ou impacto externo.

O campo histórico SUMMARY.independent_context_groups significa apenas contextos textualmente distintos; VERIFICATION.json explicita esta limitação. Distinção textual não prova independência estatística.

## Reprodução

Biblioteca padrão Python3; versões de runtime em RUNTIME.json. No diretório extraído:

    python verify_transfer.py

Este comando confere os resultados já preservados sem rede nem modelos. Para repetir a experiência, use uma cópia do pacote, porque o script sobrescreve os resultados:

    python run_transfer.py
    python verify_transfer.py

A repetição faz dois downloads públicos fixados e exige o checksum do arquivo oficial. Não altera o verificador e não usa modelos. PROTOCOL.json e EXPOSURE_LEDGER.json documentam seleção, âmbito e limitações. A fonte oficial e os resultados estão incluídos para que a verificação possa ser feita offline.
