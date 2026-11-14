# Referências numéricas: transferência refutada, correção dependente da fonte

14-11-2026. Investigação privada. Protocolo 64b385487ecc51b3a9fdd818cb4cb03325c13656 fixado antes de adquirir linhas; implementação escrita após a aquisição, antes da primeira análise. Não é validação globalmente cega: galeria, parser e excertos dos cartões já vistos; exposição anterior da família não excluída. Sem novas respostas de modelos, juízes, execução CLI ou alteração do manuscrito.

## Resultado útil

A regra que colapsa as referências 1/2 de WinoGrande **não pode ser corrigida globalmente tratando todas as referências numéricas como índices a partir de 1**. A convenção pertence à representação exata adquirida, não apenas ao nome do benchmark ou ao cartão textual. Esta é uma delimitação de generalidade e um controlo de uma correção; não uma nova descoberta de pontuação incorreta de modelos.

| Preset e fonte fixada | Verificação de referência original | Conversão global a partir de 1 |
|---|---|---|
| MedMCQA, validation, HF 91c6572c454088bf71b679ad90aa8dffcd0d5868 | 4183/4183 concordantes com ClassLabel a,b,c,d armazenado 0–3 | 4183/4183 deslocadas ou inválidas; controlo hipotético de reparação, não configuração publicada |
| MedConceptsQA, all/test, HF 98c30d83762e51a397c9a7b0eeee6722e751da17 | 819719/819719 concordantes com correspondência única entre answer e opções; 53/819772 ambíguas e não adjudicadas | Não aplicável: answer_id já é A–D |

Não são resultados de exatidão de modelos, nem duas amostras independentes de defeitos. A varredura integral é uma conferência finita dos dois contratos selecionados por estrutura. Não estima prevalência noutras fontes.

## Evidência e fronteira

One-Eval 8aba20ad17ee2c7d2391162ac03ffaebcbb17506, ChoiceLetterParser blob aabfa6eb1ff0d24db6ef0c358a504b5db0db7f76, importado sem alteração, com configurações originais da galeria. Base blob79c84b4f5b44d7b26397ba1825fcb1e06da83024. Usámos apenas a componente de parsing de referência; nenhuma alegação de geração, métrica completa ou transporte nativo saudável decorre daqui.

No MedMCQA, tanto o esquema ClassLabel embutido no Parquet como os features do cartão declaram índices0–3. O texto mais abaixo do mesmo cartão diz1–4. O carregador original dos autores, em medmcqa/medmcqa@c59ef14ca1990266c4107c7864b45a20fd93e5e0/dataset.py, subtrai1 ao cop dos seus dados originais. Não transportar essa transformação para o Parquet já recodificado. A concordância verificada aqui é com o esquema declarado do ficheiro, não uma nova adjudicação clínica de cada alternativa.

No MedConceptsQA, a comparação independente usa answer e as quatro opções, sem usar answer_id para escolher a resposta. Normalização fixada: espaços e casefold. Os53 casos sem correspondência única ficam UNKNOWN, mesmo que um rótulo possa apontar para um dos textos repetidos. O criador histórico dos autores contém uma entrada repetida no dicionário de letras; não inferimos daí que os ficheiros publicados estejam afetados: a conferência dos ficheiros fixados não encontrou discordâncias identificáveis.

Os três Parquet foram adquiridos por URL de revisão imutável; bytes e SHA256 conferidos contra tamanho e OID LFS publicados. A verificação separada independent_verify.py não importa o parser nem o analisador principal e reconcilia todos os denominadores e ambiguidades. É uma segunda implementação pelo mesmo executor, não reprodução por investigador externo. Python3.12 e pyarrow19.0.1. Download de dados:248994689bytes; esta despesa de aquisição não é crédito de inferência. Recursos:0chamadas/0juízes/0custo novo de API.

## Relação com a descoberta WinoGrande

A consequência b9c59ae5331a0175248b5afbc2c42648c0f8a57a permanece: corrigir só referências muda a comparação das mesmas24saídas. Não foi repetida. A evidência atual limita uma extensão indiscriminada desse mecanismo, não a refuta no WinoGrande. Não estabelece superioridade ao GAMMAF.

Próximo passo útil: fechar o percurso comum do WinoGrande com configuração suportada, referências explícitas e captura do pedido efetivamente renderizado. Primeiro comparar os pedidos nativos aos pedidos das respostas arquivadas; se diferirem, não rotular as24saídas como geração nativa. Só depois definir uma validação separada de respostas reais, com protocolo e limites recuperados, se resolver essa lacuna. Não repetir os blocos fechados nem alargar inventários para produzir atividade.

Manuscrito/PDF/sourceZIP congelados. Folha humana v1 lida sem alteração:64campos de classificação vazios. PromptPG negativo e todos os limites dos resultados naturais anteriores preservados.
