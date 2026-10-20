# CHANGELOG

Registro cronológico, mais recente primeiro.

## 2026-10-20 — E4.4: 169/169 testes no `teste`
- Deploy `1bd988bf` (commit `9da00cd`): 169 testes OK (inclui ida e volta real com o `age`), migração `manutencao.0001` aplicada, `teste` no ar. Falta o envio real ao Drive. Produção intacta.

## 2026-10-20 — E4.4 escrita na branch `teste` (CHECKPOINT, sem teste)
- Commit `9da00cd`; patch `75c484fe` aguarda o responsável. Criptografia com `age` (chave pública no servidor), envio ao Drive, retenção de 2 por mês, agendador semanal, tela com botão e histórico. Rascunho antigo preservado na branch `e44-rascunho` (só `drive.py`, modelo e testes do Drive foram aproveitados). Produção intacta.

## 2026-10-20 — E4.3 CONCLUÍDA; E4.4 iniciada (desenho)
- Responsável confirmou o MFA do `CENERY`. E4.4: conta Google pessoal por ora (trocável); retenção a esclarecer; desenho em `PROJECT_STATE.md`. Nenhum código novo.

## 2026-10-20 — E4.3 no ar na produção
- Deploy `6167d5fb` (commit `99240cd`): 125/125 testes, migrações `accounts.0001` e `0002` aplicadas, armazenamento persistente, serviço no ar. Falta o `CENERY` configurar o MFA.

## 2026-10-20 — E4.3 enviada para a produção (CHECKPOINT)
- `teste` mesclada em `main` (`3d03340`). Patch `226f9f83` preparado só para `production`; aguarda o responsável aplicar. Escolhas confirmadas: reincidência zera em 7 dias; segredo do MFA em texto no banco.

## 2026-10-20 — E4.3b: 125/125 testes no `teste`
- **Resultado:** deploy `1c949f38` (commit `a0afa8e`): 125 testes OK, migração `accounts.0002_mfa` aplicada, `teste` no ar. Falta a conferência na tela. Produção intacta.

## 2026-10-20 — E4.3b escrita na branch `teste` (CHECKPOINT, ainda sem teste)
- **Implementado (commit `a0afa8e`, só em `teste`):** MFA TOTP obrigatório para todo Admin, com 8 códigos de recuperação (só o hash fica no banco), exigido por middleware em todas as páginas; configuração no primeiro acesso (QR com `segno` + chave para digitar); 5 códigos errados bloqueiam 15 min (contagem própria, não zera ao digitar a senha de novo); ação "Redefinir" em `/admin/` e comando `redefinir_mfa` para quem perdeu o celular; código do aplicativo não pode ser reutilizado. Migração `accounts.0002_mfa`; dependência nova `segno`.
- **Testes:** 33 novos e ajuste dos existentes (helper de login de Admin marca a sessão como verificada). Não rodados: deploy preparado (patch `19a5eb0f`) aguarda o responsável aplicar.
- **Produção:** intacta.

## 2026-10-19 — E4.3a CONCLUÍDA no `teste`
- **Resultado:** 95/95 testes no deploy `5aa0846e` (commit `01a303d`, branch `teste`); migração `accounts.0001_initial` aplicada; `teste` no ar. Produção intacta.

## 2026-10-19 — E4.3a: 1º deploy no `teste` com 4 testes falhando; correção enviada
- **Resultado:** 95 testes, 4 falhas, todas pelo ajudante de teste `entrar` (backend antigo). O `teste` ficou fora do ar (testes rodam antes do servidor). Produção intacta.
- **Correção:** commit `01a303d` na branch `teste` (só `accounts/tests.py`), preparada no Railway (patch `b6a865df`) para o responsável aplicar.

## 2026-10-19 — E4.3a escrita na branch `teste` (CHECKPOINT, ainda sem teste)
- **Implementado (commit `416a60f`, só na branch `teste`):** bloqueio de login progressivo (5 falhas, 15 min, 1 h, 24 h, sem bloqueio permanente), aviso na próxima entrada, ação de desbloquear na área administrativa e comando `desbloquear_usuario`; `django-axes` removido. 17 testes novos.
- **Não verificado:** o Claude não roda o Django localmente; o deploy no `teste` está preparado (patch `93090ce6`) e aguarda aplicação pelo responsável (o `accept-deploy` foi recusado).
- **Produção:** intacta (branch `main`, com axes).

## 2026-10-19 — E4.2 CONCLUÍDA
- **Conferido:** produção reimplantada com HSTS de 1 ano (deploy `763e90bd`): 83/83 testes, armazenamento persistente, login abre. O cabeçalho HSTS em si não foi lido (limite do ambiente do Claude); a configuração está aplicada e testada.
- **Resultado da etapa:** HTTPS, limite de login, PDFs persistentes, backup manual baixável com restauração provada, staff automático do Admin, Admin real, produção e teste separados, guia da nuvem.
- **Próximas:** E4.3 e E4.4, antes de dados reais.

## 2026-10-19 — E4.2 item 8: guia da nuvem completo e HSTS de 1 ano; escolhas de E4.3 e E4.4
- **Guia:** `INSTALACAO_NUVEM.md` reescrito (produção e teste, fluxo de publicação, regra da troca de fonte por ambiente, primeiro Admin em ambiente novo, backup e restauração, lista de pré-requisitos).
- **HSTS:** `DJANGO_HSTS_SEGUNDOS=31536000` aplicado só na produção.
- **Decisões do responsável:** E4.3 (todo Admin, MFA por aplicativo autenticador com códigos de recuperação, aviso na próxima entrada) e E4.4 (semanal, Google Drive, chave privada só dele).
- **Código:** nenhum.

## 2026-10-19 — E4.2 item 7 concluído; políticas de backup e login decididas (D-029, D-030)
- **Conferido:** `teste` no ar na branch `teste` (deploy `b36f2e9e`, 83/83 testes, armazenamento persistente, `admin_ficticio`); produção intacta (deploy `a397d405`).
- **Decidido pelo responsável:** D-029 (segunda cópia em nuvem criptografada off-site, chave sob custódia do responsável, HD externo opcional) e D-030 (bloqueio progressivo 15 min, 1 h, 24 h, aviso ao usuário e MFA para contas sensíveis; sem bloqueio permanente por padrão; desbloqueio manual pelo Admin).
- **ROADMAP:** novas etapas E4.3 (acesso seguro) e E4.4 (backup externo criptografado), NÃO INICIADAS.
- **Código:** nenhum.

## 2026-10-19 — E4.2 item 7: ambiente `teste` configurado (aplicação pendente)
- **Conferido:** `teste` tem Postgres e volume próprios; produção não foi alterada; projeto antigo apagado e fora do ar (P-021 resolvida).
- **Configurado só no `teste`:** `DJANGO_SECRET_KEY` própria, `SENHA_ADMIN_TESTE`, comando de inicialização com `admin_ficticio`.
- **Pendente:** troca da branch do `teste` para `teste` preparada (staged) e não aplicada (recusada pelo responsável).
- **Regra nova:** `connect-service-source` sempre com `staged` + `environmentId`.
- **Código:** nenhum.

## 2026-10-18 — E4.2 item 7: produção renomeada, teste definido como environment
- **Confirmado:** projeto de produção agora se chama `gestor-contratos`. O projeto antigo `c0d68ba3…` ainda existe e responde (P-021 aberta).
- **Decidido pelo responsável:** ambiente de teste = segundo environment `teste` no mesmo projeto. O Claude não consegue criar environment; passos entregues ao responsável. Branch `teste` criada no GitHub.
- **Código:** nenhum.

## 2026-10-18 — E4.2 item 7 iniciado: produção e teste separados (D-028)
- **Decidido:** o projeto atual do Railway é a produção; deve ser renomeado para `gestor-contratos`.
- **Limite:** o Claude não consegue renomear, criar ambiente nem apagar projeto no Railway; passos entregues ao responsável.
- **Achado de segurança (P-021):** o projeto antigo `c0d68ba3…` (domínio `-d45a`) continua no ar com a versão antiga.
- **Código:** nenhum.

## 2026-10-18 — E4.2 item 6: Admin real no lugar dos usuários de teste
- **Feito pelo responsável:** criou `CENERY` (grupo Admin, senha só dele) em `/admin/`, entrou com ele, apagou `admin_teste` e `consulta_teste` e removeu `SENHA_TESTE` no Railway. Sem erros relatados.
- **Feito pelo Claude:** criação automática dos usuários de teste retirada do comando de inicialização (redeploy `67418e3f`); confirmado que `SENHA_TESTE` não existe mais e que o deploy seguinte (`a397d405`) está rodando. Nenhum código alterado.
- **Não verificável pelo Claude:** a exclusão dos dois usuários (sem acesso ao banco); fica pela confirmação do responsável.
- **Pendente:** itens 7 e 8.

## 2026-10-18 — E4.2 item 5: novo Admin recebe acesso à área administrativa (P-016)
- **Implementado:** `sincronizar_staff` em `accounts/perfis.py`, ligado ao sinal `m2m_changed` de `User.groups` em `accounts/apps.py`. Entrar no grupo Admin concede `is_staff`; sair retira (exceto superusuário); Consulta nunca concede; `is_staff` dado à mão a quem não é Admin não é mexido.
- **Testes:** +12 em `accounts/tests.py` (add, set, lado do grupo, remove, clear nos dois lados, superusuário, outro grupo, acesso real a `/admin/`). 83/83 no Railway (deploy `9f5beb98`, commit `7a3c542`).
- **Arquivos:** `accounts/perfis.py`, `accounts/apps.py`, `accounts/tests.py`.

## 2026-10-18 — E4.2: restauração de teste do backup real no Railway
- **Novo:** `manutencao/management/commands/conferir_restauracao.py` (+3 testes) e `manutencao` registrado em `INSTALLED_APPS`.
- **Resultado:** o `.zip` baixado pelo responsável restaurou num banco temporário do Railway (pg 18); contagens iguais às do banco em uso; banco temporário removido (`RESTAURACAO_OK`). 71/71 testes.
- **Limpeza:** comando de inicialização restaurado; branch temporária apagada.

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
