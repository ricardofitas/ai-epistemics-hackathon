# Reproduzir a auditoria de contratos predefinidos

Leia primeiro `default_contract_audit_20261113/RESULTS.md`. Os resultados atuais estão em `default_contract_audit_20261113/results/`.

O arquivo contém quatro capturas imutáveis com hashes, os métodos, a correção proposta, as verificações e o código mínimo de pontuação com licenças. Não é necessária uma chave de API para repetir a análise.

Use Python3.11, pandas2.2.3 e numpy2.3.5 para repetir o ambiente suportado verificado. A análise local em Python3.12 é registada separadamente; os ficheiros de resultados foram comparados com a reprodução em3.11. O código do framework é exercitado por um adaptador isolado documentado, sem instalar ou executar a aplicação completa.

Na pasta extraída:

```bash
python3 default_contract_bootstrap_20261113.py
python3 default_contract_audit_20261113/audit_contracts.py
python3 default_contract_audit_20261113/independent_source_audit.py
python3 default_contract_audit_20261113/verify_public_metric_cli.py
python3 default_contract_audit_20261113/validate_source_correction.py
python3 default_contract_audit_20261113/validate_prompt_correction.py
python3 default_contract_audit_20261113/verify_native_prompt_wire.py
python3 default_contract_audit_20261113/verify_model_capture.py
python3 default_contract_audit_20261113/analyze_model_smoke.py
```

Estes comandos analisam as respostas já capturadas e não fazem chamadas a modelos. Os métodos de execução das96 chamadas originais estão preservados em `model_smoke/`, com o protocolo congelado e bloqueios contra uma repetição acidental.

Os ficheiros `audit_contracts_initial_bare_labels.py`, `audit_contracts_before_truth_scope.py` e `results_initial_truth_scope/` são histórico de validação, não resultados finais. As duas alterações do adaptador de teste estão documentadas: usar as etiquetas de resposta pedidas pelo template para eliminar a ambiguidade de letras soltas; e distinguir a resposta correta num conjunto reparado de opções da resposta efetivamente disponível nas opções nativas. Nenhuma pergunta ou chamada a modelo foi removida por essas alterações.

Os controlos construídos não são resultados de modelos. O ensaio prospetivo com modelos usa o template pretendido renderizado diretamente; a auditoria do gerador nativo é separada. WinoGrande validation é um split diagnóstico explícito. PIQA não foi analisado após a falha de aquisição e GPQA não foi obtido através de autenticação ou espelhos alternativos. A frequência de uso real e a novidade científica não são estabelecidas por este pacote.
