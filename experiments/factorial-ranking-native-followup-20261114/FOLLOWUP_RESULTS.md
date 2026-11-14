# Integração nativa e robustez da comparação entre modelos

14 de novembro de 2026. Trabalho privado.

O ensaio factorial anterior conserva as suas 160 tentativas, 152 respostas completas e oito incompletas. A análise exploratória da pontuação por regras confirma a inversão entre Gemma e Qwen em todas as 256 atribuições binárias possíveis às incompletas. A inversão persiste nas sete combinações de exclusão das três fontes com ressalvas pré-registadas. São diferenças emparelhadas neste painel fixo de 20 perguntas por modelo. Os limites descrevem a sensibilidade às respostas desconhecidas.

O percurso instalado One-Eval/DataFlow foi executado com o cliente HTTP original e o avaliador nativo. As quatro novas chamadas ao Qwen terminaram completas. Nos dois casos da configuração original, o pedido continha `{{prompt}}` por resolver e o avaliador encontrou zero referências pontuáveis. O zero numérico está identificado como UNSCORABLE.

Nos dois casos corrigidos, o conteúdo final da API foi `Dance` e `Tony Blair`, ambos aceites pelas fontes. O cliente acrescentou raciocínio e tags ao texto entregue à métrica de correspondência exata escolhida para este diagnóstico, que atribuiu zero. A correção de engenharia copia o campo final estruturado da API para uma coluna declarada de previsão. Uma nova execução do mesmo avaliador nativo sobre as quatro respostas existentes atribuiu um a ambas as respostas corrigidas. Esta reprodução fez zero chamadas adicionais a modelos ou juízes.

O primeiro teste com respostas sintéticas terminou com falha do seu próprio controlo de IDs. O pandas converteu os IDs de texto para números, mantendo os valores. Os quatro percursos nativos e as suas métricas tinham sido executados. A reconciliação mantém os dados originais, aceita apenas igualdade exata após conversão dos IDs para texto e verifica os restantes campos. A execução real incorporou esse controlo antes das chamadas.

A validação nativa usa duas perguntas já conhecidas e uma métrica de diagnóstico explícita. A correção da coluna de previsão foi preparada após observar os resultados. O avaliador oficial MixEval com modelo juiz continua por executar. A pesquisa externa adicional não confirmou uma conclusão publicada afetada. O PR 63 do One-Eval já reconhecia correções de extração e pontuação e passou a destacar a métrica primária em julho de 2026. Esse antecedente entra no enquadramento da novidade.

O manuscrito atualizado e as fontes conservam as identidades anteriores.

- [Manuscrito](https://chatgpt.com/library?file_id=libfile_fde3_f-a76d9b19be288191a854f8f165586de6_198492b795908191b811098f9e84ee4a&account_id=personal)
- [Fontes do manuscrito](https://chatgpt.com/library?file_id=libfile_fde3_f-f50f5bc8b29c8191af8d18de82eb6222_198492b795908191b811098f9e84ee4a&account_id=personal)
- [Ensaio factorial e adjudicação completa](https://chatgpt.com/library?file_id=libfile_fde3_f-907d451c4c588191b5f88a9c362a86d9_198492b795908191b811098f9e84ee4a&account_id=personal)

## Reprodução sem novas chamadas

O pacote contém os quatro arquivos originais autenticados, os verificadores, a análise de robustez, os recibos de execução e o seguimento externo. O gráfico está em `ranking_analysis/instruction_carrier_interaction.png`.

Num ambiente Python com NumPy disponível, executar o comando seguinte. O programa extrai os arquivos para uma pasta temporária nova e executa as verificações sobre essas cópias.

```bash
python3 reproduce_followup.py
```

Os scripts dos percursos instalados estão conservados nos arquivos originais. As contagens de chamadas nos relatórios referem-se às execuções arquivadas. Os dados e as classificações da revisão das 152 respostas encontram-se no pacote separado do ensaio factorial, ligado acima. A aritmética da pontuação por regras, a revisão factual por assistentes e a métrica nativa de diagnóstico têm resultados próprios.
