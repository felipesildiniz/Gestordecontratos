# DATABASE

SGBD: PostgreSQL (D-004). Acesso via Django ORM. Estado em 2026-10-03: **modelo lógico documentado na E3; nada criado no banco.**

Convenções: chaves primárias `id` (bigint); datas em `date`; carimbos em `timestamptz`; valores em reais como `numeric(15,2)`; toda tabela de negócio tem `criado_em` e `atualizado_em`. Legenda de obrigatoriedade: **CONFIRMADO** = dito pelo responsável como obrigatório; **OPCIONAL** = pode ficar vazio (campos complementares e também data de publicação, gestor e fiscal, confirmados como não obrigatórios).

## Usuários e perfis
Usa as tabelas padrão do Django (`auth_user`, `auth_group`). Perfis = grupos **Admin** (edita tudo, inclusive usuários) e **Consulta** (somente leitura). Não há tabela própria de perfil.

## Tabelas

### modalidade
| Campo | Tipo | Nulo | Observação |
|---|---|---|---|
| sigla | varchar(10) | não | única. Siglas informadas: INEX, AD, PE, CE, CH |
| nome | varchar(80) | não | nome por extenso (todos confirmados, ver carga inicial) |
| ativo | boolean | não | padrão verdadeiro |

Cadastro mantido pelo Admin. Carga inicial:
| Sigla | Nome | Situação |
|---|---|---|
| AD | Adesão de Ata | confirmado |
| CE | Concorrência Eletrônica | confirmado |
| CH | Chamada Pública | confirmado |
| PE | Pregão Eletrônico | confirmado |
| INEX | Inexigibilidade | confirmado |

"Ata de registro de preços" **não** é modalidade (ver "Fora desta etapa").

### contratado
| Campo | Tipo | Nulo | Observação |
|---|---|---|---|
| tipo_pessoa | char(2) | não | `PF` ou `PJ` |
| documento | varchar(14) | não | CPF ou CNPJ, só dígitos, único; validar dígitos verificadores |
| razao_social | varchar(200) | não | razão social (PJ) ou nome (PF) |

### agente
| Campo | Tipo | Nulo | Observação |
|---|---|---|---|
| nome | varchar(150) | não | pessoa que pode atuar como gestor, fiscal etc. em vários contratos |

### contrato
| Campo | Tipo | Nulo | Obrigatoriedade | Observação |
|---|---|---|---|---|
| sequencial | integer | não | **CONFIRMADO** | o "N°" que abre o número do contrato; **reinicia a cada ano** |
| modalidade_id | FK modalidade | não | **CONFIRMADO** | sigla que compõe o número |
| numero_modalidade | integer | não | **CONFIRMADO** | número da modalidade (faixa 1–100 informada) |
| ano | smallint | não | **CONFIRMADO** | ano do número |
| numero_formatado | varchar(30) | não | **CONFIRMADO** | número completo do contrato; **único**; montado pelo sistema a partir das 4 partes acima |
| data_assinatura | date | não | **CONFIRMADO** | |
| data_publicacao | date | sim | OPCIONAL | confirmado como não obrigatório |
| data_inicio_vigencia | date | não | **CONFIRMADO** | |
| data_fim_vigencia | date | não | **CONFIRMADO** | vigência final **vigente**; é a data usada nos alertas |
| data_fim_vigencia_original | date | não | **CONFIRMADO** | cópia da vigência final na assinatura; nunca muda |
| objeto | text | não | **CONFIRMADO** | descrição resumida |
| valor | numeric(15,2) | não | **CONFIRMADO** | em reais; não negativo |
| contratado_id | FK contratado | não | **CONFIRMADO** | |
| informacoes_complementares | text | sim | OPCIONAL | texto livre |
| envolve_saude | boolean | não | OPCIONAL | padrão falso |
| envolve_educacao | boolean | não | OPCIONAL | padrão falso |
| criado_por / atualizado_por | FK auth_user | | | autoria |

Restrições: `numero_formatado` único; (`ano`, `sequencial`) único, já que o sequencial reinicia a cada ano; `valor` ≥ 0; `data_fim_vigencia` ≥ `data_inicio_vigencia`; `data_fim_vigencia` ≥ `data_assinatura` (premissa a confirmar).

### contrato_agente (gestor, fiscal e responsáveis adicionais; todos opcionais no cadastro)
| Campo | Tipo | Nulo | Observação |
|---|---|---|---|
| contrato_id | FK contrato | não | |
| agente_id | FK agente | não | |
| papel | varchar(30) | não | `GESTOR`, `FISCAL`, `ASSINANTE`, `CONTROLADOR_ENCARGOS`, `SUPLENTE` |
| cargo | varchar(120) | sim | cargo no período (por isso fica aqui e não em `agente`) |
| data_inicio | date | não | início da responsabilidade |
| data_fim | date | sim | nulo = responsabilidade em curso; ≥ data_inicio |

### documento (arquivos PDF)
| Campo | Tipo | Nulo | Observação |
|---|---|---|---|
| contrato_id | FK contrato | não | |
| alteracao_id | FK alteracao_contratual | sim | para PDFs de aditivos, apostilamentos etc. |
| tipo | varchar(30) | não | `CONTRATO` (o PDF do contrato, contendo somente o contrato; no máximo um por contrato) ou `ALTERACAO` (PDF de aditivo, apostilamento etc., ligado a `alteracao_id`) |
| arquivo | varchar(255) | não | caminho no armazenamento do servidor |
| nome_original | varchar(255) | não | |
| tamanho_bytes | bigint | não | |
| sha256 | char(64) | não | detecta arquivo alterado ou duplicado |
| enviado_por / enviado_em | FK auth_user / timestamptz | não | |

**O PDF do contrato é obrigatório:** todo contrato precisa ter um documento do tipo `CONTRATO` (validado pela aplicação no cadastro, pois o arquivo fica em tabela separada). Consequência: o PDF do contrato só pode ser excluído para ser substituído por outro ou junto com o contrato inteiro (interpretação minha, a confirmar).

Somente PDF, **até 10 MB por arquivo** (decisão de 2026-10-03 que substitui a resposta anterior de "sem limite"). **Exclusão física:** ao excluir um PDF, o arquivo é apagado de vez do armazenamento e a linha de `documento` é removida; a auditoria registra quem excluiu, quando, o nome original e o `sha256`.

### dotacao_orcamentaria (OPCIONAL)
`contrato_id`, `ano` smallint, `descricao` varchar(255), `codigo` varchar(60). Vários por contrato.

### parcela_pagamento (OPCIONAL, cronograma)
`contrato_id`, `numero_parcela` integer, `data_prevista` date, `valor_previsto` numeric(15,2). Único por (`contrato_id`, `numero_parcela`).

### garantia (OPCIONAL)
`contrato_id`, `descricao` text. Valor e vencimento da garantia não foram pedidos; não modelados.

### item_contrato (OPCIONAL)
`contrato_id`, `numero_item` integer, `descricao` text, `unidade` varchar(20) nulo, `quantidade` numeric(15,3) nulo, `valor_unitario` numeric(15,2) nulo, `origem` (`LICITACAO` ou `MANUAL`), `referencia_licitacao` varchar(100) nulo. Único por (`contrato_id`, `numero_item`). Não existe entidade Licitação no sistema; a vinculação é uma referência em texto.

### alteracao_contratual (histórico de alterações; estrutura mínima, detalhar na E7)
`contrato_id`, `tipo` (`ADITIVO`, `APOSTILAMENTO`, `PRORROGACAO`, `RESCISAO`), `data_ato` date, `descricao` text, `nova_data_fim_vigencia` date nulo, `valor_alteracao` numeric(15,2) nulo (negativo em supressões). Registrar uma prorrogação atualiza `contrato.data_fim_vigencia`.

### log_auditoria (estrutura mínima, detalhar na E11)
`usuario_id`, `data_hora` timestamptz, `acao` (`CRIAR`, `ALTERAR`, `EXCLUIR`), `entidade` varchar(60), `entidade_id` bigint, `dados_antes` jsonb, `dados_depois` jsonb. Somente inserção: sem alteração nem exclusão de linhas.

## Relacionamentos
- modalidade 1—N contrato; contratado 1—N contrato.
- contrato 1—N contrato_agente N—1 agente.
- contrato 1—N documento, dotacao_orcamentaria, parcela_pagamento, garantia, item_contrato, alteracao_contratual.
- alteracao_contratual 1—N documento.
- Exclusão de contrato: o Admin pode excluir o contrato por inteiro (caso de cadastro errado). A exclusão é física e em cascata: apaga também agentes, dotações, parcelas, garantias, itens, alterações e documentos, inclusive os arquivos PDF. Antes de apagar, a auditoria guarda uma cópia dos dados do contrato e de seus filhos em `dados_antes`.

## Fora desta etapa
- **Alertas:** sem tabela. O nível (verde, amarelo, vermelho) é calculado na consulta a partir de `data_fim_vigencia` (D-013).
- **Ata de registro de preços e saldos:** a ata não é uma modalidade; ela complementa o Pregão Eletrônico (PE) e é nela que ficam os saldos consumidos pelos contratos. Será modelada na E8 (Atas e saldos). A ligação contrato–ata (e o consumo de saldo) ainda não existe no modelo. Ao excluir um contrato, o saldo que ele consumiu da ata deverá ser devolvido (regra a tratar na E8).

## Confirmado em 2026-10-03
Formato do número `sequencial.SIGLA.numero_modalidade/ano` (ex.: `1.PE.15/2026`), com sequencial reiniciando por ano; siglas AD, CE e CH; obrigatórios também objeto, valor, contratado e início da vigência; limites de alerta valem no dia exato. Em 2026-10-03 (segunda rodada): PE = Pregão Eletrônico e INEX = Inexigibilidade; ata de registro de preços não é modalidade; o PDF contém somente o contrato; publicação, gestor e fiscal não são obrigatórios; contrato pode ser excluído por inteiro; PDF limitado a 10 MB, com exclusão física.

## Pendências do modelo (não bloqueiam a E4)
1. Confirmar que o PDF do contrato não pode ser excluído sozinho (só substituído ou junto com o contrato), consequência de ele ser obrigatório.

Ata e saldo (E8): por decisão do responsável, a regra do saldo fica **em aberto de propósito** e será definida ao cadastrar a ata. Ao chegar na E8, o modelo deve ser flexível (por exemplo, saldo por item e quantidade ou por valor) em vez de fixar uma regra agora. Ainda a definir: campos da ata e ligação com o PE.
