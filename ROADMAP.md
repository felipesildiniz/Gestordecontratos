# ROADMAP

Estados: NÃO INICIADA · EM ANDAMENTO · CHECKPOINT · BLOQUEADA · PRECISA REVISÃO · CONCLUÍDA

| ID | Etapa | Objetivo | Estado |
|---|---|---|---|
| E1 | Fundação | Diagnóstico e 7 documentos de continuidade | CONCLUÍDA |
| E2 | Requisitos e stack | Registrar requisitos e decidir stack (D-003, D-004, D-010, D-011) | CONCLUÍDA |
| E3 | Modelo de dados | Definir entidades, campos e relacionamentos (DATABASE.md) | CONCLUÍDA |
| E4 | Esqueleto do projeto | Projeto Django + PostgreSQL, git local, login e perfis Admin/Consulta, testes automatizados | CONCLUÍDA (22/22 testes OK no Railway; falta confirmar no Windows) |
| E4.1 | Backup local | Script de backup do banco, dos PDFs e da pasta do projeto, com restauração testada; obrigatório antes de dados reais (D-012, D-022) | PRECISA REVISÃO (código e restauração testados com PostgreSQL 16 no Linux; falta validar os .bat e o agendamento no Windows) |
| E4.2 | Preparar para a internet | HTTPS obrigatório, limite de tentativas de senha, PDFs em armazenamento persistente, backup em nuvem, GitHub como repositório oficial, ambiente de produção separado do de teste (D-024) | CONCLUÍDA (2026-10-19) |
| E4.3 | Acesso seguro | Bloqueio progressivo (5 tentativas, 15 min, 1 h, 24 h), aviso na próxima entrada e MFA por aplicativo autenticador com códigos de recuperação para todo Admin; desbloqueio manual pelo Admin (D-030) | NÃO INICIADA |
| E4.4 | Backup externo criptografado | Backup semanal criptografado no Google Drive, chave privada só do responsável; opcional terceira cópia em HD externo (D-029) | NÃO INICIADA |
| E5 | Cadastro de contratos | CRUD de contratos | NÃO INICIADA |
| E6 | Vigências e prorrogações | Prazos, prorrogações e alertas 90/30/15 dias | NÃO INICIADA |
| E7 | Termos aditivos | Aditivos vinculados a contratos | NÃO INICIADA |
| E8 | Atas e saldos | Atas ligadas ao Pregão Eletrônico, saldos e consumo pelos contratos (D-017) | NÃO INICIADA |
| E9 | Documentos | Upload e vínculo de arquivos | NÃO INICIADA |
| E10 | Alertas de saldo | Avisos de saldo baixo, se confirmados (RN-H05); os de vencimento estão na E6 | NÃO INICIADA |
| E11 | Auditoria | Log de alterações | NÃO INICIADA |
| E12 | Relatórios | Relatórios e exportação | NÃO INICIADA |

A E4.3 e a E4.4 devem estar prontas antes de dados reais. A ordem de E5 a E12 é provisória. Desde 2026-10-17 o sistema é construído e testado no Railway (D-024); a E4.2 deve vir antes de dados reais e, de preferência, antes da E9 (upload de PDFs).

## E3 — Modelo de dados (CONCLUÍDA em 2026-10-03)
- Modelo lógico de 12 tabelas em DATABASE.md, revisado e ajustado com as respostas do responsável. Nenhum código.
- **Testes:** revisão de consistência entre DATABASE, BUSINESS_RULES, DECISIONS e ARCHITECTURE. O modelo só poderá ser executado em banco real a partir da E4/E5.
- **Ajuste pós-fechamento (2026-10-03):** segunda rodada de respostas aplicada (PE e INEX, ata fora das modalidades, PDF só do contrato com 10 MB, exclusão de contrato inteiro, publicação/gestor/fiscal opcionais).
- **Respostas de 2026-10-03 (terceira rodada):** PDF do contrato obrigatório; regra do saldo da ata em aberto até o cadastro da ata; código no GitHub (substituído em 2026-10-04: código somente no computador, D-018).
- **Pendência herdada:** confirmar que o PDF do contrato só pode ser substituído, não excluído sozinho. Pendências da ata ficam para a E8.

## E4 — Esqueleto do projeto (CONCLUÍDA)
- **ID:** E4 · **Objetivo:** projeto Django com PostgreSQL, git local, login funcionando e perfis Admin e Consulta, sem funcionalidades de negócio.
- **Entrada:** D-003, D-004, D-010, D-011 (servidor Windows), D-018 (código só no computador).
- **Implementação (feita):** pastas `config/` e `accounts/`, configuração por `.env`, login e saída, perfis criados após cada `migrate`, comando `criar_usuario`, página inicial, CSS, servidor `waitress`, três scripts `.bat`, guia `INSTALACAO_WINDOWS.md`, repositório git local.
- **Testes:** 22 testes automatizados escritos em `accounts/tests.py` (perfis, login, saída, área administrativa, criação de usuários, leitura do `.env`). **Nenhum foi executado**: o ambiente da sessão não consegue baixar o Django (PyPI bloqueado por política, erro 403). Verificado na sessão: sintaxe de todos os `.py`, análise estática com `ruff` e a lógica de `config/env.py`.
- **Arquivos modificados:** todo o código novo, mais ARCHITECTURE, DECISIONS, PROJECT_STATE, CHANGELOG, ROADMAP.
- **Pendências:** executar o guia no servidor Windows e rodar `executar_testes.bat`; corrigir o que falhar.
- **Próxima ação:** E4.1 (backup). Pendência não bloqueante: rodar `executar_testes.bat` no servidor Windows (Python 3.12) para confirmar o mesmo resultado.

## E4.1 — Backup local (PRECISA REVISÃO)
- **ID:** E4.1 · **Objetivo:** backup e restauração do banco, dos PDFs e da pasta do sistema, antes de qualquer dado real.
- **Entrada:** D-012, D-018, D-016 (exclusão física), D-023.
- **Implementação (feita):** `manutencao/nucleo.py`, `manutencao/cli.py`, `fazer_backup.py`, `restaurar_backup.py`, `fazer_backup.bat`, `restaurar_backup.bat`, `agendar_backup.bat`, `MEDIA_ROOT` e variáveis de backup no `.env`, seção "Backup" em `INSTALACAO_WINDOWS.md`.
- **Testes:** 20 testes em `manutencao/test_nucleo.py` (compactação, retenção, conferência, restauração, recusas, falha da cópia). Rodados com **PostgreSQL 16 real** no Linux: 20/20 OK; 3 mutações do código foram detectadas (a 4ª não mudava o comportamento). Teste de ponta a ponta com os scripts: backup, cópia em outro lugar, restauração (500 linhas e PDF recuperados) e recusa de restaurar por cima. **Não executados:** `manage.py test` completo (o Django não instala na sessão; as suítes são independentes) e nada no Windows.
- **Arquivos modificados:** ver CHANGELOG.
- **Pendências:** no servidor Windows, rodar `fazer_backup.bat`, `restaurar_backup.bat` e `agendar_backup.bat`; configurar `BACKUP_PASTA_COPIA`; decidir o segundo local (D-012).
- **Próxima ação:** o responsável valida no Windows; depois E5 (cadastro de contratos).

## E4.2 — Preparar para a internet (EM ANDAMENTO)
- **ID:** E4.2 · **Objetivo:** deixar a base segura e persistente para rodar na internet, sem acrescentar funcionalidade de negócio.
- **Entrada:** D-024, P-015, P-016, D-022 (backup), D-023 (pasta dos PDFs).
- **Implementação prevista:** (1) HTTPS obrigatório e cabeçalhos de segurança (`SECURE_SSL_REDIRECT`, HSTS, cookies seguros); (2) limite de tentativas de login; (3) armazenamento persistente dos PDFs (volume ou bucket do Railway) e `ARQUIVOS_PASTA`/`MEDIA_ROOT` apontando para ele; (4) backup em nuvem do banco e dos PDFs com restauração testada (adaptando a E4.1); (5) novos Admin criados já com acesso à área administrativa (P-016); (6) remover `SENHA_TESTE` e os usuários de teste do ambiente de produção; (7) separar ambientes teste e produção; (8) documentar em `INSTALACAO_NUVEM.md`.
- **Testes previstos:** testes automatizados do limite de login e dos cabeçalhos; teste de reimplantação mantendo um arquivo gravado; backup e restauração reais no Railway.
- **Pendências:** decisões do responsável listadas na D-024 (hospedagem definitiva, domínio, responsável pelas contas, custo).
- **Feito (2026-10-17):** itens 1 (HTTPS, D-026), 2 (limite de tentativas, D-026) e 3 (volume `/data`, comando `verificar_armazenamento`, persistência comprovada entre deploys). 34 testes OK no Railway.
- **Feito também (2026-10-18):** item 4, backup manual baixável (D-027): `Dockerfile` com `pg_dump` 18, tela "Backup" só para Admin, `.zip` sem `.env`; 66 testes OK no Railway.
- **Feito (2026-10-18):** item 4 (backup manual baixável, confirmado em uso real e restauração real provada no Railway) e item 5 (staff automático para Admin, P-016; 83 testes OK no Railway), e item 6 (Admin real `CENERY`; usuários de teste e `SENHA_TESTE` removidos).
- **Feito (2026-10-19):** item 7 (produção `gestor-contratos` e ambiente `teste` separados, com banco e volume próprios; D-028).
- **Feito (2026-10-19):** item 8 (`INSTALACAO_NUVEM.md` completo: ambientes, fluxo de publicação, primeiro Admin, políticas; HSTS da produção em 1 ano).
- **E4.2 CONCLUÍDA em 2026-10-19** (produção com HSTS de 1 ano conferida: 83/83 testes). Segurança de acesso e backup externo viraram as etapas E4.3 e E4.4 (D-029, D-030), antes de dados reais.
- **Próxima ação:** o responsável testa o botão de backup no navegador e confirma; depois restauração de teste e itens 5 a 8.
