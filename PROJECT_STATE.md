# PROJECT_STATE — GESTOR DE CONTRATOS — LICITAÇÕES

> Fonte oficial do estado do projeto (Regra 1). Ler este arquivo primeiro em toda nova conversa.
> Última atualização: 2026-10-17 (E4.2 em andamento: HTTPS, limite de login e volume de PDFs feitos; 34 testes OK no Railway)

## Visão geral
Sistema web para gerenciamento de contratos administrativos, atas, vigências, saldos, termos aditivos, documentos, alertas, auditoria e relatórios.

## Etapa atual
- **Concluídas:** E1 — Fundação; E2 — Requisitos e decisão de stack; E3 — Modelo de dados; E4 — Esqueleto do projeto (validada no Railway; falta confirmar no Windows).
- **E4.1 — Backup local: PRECISA REVISÃO.** Código e restauração testados com PostgreSQL 16 no Linux (20/20); falta validar os .bat e o agendamento no servidor Windows.
- **E4.2 — Preparar para a internet: EM ANDAMENTO** (itens 1 a 4 de 8 feitos: HTTPS, limite de login, PDFs persistentes e backup manual baixável); faltam 5 a 8. Depois: E5 — Cadastro de contratos.

## Diagnóstico
| Item | Resultado |
|---|---|
| Código-fonte | Escrito na E4 (17 arquivos .py, 3 templates, CSS, 3 scripts .bat). Executado no Railway (Linux, Python 3.13): 22/22 testes OK. Ainda não executado no Windows. |
| Stack | Django 5.2 + PostgreSQL + waitress + whitenoise (D-003, D-004, D-020) |
| Arquitetura | Monólito web simples (ARCHITECTURE.md) |
| Modelo de dados | Documentado em DATABASE.md (12 tabelas lógicas); nenhuma tabela de negócio criada |
| Hospedagem | Internet, Railway (D-024, substitui D-011); servidor Windows local é só alternativa; backup da E4.1 feito para servidor local, a adaptar na E4.2 |
| Repositório git | GitHub privado `felipesildiniz/Gestordecontratos` é o oficial (D-024); git local também mantido. Atenção: o GitHub tem só o código da E4 (sem E4.1 nem documentos) |
| Funcionalidades implementadas | Login, saída, perfis Admin e Consulta, criação de usuários (comando e área administrativa do Django), página inicial, HTTPS obrigatório, bloqueio por tentativas de senha, volume persistente para PDFs. Nenhuma funcionalidade de negócio. |
| Testes | **34/34 OK no Railway** (E4 + E4.2: login, perfis, HTTPS, limite de tentativas, armazenamento). E4.1: 20/20 OK com PostgreSQL 16 real (Linux), em `manutencao/test_nucleo.py` (ainda não enviado ao GitHub nem rodado no Railway). Nada rodou no Windows. |

## Requisitos confirmados pelo responsável
- Aplicação web, cerca de 20 usuários; login; perfis Admin (edita tudo) e Consulta (somente visualiza).
- Hospedagem: internet, Railway definitivo (D-024, D-025); plano Hobby agora e Pro depois. Código no GitHub (D-024; antes: só no computador, D-018).
- PDF contém somente o contrato, é guardado só no sistema, limite de 10 MB, excluído fisicamente.
- Contrato pode ser excluído por inteiro (cadastro errado), só pelo Admin, com cópia na auditoria (D-016).
- Alertas só dentro do sistema: 90 dias verde, 30 amarelo, 15 vermelho, no dia exato (RN-08).
- Sem dados legados para importar.
- Número do contrato `N°.MODALIDADE.NÚMERO/ANO`, sequencial reiniciando por ano (RN-05). Modalidades: PE (Pregão Eletrônico), INEX (Inexigibilidade), AD (Adesão de Ata), CE (Concorrência Eletrônica), CH (Chamada Pública).
- Ata de registro de preços não é modalidade: complementa o Pregão Eletrônico e guarda os saldos usados pelos contratos (D-017). Regra do saldo em aberto até o cadastro da ata (RN-16).
- Obrigatórios: número do contrato, data de assinatura, vigência final, início da vigência, objeto, valor, contratado e **PDF do contrato** (D-019). Não obrigatórios: data de publicação, gestor e fiscal.

## Funcionalidades de negócio (escopo declarado, nada implementado)
Contratos · Atas e saldos · Vigências · Termos aditivos · Documentos · Alertas · Auditoria · Relatórios — todas NÃO INICIADA.

## Problemas e riscos registrados
- **P-004** Os documentos ficam na raiz da pasta do projeto; no Project do claude.ai existem cópias em `claude/` (não é possível gravar na raiz do Project).
- **P-005** (REDUZIDA) Backup implementado na E4.1 (D-022): diário às 02:00, 30 cópias, restauração testada. Seguem abertos (D-012): qual computador será o servidor, **onde fica o segundo local** (`BACKUP_PASTA_COPIA`, disco externo ou outro computador) e quem confere os backups. Até validar no Windows e definir o segundo local, **só dados de teste**.
- **P-020** (REDUZIDA em 2026-10-18) Na internet (D-024) já estão feitos: HTTPS obrigatório, limite de tentativas, PDFs persistentes e backup manual baixável. Faltam: remover a senha e os usuários de teste, separar teste e produção, HSTS de 1 ano, restauração de teste do .zip baixado.
- **P-019** Os scripts `.bat` e o agendamento (`agendar_backup.bat`) nunca rodaram no Windows. O backup contém o `.env` e os hashes de senha: guardar em lugar seguro (D-022).
- **P-007** Como o PDF é obrigatório, falta confirmar que ele não pode ser excluído sozinho (só substituído ou junto com o contrato).
- **P-008** Ata e saldo não modelados; regra do saldo em aberto de propósito (E8).
- **P-013** (RESOLVIDA em 2026-10-18) O código oficial está no GitHub `felipesildiniz/gestordecontratos` (D-024); o .zip deixou de ser a única cópia.
- **P-014** (REDUZIDA) A E4 foi executada no Railway com 22/22 testes OK, mas ainda não no servidor Windows com Python 3.12. Mitigação: `executar_testes.bat` no servidor.
- **P-015** (REDUZIDA) HTTPS obrigatório e limite de tentativas implementados (D-026). Resta o bloqueio ser por usuário, não por IP, o que permite negar acesso a uma conta de propósito.
- **P-016** Ao criar um novo Admin pela área administrativa, é preciso marcar "staff" manualmente (D-020).
- **P-017** O sistema não inicia sozinho com o Windows (D-020).
- **P-018** (RESOLVIDA) Teste no Railway feito em 2026-10-17: projeto `gestor-contratos-teste`, domínio https://gestor-production-5955.up.railway.app, só dados de teste. A cópia no GitHub e o projeto Railway devem ser apagados quando não forem mais úteis (D-021). O Railway usa Python 3.13; o Windows planejado usa 3.12.
- Resolvidos: P-001 (stack), P-002 (perfis), P-003 (repositório), P-006 (formato do número), P-009 (exclusão de contrato), P-010 (PE, INEX e ata), P-011 (PDF único), P-012 (código local).

## Checkpoint
- ETAPA: E4.2 — Preparar para a internet
- STATUS: EM ANDAMENTO (itens 1 a 4 de 8)
- ÚLTIMO PONTO CONCLUÍDO: item 4, backup manual baixável (D-027): `Dockerfile` com `postgresql-client-18`; tela "Backup" só para Admin que gera o `.zip` (banco + PDFs + manifesto SHA-256, sem `.env` nem código) e o baixa; `nucleo` com projeto opcional. **66/66 testes OK no Railway** (deploy `28815753`, commit `9f6ecc0`), inclusive o que gera o `.zip` de verdade com `pg_dump` 18 e o que restaura (E4.1) com `pg_restore` 18. Volume `/data` continua persistente após a troca de build. `INSTALACAO_NUVEM.md` criado (item 8, primeira versão).
- **2026-10-18 (verificado pelo responsável):** o site abriu com `ERR_TOO_MANY_REDIRECTS` (waitress descartava `X-Forwarded-Proto`); corrigido em `serve.py` (commit `e2ea16d`, deploy `91a3a4fa`, 68/68 testes). Depois disso o responsável entrou no sistema e **baixou o backup pelo botão: item 4 verificado em uso real**. **Conferência do `.zip` real (2026-10-18):** zip íntegro; `banco.dump` (44442 bytes) e `arquivos.zip` (165 bytes, só a marca do armazenamento: ainda não há PDFs) batem com o SHA-256 do manifesto; sem `.env` nem código; o dump traz as 14 tabelas do sistema (auth, axes, django). **Restauração desse arquivo NÃO executada:** o dump é do `pg_dump` 18 e o ambiente de teste do Claude só tem o `pg_restore` 16 (recusa o formato 1.16; o apt do PostgreSQL está bloqueado). O caminho de restauração já é coberto no Railway pelo teste automático (pg 18, 68/68). Para restaurar este arquivo de verdade: máquina com o cliente PostgreSQL 18 ou o serviço no Railway.
- PONTO EXATO ONDE PAROU: o botão da tela de backup ainda não foi usado por uma pessoa no navegador; não houve restauração de um `.zip` baixado de verdade.
- ARQUIVOS ALTERADOS: Dockerfile, .dockerignore, manutencao/nucleo.py, manutencao/web.py, manutencao/urls.py, manutencao/test_nucleo.py (+4 testes), manutencao/test_web.py (+7), config/urls.py, templates/backup.html, templates/home.html, INSTALACAO_NUVEM.md, DECISIONS, ROADMAP, PROJECT_STATE, CHANGELOG.
- O QUE FALTA: item 5 (novo Admin pela área administrativa com acesso `staff`, P-016); 6 (remover `SENHA_TESTE` e usuários de teste); 7 (separar teste e produção); 8 (completar o guia); HSTS de 1 ano; restauração de teste do `.zip` baixado.
- ERROS: nenhum aberto. No caminho: um teste meu esperava 4 arquivos no .zip em vez de 3 (corrigido); enquanto falhou, o serviço reiniciou em laço (o comando de início roda os testes antes de subir).
- PRÓXIMA AÇÃO: o responsável abre `https://gestor-production-5955.up.railway.app`, entra como `admin_teste`, vai em "Backup dos dados", baixa o `.zip` e me conta se funcionou; depois fazemos a restauração de teste e os itens 5 a 8.
