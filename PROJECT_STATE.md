# PROJECT_STATE — GESTOR DE CONTRATOS — LICITAÇÕES

> Fonte oficial do estado do projeto (Regra 1). Ler este arquivo primeiro em toda nova conversa.
> Última atualização: 2026-10-17 (E4.2 em andamento: HTTPS, limite de login e volume de PDFs feitos; 34 testes OK no Railway)

## Visão geral
Sistema web para gerenciamento de contratos administrativos, atas, vigências, saldos, termos aditivos, documentos, alertas, auditoria e relatórios.

## Etapa atual
- **Concluídas:** E1 — Fundação; E2 — Requisitos e decisão de stack; E3 — Modelo de dados; E4 — Esqueleto do projeto (validada no Railway; falta confirmar no Windows).
- **E4.1 — Backup local: PRECISA REVISÃO.** Código e restauração testados com PostgreSQL 16 no Linux (20/20); falta validar os .bat e o agendamento no servidor Windows.
- **E4.2 — Preparar para a internet: CONCLUÍDA em 2026-10-19** (8 de 8 itens; 83/83 testes na produção e no teste). Próximas, antes de dados reais: **E4.3** (acesso seguro) e **E4.4** (backup externo criptografado). Depois, **antes de dados reais:** E4.3 (acesso seguro: bloqueio progressivo, aviso e MFA, D-030) e E4.4 (backup externo criptografado, D-029). Depois: E5 — Cadastro de contratos.

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
- **P-021** (RESOLVIDA em 2026-10-18: projeto apagado, domínio fora do ar; restam resquícios na janela de 48 h do Railway) (antes: ABERTA, segurança) O projeto Railway antigo `c0d68ba3…` (domínio `gestor-production-d45a.up.railway.app`) continua no ar, publicamente, com a versão antiga do sistema (E4, sem limite de login nem HTTPS forçado) e provavelmente com os usuários de teste. Deve ser apagado pelo responsável (o Claude não tem ferramenta para isso). Não contém dados reais.
- **P-020** (REDUZIDA em 2026-10-18) Na internet (D-024) já estão feitos: HTTPS obrigatório, limite de tentativas, PDFs persistentes e backup manual baixável. Faltam: remover a senha e os usuários de teste, separar teste e produção, HSTS de 1 ano, restauração de teste do .zip baixado.
- **P-019** Os scripts `.bat` e o agendamento (`agendar_backup.bat`) nunca rodaram no Windows. O backup contém o `.env` e os hashes de senha: guardar em lugar seguro (D-022).
- **P-007** Como o PDF é obrigatório, falta confirmar que ele não pode ser excluído sozinho (só substituído ou junto com o contrato).
- **P-008** Ata e saldo não modelados; regra do saldo em aberto de propósito (E8).
- **P-013** (RESOLVIDA em 2026-10-18) O código oficial está no GitHub `felipesildiniz/gestordecontratos` (D-024); o .zip deixou de ser a única cópia.
- **P-014** (REDUZIDA) A E4 foi executada no Railway com 22/22 testes OK, mas ainda não no servidor Windows com Python 3.12. Mitigação: `executar_testes.bat` no servidor.
- **P-015** (REDUZIDA) HTTPS obrigatório e limite de tentativas implementados (D-026). Resta o bloqueio ser por usuário, não por IP, o que permite negar acesso a uma conta de propósito. Política nova decidida em D-030 (bloqueio progressivo 15 min, 1 h, 24 h, aviso e MFA; desbloqueio manual pelo Admin): será implementada na E4.3.
- **P-016** (RESOLVIDA) Quem entra no grupo Admin recebe `is_staff` automaticamente, por qualquer caminho; ao sair do grupo perde (superusuário não). Implementado em `accounts/perfis.py` (`sincronizar_staff`, sinal `m2m_changed`), 12 testes, 83/83 no Railway (deploy `9f5beb98`).
- **P-017** O sistema não inicia sozinho com o Windows (D-020).
- **P-018** (RESOLVIDA) Teste no Railway feito em 2026-10-17: projeto `gestor-contratos-teste`, domínio https://gestor-production-5955.up.railway.app, só dados de teste. A cópia no GitHub e o projeto Railway devem ser apagados quando não forem mais úteis (D-021). O Railway usa Python 3.13; o Windows planejado usa 3.12.
- Resolvidos: P-001 (stack), P-002 (perfis), P-003 (repositório), P-006 (formato do número), P-009 (exclusão de contrato), P-010 (PE, INEX e ata), P-011 (PDF único), P-012 (código local).

## Checkpoint
- ETAPA: E4.3 — Acesso seguro. Subetapa **E4.3a — bloqueio de login progressivo com aviso na próxima entrada**
- STATUS: CHECKPOINT (código escrito e enviado à branch `teste`, commit `416a60f`; ainda NÃO testado: o Claude não consegue rodar o Django localmente e o deploy no ambiente `teste` não foi aplicado)
- ÚLTIMO PONTO CONCLUÍDO: implementação completa da E4.3a: modelo `BloqueioLogin` + migração `accounts/migrations/0001_initial.py`; `accounts/bloqueio.py` (5 falhas, 15 min, 1 h, 24 h; durante o bloqueio nada conta; nível zera após 7 dias; sem bloqueio permanente); `accounts/backends.py` (recusa login bloqueado também em `/admin/login/`); `accounts/sinais.py` (conta falhas, zera ao entrar, aviso na próxima entrada); `EntrarView` (página 403 com horário); admin com ação "Desbloquear" (Admin ganha as permissões `view/change_bloqueiologin`); comando `desbloquear_usuario`; templates, CSS; **`django-axes` removido** (settings, requirements); 17 testes novos no lugar dos do axes (`BloqueioProgressivoTests`, relógio simulado).
- PONTO EXATO ONDE PAROU: 1º deploy da E4.3a no `teste` (commit `416a60f`, aplicado pelo responsável): **91 de 95 testes passaram, 4 falharam** por erro do próprio teste (o ajudante `entrar` abria a sessão com o backend antigo `ModelBackend`, que saiu da lista de backends; o Django tratava o usuário como anônimo). Por isso o serviço do `teste` não sobe (os testes rodam antes do servidor) e fica reiniciando. Correção no commit `01a303d` (só o teste), enviada à branch `teste` e **preparada (staged, patch `b6a865df`) no `teste`, aguardando o responsável aplicar de novo**. A produção segue intacta na `main` com o axes.
- ARQUIVOS ALTERADOS (só na branch `teste`): accounts/models.py, accounts/migrations/0001_initial.py, accounts/bloqueio.py, accounts/backends.py, accounts/sinais.py, accounts/admin.py, accounts/apps.py, accounts/perfis.py, accounts/views.py, accounts/urls.py, accounts/tests.py, accounts/management/commands/desbloquear_usuario.py, config/settings.py, requirements.txt, templates/bloqueado.html, templates/home.html, static/css/app.css.
- O QUE FALTA: (1) aplicar o deploy no `teste` (painel do Railway, ambiente `teste`, "Apply changes"/Deploy) e ler o log: se algum teste falhar o serviço não sobe, e o Claude corrige; (2) conferir no `teste` a tela de bloqueio e o aviso; (3) E4.3b, MFA (TOTP + códigos de recuperação, todo Admin, exigido por middleware); (4) levar à produção só depois de E4.3a e E4.3b passarem no `teste`.
- ERROS: os 4 do 1º deploy (ajudante de teste com backend antigo), já corrigidos no commit `01a303d`; falta confirmar no `teste`.
- PRÓXIMA AÇÃO: o responsável aplica o deploy no `teste` (ou autoriza o Claude a aplicar); o Claude lê o resultado dos testes e corrige o que falhar.
- DECISÃO DE PROJETO TOMADA PELO CLAUDE (a confirmar): o nível de reincidência volta a zero quando o último bloqueio terminou há mais de 7 dias.
