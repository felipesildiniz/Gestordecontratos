# BUSINESS_RULES

## Estado atual (2026-10-03)
Regras confirmadas pelo responsável estão na primeira tabela. As demais são HIPÓTESES e **precisam de validação** antes de virar requisito.

## Regras confirmadas
| ID | Regra | Origem |
|---|---|---|
| RN-01 | Campos obrigatórios do contrato: **número do contrato**, **data de assinatura** e **vigência final** | Responsável |
| RN-02 | O contrato é um arquivo PDF guardado no próprio sistema (somente o contrato; ver RN-10) | Responsável |
| RN-03 | Alertas aparecem somente dentro do sistema | Responsável |
| RN-04 | O acesso exige login. Perfil **Admin** edita tudo, inclusive usuários; perfil **Consulta** apenas visualiza | Responsável |
| RN-05 | Número do contrato no formato `N°.MODALIDADE.NÚMERO-DA-MODALIDADE/ANO` (ex.: `1.PE.15/2026`). O N° (sequencial) **reinicia a cada ano**. Siglas: INEX, AD (Adesão de Ata), PE, CE (Concorrência Eletrônica), CH (Chamada Pública). Número da modalidade de 1 a 100 | Responsável (confirmado 2026-10-03) |
| RN-09 | São obrigatórios também: objeto, valor, contratado e início da vigência | Responsável (confirmado 2026-10-03) |
| RN-10 | O PDF contém somente o contrato e tem limite de **10 MB** por arquivo (substitui a resposta anterior de "sem limite") | Responsável (confirmado 2026-10-03) |
| RN-11 | Ao excluir um PDF, ele é apagado de vez (exclusão física) | Responsável (confirmado 2026-10-03) |
| RN-12 | Um contrato pode ser excluído por inteiro em caso de cadastro errado. Pela RN-04, só o Admin exclui | Responsável (confirmado 2026-10-03); restrição ao Admin é decorrência |
| RN-13 | Data de publicação, gestor e fiscal **não** são obrigatórios | Responsável (confirmado 2026-10-03) |
| RN-14 | PE = Pregão Eletrônico e INEX = Inexigibilidade. A ata de registro de preços **não é modalidade**: complementa o Pregão Eletrônico e guarda os saldos que os contratos utilizam | Responsável (confirmado 2026-10-03) |
| RN-15 | O PDF do contrato é **obrigatório** no cadastro | Responsável (confirmado 2026-10-03) |
| RN-16 | A regra de cálculo e consumo do saldo da ata fica em aberto e será definida ao cadastrar a ata (E8) | Responsável (confirmado 2026-10-03) |
| RN-06 | Dados mínimos do contrato: número, modalidade, datas (assinatura, publicação, início e fim da vigência), objeto, valor em reais, contratado (CPF/CNPJ e razão social), gestor e fiscal (nome, cargo e período) e arquivo PDF | Responsável |
| RN-07 | Campos complementares opcionais: informações complementares, dotação orçamentária, cronograma de pagamentos, garantias, itens, histórico de alterações, responsáveis adicionais (assinante, controlador de encargos, suplente) e indicador de saúde ou educação | Responsável |
| RN-08 | Alertas de vencimento pela vigência final: **90 dias = verde** ("super antecipado"), **30 dias = amarelo**, **15 dias = vermelho** | Responsável |

## Interpretação de RN-08 (limites no dia exato: confirmado em 2026-10-03; o estado "vencido" é sugestão minha)
Dias restantes = vigência final vigente − data de hoje.
| Dias restantes | Alerta |
|---|---|
| mais de 90 | nenhum |
| de 31 a 90 | verde |
| de 16 a 30 | amarelo |
| de 0 a 15 | vermelho |
| menor que 0 | vencido (estado não pedido, sugerido para o contrato não ficar sem sinal) |

Observações: a vigência final vigente considera prorrogações registradas. O alerta é calculado a cada consulta, sem tabela própria (D-013). Alertas por saldo baixo continuam hipótese (RN-H05).

## Validações propostas (confirmar)
- Número do contrato único no sistema, e sequencial único dentro de cada ano.
- Vigência final não anterior à data de assinatura nem ao início da vigência.
- Valor não negativo.
- CPF/CNPJ com dígitos verificadores válidos.
- Anexo somente em PDF, até 10 MB.

## Hipóteses a validar
| ID | Hipótese | Origem | Estado |
|---|---|---|---|
| RN-H01 | Prorrogações geram novo prazo final, preservando a vigência original | Escopo (vigências) | A VALIDAR (modelado em DATABASE.md) |
| RN-H02 | O saldo fica na ata e é consumido pelos contratos; o cálculo exato (por item ou por valor) será definido na E8 | RN-14 | A VALIDAR |
| RN-H03 | Termo aditivo pode alterar prazo, valor ou objeto e fica vinculado ao contrato | Escopo (termos aditivos) | A VALIDAR |
| RN-H04 | Ata está ligada a um Pregão Eletrônico, tem prazo de validade próprio e abastece contratos | RN-14 | A VALIDAR |
| RN-H05 | Alertas também disparam por saldo baixo | Escopo (alertas) | A VALIDAR |
| RN-H06 | Alterações em contrato, saldo e aditivo geram registro de auditoria que não pode ser alterado | Escopo (auditoria) | A VALIDAR |
| RN-H07 | Limites da Lei 14.133/2021 (por exemplo, 25% em acréscimos e supressões; validade de 1 ano, prorrogável, para ata de registro de preços) | Legislação | CONFERIR texto vigente antes de usar |

## Perguntas abertas
- O PDF do contrato pode ser excluído sozinho? Como é obrigatório (RN-15), a proposta é permitir só a substituição ou a exclusão junto com o contrato.
- Para a E8: campos da ata e ligação com o PE (a regra do saldo fica aberta, RN-16).
- Contratos vencidos continuam aparecendo com o estado "vencido"?
- Quais limites e prazos da lei o sistema deve validar automaticamente, e quais apenas sinalizar?
