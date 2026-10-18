# CHANGELOG

Registro cronológico, mais recente primeiro.

## 2026-10-18 — E4.2: corrige laço de redirecionamentos e confirma o backup em uso real
- **Erro:** `ERR_TOO_MANY_REDIRECTS` no site do Railway. Causa: o waitress descartava o cabeçalho `X-Forwarded-Proto`, então o Django via HTTP e redirecionava sempre. Correção em `serve.py` (`opcoes_de_proxy`), commit `e2ea16d`, publicado no deploy `91a3a4fa` (68/68 testes).
- **Confirmado pelo responsável:** login funciona e o download do backup pela tela "Backup dos dados" funcionou.
- **Pendente:** restauração de teste com o `.zip` baixado; itens 5 a 8.

## 2026-10-17 — D-027 decidida: backup manual no Hobby e cópia no computador
- **Informado pelo responsável:** no plano Hobby o backup do Railway só funciona manualmente; uma cópia deve ficar no computador dele.
- **Verificado no Railway:** o Postgres não tem proxy TCP nem URL pública; o computador não alcança o banco com os scripts da E4.1. Os PDFs ficam num volume visível só ao serviço `gestor`.
- **Registrado:** D-027 (política DECIDIDA; mecanismo PROPOSTO: tela "Backup" só para Admin que gera e baixa um .zip com banco e PDFs, sem `.env`); ROADMAP e PROJECT_STATE ajustados. Nenhum código.
- **GitHub:** `add_repo` continua recusado (a conta do GitHub não está vinculada ao Claude Code); os envios seguem pela ferramenta de GitHub, arquivo a arquivo.
- **Próxima ação:** confirmação do mecanismo; depois implementação e teste no Railway.

## 2026-10-18 — E4.2 item 4: backup manual baixável (EM ANDAMENTO)
- **Decisão (D-027):** no Hobby o backup do Railway é só manual; a cópia vai para o computador do responsável por uma tela "Backup" do sistema (mecanismo recomendado, adotado).
- **GitHub:** o repositório foi adicionado à sessão (`add_repo`); o código oficial passa a ser enviado por `git push` do clone `/home/claude/gestordecontratos`. Enviados: documentos de continuidade, E4.1 (já estava lá) e esta etapa.
- **Código:** `Dockerfile` (Python 3.13 + `postgresql-client-18`) e `.dockerignore`; `manutencao/nucleo.py` (projeto.zip opcional; `verificar_backup` só exige banco e PDFs); `manutencao/web.py`, `urls.py`, `templates/backup.html` (tela só para Admin, uma geração por vez, zip temporário apagado depois do envio); link "Backup dos dados" na página inicial do Admin; `INSTALACAO_NUVEM.md`.
- **Testes:** local, com PostgreSQL 16: 24/24 do núcleo. **Railway: 66/66 OK** (22 da E4 + 12 da E4.2 + 24 do núcleo de backup + 8 da tela de backup), com `pg_dump`/`pg_restore` 18 reais. O `.zip` gerado contém só `banco.dump`, `arquivos.zip` e `manifest.json`.
- **Erros e correções:** (1) meu teste esperava 4 arquivos no zip; são 3. Enquanto falhou, o serviço reiniciou em laço (ele roda os testes antes de subir). (2) Os logs do Railway são muito extensos: usar filtros.
- **Não verificado:** clique real no botão pelo navegador; restauração de um `.zip` baixado; meu acesso de rede ao domínio do Railway é bloqueado.
- **Próxima ação:** o responsável testa o botão; restauração de teste; itens 5 a 8 da E4.2.

## 2026-10-17 — E4.2 itens 1 a 3: HTTPS, limite de tentativas e PDFs persistentes (EM ANDAMENTO)
- **Decisões:** D-025 (Railway definitivo; Hobby agora, Pro depois) e D-026 (segurança de acesso).
- **Código:** `config/settings.py` (HTTPS, HSTS, cookies, cabeçalhos, `django-axes`, `MEDIA_ROOT`), `templates/bloqueado.html`, `accounts/management/commands/verificar_armazenamento.py`, `accounts/tests.py` (12 testes novos e `force_login`), `requirements.txt` (`django-axes`), `.env.example`.
- **Railway:** volume `gestor-volume` em `/data`; variável `ARQUIVOS_PASTA=/data/arquivos`; comando de início agora roda `verificar_armazenamento`.
- **Testes:** **34/34 OK no Railway** (22 antigos + 12 novos). Persistência: a marca criada às 22:04 UTC continuou presente após reimplantar ("persistente").
- **Erros e correções:** 1º deploy: 5 testes antigos falharam (`AxesBackendRequestParameterRequired`, porque `client.login()` não passa `request`); corrigidos com `force_login`. O serviço reiniciava em loop enquanto os testes falhavam (o comando de início roda os testes antes de subir). Aviso `axes.W006` silenciado de propósito (D-026).
- **Aprendizado de operação:** um `push` ao GitHub feito pela ferramenta **não dispara** deploy no Railway; é preciso reconectar a fonte do serviço (`connect-service-source`). `redeploy` reaproveita a versão antiga da configuração.
- **Não feito:** itens 4 a 8 da E4.2; a E4.1 ainda não foi ao GitHub; login com bloqueio não foi exercitado manualmente no navegador (só nos testes automáticos).
- **Próxima ação:** item 4, backup em nuvem.
- **Complemento (mesma data):** D-027 (PROPOSTA) registra a pesquisa sobre backup no Railway: backups de volume agendados cobrem qualquer volume (diário 6 dias, semanal 27, mensal 89); a documentação não informa os planos; só restauram no mesmo projeto; apagar o volume apaga os backups; não há ferramenta para agendá-los (painel). Recomendação: agendar nos dois volumes e depois ter uma cópia fora do Railway.

## 2026-10-17 — D-024: sistema na internet, Railway como ambiente de construção e teste
- **Decisão do responsável:** mudou de ideia sobre o projeto somente local; pode ficar na internet e será construído e testado no Railway.
- **Registrado:** D-024 (substitui D-011 e D-018; D-021 vira ambiente contínuo); nova etapa E4.2 no ROADMAP; ARCHITECTURE e PROJECT_STATE atualizados; riscos novos em P-020.
- **Alterado:** DECISIONS, ROADMAP, ARCHITECTURE, PROJECT_STATE, CHANGELOG. Nenhum código.
- **Erros:** nenhum.
- **Próxima ação:** aprovação da E4.2 e das decisões pendentes (hospedagem definitiva, domínio, responsável pelas contas, custo).

## 2026-10-17 — E4.1 Backup local (PRECISA REVISÃO)
- **Entregue:** `manutencao/nucleo.py` e `cli.py` (backup e restauração sem Django, só biblioteca padrão e ferramentas do PostgreSQL), `fazer_backup.py`, `restaurar_backup.py`, `fazer_backup.bat`, `restaurar_backup.bat`, `agendar_backup.bat`; `MEDIA_ROOT` em `config/settings.py` (D-023); variáveis `ARQUIVOS_PASTA`, `BACKUP_PASTA`, `BACKUP_PASTA_COPIA`, `BACKUP_MANTER`, `PG_BIN` em `.env.example`; `restauracao/` no `.gitignore`; seção "Backup" em `INSTALACAO_WINDOWS.md`; ajustes em ARCHITECTURE, DECISIONS (D-012 parcial, D-022, D-023), ROADMAP e README.
- **Testes:** 20 em `manutencao/test_nucleo.py`, reexecutados hoje com PostgreSQL 16 real no Linux: **20/20 OK**. Cobrem compactação, retenção, conferência de integridade, restauração (inclusive recusa de sobrescrever, de backup corrompido, de nome de banco e de caminho malicioso) e falha da cópia secundária.
- **Não verificado:** `.bat` e agendamento no Windows; `manage.py test` completo com a E4.1 (Django não instala na sessão); envio da E4.1 ao Railway (não feito, a cópia de teste tem só a E4).
- **Correção de registro:** PROJECT_STATE e CHANGELOG estavam sem a E4.1, embora ROADMAP e DECISIONS já a descrevessem; reconciliados.
- **Erros:** nenhum.
- **Próxima ação:** validar no servidor Windows; definir o segundo local dos backups (D-012); depois E5.

## 2026-10-17 — E4 validada no Railway (CONCLUÍDA)
- **Feito:** GitHub com escrita liberado; código enviado ao repositório privado `felipesildiniz/Gestordecontratos` (branch main, 3 commits). Projeto Railway `gestor-contratos-teste` criado com PostgreSQL e o serviço `gestor`, ligado ao repositório. Domínio de teste: https://gestor-production-5955.up.railway.app.
- **Ajustes de código para hospedagem:** `serve.py` lê a variável `PORT` (antes de `SERVIDOR_PORTA`); `settings.py` confia em `X-Forwarded-Proto` quando `DJANGO_USAR_HTTPS=True`; no `tests.py` o BOM foi escrito como `"\ufeff"` (mesmo comportamento).
- **Start command do teste:** `test` → `migrate` → `collectstatic` → `serve.py`.
- **Testes:** **22 de 22 passaram** (`Ran 22 tests ... OK`, PostgreSQL do Railway, Python 3.13, Linux). Migrações e `collectstatic` (128 arquivos) OK. Página `/entrar/` abre no ar (título, campos Usuário/Senha e botão Entrar).
- **Não verificado:** login manual no navegador (não há usuário criado no Railway); execução no Windows com Python 3.12.
- **Erros:** nenhum. Aviso inofensivo nos testes: "No directory at /app/staticfiles/" (o `collectstatic` ainda não tinha rodado).
- **Observação:** `get-logs` e `curl` a partir da sessão: o proxy de saída bloqueia o domínio do Railway; a verificação HTTP foi feita por WebFetch.
- **Próxima ação:** E4.1 (backup local). Opcional: criar um usuário de teste no Railway e testar o login no navegador; depois apagar o projeto de teste.

## 2026-10-17 — Repositório informado; vínculo do GitHub pendente (E4 segue PRECISA REVISÃO)
- **Informado pelo responsável:** repositório `felipesildiniz/Gestordecontratos` para o teste no Railway (D-021 decidida).
- **Tentativa:** anexar o repositório à sessão com permissão de envio. **Recusada:** o GitHub não está vinculado ao Claude. Nada foi enviado ao GitHub e nada foi criado no Railway.
- **Alterado:** DECISIONS, ROADMAP, PROJECT_STATE, CHANGELOG. Nenhum código.
- **Erros:** nenhum.
- **Próxima ação:** o responsável vincula o GitHub ao Claude (claude.ai → Configurações → Conectores) e avisa; então a sessão anexa o repositório, envia o código e testa no Railway.

## 2026-10-17 — Pedido de teste no Railway (E4 segue PRECISA REVISÃO)
- **Pedido do responsável:** testar o sistema no Railway, já que o ambiente da sessão não instala o Django.
- **Verificado:** a conta do Railway conectada é a do usuário `felipesildiniz`, com um projeto já existente (`proactive-connection`, não tocado). As ferramentas do Railway só implantam a partir de um repositório GitHub ou de uma imagem Docker pública, e o Railway CLI não está instalado na sessão. Como o código está só no computador (D-018), **nada foi criado no Railway**.
- **Decisão pendente:** D-021 (teste no Railway exige um repositório GitHub de teste, exceção temporária à D-018).
- **Alterado:** DECISIONS, ROADMAP, PROJECT_STATE, CHANGELOG. Nenhum código.
- **Erros:** nenhum.
- **Próxima ação:** o responsável decide sobre o repositório GitHub de teste (D-021) ou segue o teste no servidor Windows.

## 2026-10-04 — E4 Esqueleto do projeto (PRECISA REVISÃO)
- **Adicionado:** projeto Django (`config/`, `accounts/`, `templates/`, `static/`), configuração por `.env`, login e saída, perfis Admin e Consulta (grupos criados após cada `migrate`), comando `criar_usuario`, página inicial, servidor `waitress`, `criar_ambiente.bat`, `iniciar_servidor.bat`, `executar_testes.bat`, `INSTALACAO_WINDOWS.md`, `README.md`, git local.
- **Decisão nova:** D-020 (escolhas técnicas da E4).
- **Testes:** 22 escritos, **0 executados**. O ambiente da sessão não instala o Django (PyPI respondeu 403, bloqueio de política; não foi contornado). Executados: `py_compile` em 17 arquivos, `ruff` (regras F, E9, B; um aviso de estilo corrigido) e a lógica do `config/env.py`.
- **Erros conhecidos:** nenhum, mas o código nunca rodou com o Django.
- **Problema:** o código só existe no .zip entregue (P-013) e a E4 depende de verificação no servidor (P-014).
- **Próxima ação:** executar o guia no servidor Windows e enviar o resultado de `executar_testes.bat`.

## 2026-10-04 — Decisões: servidor Windows e código somente no computador
- **Confirmado pelo responsável:** o sistema roda em um computador servidor da prefeitura, acessado pela rede interna (D-011); o servidor usa **Windows**; o código fica **somente no computador**, sem GitHub (D-018 substituída).
- **Consequências registradas:** servidor de produção `waitress` e estáticos `whitenoise` (gunicorn não roda em Windows); git local apenas para histórico; backup deve incluir a pasta do projeto; entrega do código a cada etapa em .zip (P-013).
- **Alterado:** DECISIONS, ARCHITECTURE, PROJECT_STATE, CHANGELOG. Nenhum código nesta entrada.
- **Erros:** nenhum.

## 2026-10-03 — Mudança: hospedagem local em vez de nuvem
- **Decisão revista:** D-011 passa de "nuvem" para "local, por enquanto". D-012 deixa de ser "provedor de nuvem" e vira "backup e computador servidor".
- **Premissa registrada (a confirmar):** um computador servidor na rede interna, acessado pelo navegador pelos ~20 usuários.
- **Risco:** banco e PDFs em um único computador; backup passa a ser prioridade antes de dados reais.
- **Dúvida aberta:** "tudo local" inclui o código? GitHub (D-018) a reconfirmar.
- **Alterado:** DECISIONS, ARCHITECTURE, PROJECT_STATE, ROADMAP, CHANGELOG. Nenhum código.
- **Testes:** busca por referências antigas a "nuvem" e "provedor".
- **Erros:** nenhum.
- **Próxima ação:** esclarecer as duas dúvidas e iniciar a E4.

## 2026-10-03 — Terceira rodada de respostas (E3 segue CONCLUÍDA; E4 aguarda repositório)
- **Confirmado:** PDF do contrato obrigatório (RN-15, D-019); regra do saldo da ata em aberto até o cadastro da ata (RN-16, D-017); código no GitHub (D-018).
- **Verificado:** a sessão não tem GitHub conectado (listagem de repositórios falhou: nenhuma conta vinculada). Nada foi criado fora do Project.
- **Alterado:** DATABASE, BUSINESS_RULES, DECISIONS, ARCHITECTURE, ROADMAP, PROJECT_STATE, CHANGELOG.
- **Testes:** revisão de consistência entre documentos.
- **Erros:** nenhum.
- **Próxima ação:** conectar o GitHub, informar `dono/nome` do repositório, e iniciar a E4.

## 2026-10-03 — E3 ajuste pós-fechamento (segunda rodada de respostas; E3 segue CONCLUÍDA)
- **Confirmado:** PE = Pregão Eletrônico; INEX = Inexigibilidade; ata de registro de preços não é modalidade (complementa o PE e guarda os saldos); PDF contém somente o contrato; publicação, gestor e fiscal opcionais; contrato pode ser excluído por inteiro; upload limitado a 10 MB.
- **Mudança de decisão:** o limite de upload deixou de ser "sem limite" e passou a 10 MB.
- **Alterado:** DATABASE (modalidades, tipos de documento, exclusão em cascata, ata fora do modelo atual), BUSINESS_RULES (RN-10 a RN-14, RN-H02, RN-H04), DECISIONS (D-007, D-016, D-017), ROADMAP (E6, E8 e E10 renomeadas), PROJECT_STATE, CHANGELOG.
- **Testes:** revisão de consistência entre documentos.
- **Erros:** nenhum.
- **Próxima ação:** E4, após definir onde o código será guardado.

## 2026-10-03 — E3 Modelo de dados, fechamento (CONCLUÍDA)
- **Confirmado pelo responsável:** sequencial reinicia por ano; AD = Adesão de Ata, CE = Concorrência Eletrônica, CH = Chamada Pública; obrigatórios também objeto, valor, contratado e início da vigência; PDF sem limite de tamanho e com exclusão física; limites dos alertas valem no dia exato.
- **Alterado:** DATABASE (obrigatoriedade, unicidade de ano+sequencial, carga de modalidades, regra do PDF), BUSINESS_RULES (RN-05, RN-09 a RN-11), DECISIONS (D-007, D-015), ROADMAP, PROJECT_STATE, CHANGELOG.
- **Testes:** revisão de consistência entre documentos.
- **Erros:** nenhum.
- **Pendências herdadas:** nomes de PE e INEX, PDF único ou dois, obrigatoriedade de publicação/gestor/fiscal/PDF, exclusão de contrato, limite de upload.
- **Próxima ação:** E4.

## 2026-10-03 — E3 Modelo de dados (registro anterior, PRECISA REVISÃO)
- **Adicionado:** modelo lógico completo em DATABASE.md (modalidade, contratado, agente, contrato, contrato_agente, documento, dotacao_orcamentaria, parcela_pagamento, garantia, item_contrato, alteracao_contratual, log_auditoria).
- **Regras registradas:** formato do número (RN-05), dados mínimos e opcionais (RN-06, RN-07), alertas 90/30/15 dias (RN-08).
- **Decisões:** D-013 (alertas calculados), D-014 (vigência vigente e original), D-015 (número em partes); D-005, D-006 e D-008 atualizadas.
- **Arquivos alterados:** DATABASE, BUSINESS_RULES, DECISIONS, ARCHITECTURE, PROJECT_STATE, ROADMAP, CHANGELOG.
- **Testes:** revisão de consistência entre documentos; o modelo ainda não foi executado em banco.
- **Erros:** nenhum. **Problema:** descrição do número do contrato ambígua e lista de "dados mínimos" não diz quais são obrigatórios (premissas em DATABASE.md).
- **Próxima ação:** revisão do responsável; depois E4.

## 2026-10-03 — E2 Requisitos e stack (CONCLUÍDA)
- **Decidido:** Django + PostgreSQL (D-003, D-004); perfis Admin e Consulta (D-010); hospedagem em nuvem (D-011). Aberta: provedor e backup (D-012).
- **Arquivos alterados (fechamento):** DECISIONS, ARCHITECTURE, BUSINESS_RULES, DATABASE, PROJECT_STATE, ROADMAP, CHANGELOG.
- **Próxima ação:** E3 — Modelo de dados.
- **Registro anterior da etapa (checkpoint):**
- **Registrado:** web com ~20 usuários; login e perfis; contratos em PDF guardados no sistema; alertas internos; sem importação; campos obrigatórios (número, data de assinatura, vigência final).
- **Proposto:** Django + PostgreSQL (D-003, D-004), aguardando confirmação.
- **Arquivos alterados:** DECISIONS, BUSINESS_RULES, ARCHITECTURE, DATABASE, PROJECT_STATE, ROADMAP, CHANGELOG.
- **Testes:** conferência de consistência de IDs entre documentos.
- **Erros:** nenhum.
- **Próxima ação:** confirmar stack e perfis; depois E3.

## 2026-10-03 — E1 Fundação
- **Adicionado:** PROJECT_STATE.md, CHANGELOG.md, DECISIONS.md, ARCHITECTURE.md, DATABASE.md, BUSINESS_RULES.md, ROADMAP.md (conteúdo inicial).
- **Diagnóstico:** projeto sem código, sem stack, sem banco, sem repositório.
- **Testes:** verificação de consistência entre os 7 documentos (IDs de etapas, decisões e problemas).
- **Erros:** nenhum.
- **Próxima ação:** E2 — Requisitos e decisão de stack.
