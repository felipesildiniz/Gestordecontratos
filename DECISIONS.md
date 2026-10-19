# DECISIONS

Registro de decisões técnicas. Estados: ABERTA · PROPOSTA · DECIDIDA · SUBSTITUÍDA.

## Decididas
### D-001 — Documentação Markdown como fonte de verdade
- **Data:** 2026-10-03 · **Estado:** DECIDIDA
- Os 7 arquivos .md guardam o estado do projeto; a memória da conversa não é fonte oficial.
- Consequência: toda etapa termina com atualização de PROJECT_STATE.md e CHANGELOG.md.

### D-002 — Desenvolvimento incremental por etapas
- **Data:** 2026-10-03 · **Estado:** DECIDIDA
- Etapas pequenas, com ID, objetivo, entrada, implementação, testes, arquivos, pendências e próxima ação. Estados permitidos: NÃO INICIADA, EM ANDAMENTO, CHECKPOINT, BLOQUEADA, PRECISA REVISÃO, CONCLUÍDA.

### D-005 — Modelo de uso: aplicação web, ~20 usuários
- **Data:** 2026-10-03 · **Estado:** DECIDIDA (por resposta do responsável)
- Aplicação web, inicialmente com 20 usuários.
- Hospedagem: ver D-011 (local, por enquanto).

### D-006 — Autenticação e perfis
- **Data:** 2026-10-03 · **Estado:** DECIDIDA quanto ao princípio
- Haverá login e perfis com acessos diferentes.
- Perfis definidos em D-010.

### D-007 — Documentos em PDF, armazenados no sistema
- **Data:** 2026-10-03 · **Estado:** DECIDIDA
- Os contratos são PDF e ficam guardados somente dentro do sistema (sem integração com serviço externo).
- Confirmado em 2026-10-03: **exclusão física** do PDF (apagado de vez). O PDF contém somente o contrato.
- **Limite de upload: 10 MB por arquivo** (segunda rodada de respostas, substitui a resposta anterior de "sem limite"). Isso reduz o risco de disco e permite configurar o limite no servidor.
- Risco aceito: exclusão física é irreversível, então o backup (D-012) é a única proteção contra exclusão por engano. A auditoria registra quem excluiu.
- Política de backup: D-012 e D-022.

### D-008 — Alertas somente dentro do sistema
- **Data:** 2026-10-03 · **Estado:** DECIDIDA quanto ao canal (sem e-mail ou outro canal externo)
- Antecedência definida em 2026-10-03: 90, 30 e 15 dias (RN-08). Alerta por saldo baixo segue como hipótese (RN-H05).

### D-009 — Sem importação de dados inicial
- **Data:** 2026-10-03 · **Estado:** DECIDIDA
- Não existem contratos em planilhas; o sistema começa vazio e o cadastro é feito direto nele. Importação fica fora do escopo inicial.

## Decididas na E2 (confirmadas pelo responsável em 2026-10-03)
### D-003 — Linguagem e framework
- **Estado:** DECIDIDA — Python com Django.
- **Justificativa:** traz autenticação, grupos e permissões prontos (perfis de acesso), migrações de banco, upload de arquivos e painel administrativo, o que cobre login, perfis, PDFs e cadastro sem construir tudo do zero. Atende bem 20 usuários.
- **Alternativa:** Node.js (backend) com React (interface): mais flexível na interface, porém exige montar autenticação e permissões manualmente.

### D-004 — Banco de dados
- **Estado:** DECIDIDA — PostgreSQL.
- **Justificativa:** tipos decimais exatos para valores e saldos, integridade relacional, bom suporte a datas e consultas para relatórios. Compatível com Django.
- **Observação:** os PDFs ficam no sistema de arquivos do servidor (referenciados pelo banco), não dentro do banco.

### D-010 — Perfis de acesso
- **Estado:** DECIDIDA — dois perfis: **Admin** (edita tudo, inclusive usuários) e **Consulta** (somente visualiza).
- Se surgir necessidade de um perfil intermediário (ex.: Gestor que cadastra contratos sem gerenciar usuários), registrar nova decisão.

### D-011 — Hospedagem
- **Estado:** SUBSTITUÍDA pela D-024 em 2026-10-17 (o sistema passa a poder ficar na internet; o histórico abaixo é mantido). Antes: DECIDIDA — **local, por enquanto** (revisada em 2026-10-03; a decisão anterior era nuvem e foi substituída).
- **Confirmado em 2026-10-04:** o sistema roda em **um único computador servidor** da prefeitura, com **Windows**, e os ~20 usuários acessam pelo navegador, pela rede interna. (Uma cópia em cada computador não serviria, porque todos precisam enxergar os mesmos dados.)
- Consequência técnica do Windows: o servidor de produção será o `waitress` (o `gunicorn` não roda em Windows) e os arquivos estáticos serão servidos pelo `whitenoise`.
- Consequência: banco, PDFs e sistema ficam no mesmo computador; o backup deixa de ser responsabilidade de um provedor (ver D-012).
- A mudança para nuvem fica possível no futuro (a stack Django + PostgreSQL funciona nos dois).

## Decididas na E3 (decisão técnica do responsável técnico, 2026-10-03; reversíveis enquanto não houver dados)
### D-013 — Alertas calculados, sem tabela
- **Estado:** DECIDIDA
- O nível do alerta (verde, amarelo, vermelho, vencido) é calculado na consulta a partir de `data_fim_vigencia`.
- **Justificativa:** com ~20 usuários o cálculo é barato; evita tabela que fica desatualizada quando a vigência muda.
- **Consequência:** se for pedido "marcar alerta como lido" ou histórico de alertas, criar tabela em etapa própria.

### D-014 — Vigência final vigente e original
- **Estado:** DECIDIDA
- `contrato` guarda `data_fim_vigencia` (vigente, usada nos alertas) e `data_fim_vigencia_original` (imutável). Prorrogações registradas em `alteracao_contratual` atualizam a vigente.
- **Justificativa:** alertas leem um único campo, e o prazo original continua auditável.

### D-015 — Número do contrato guardado em partes e formatado
- **Estado:** DECIDIDA (formato confirmado em 2026-10-03, RN-05); sequencial reinicia a cada ano, logo (`ano`, `sequencial`) é único
- Guarda `sequencial`, `modalidade`, `numero_modalidade` e `ano`, e monta `numero_formatado` (único).
- **Justificativa:** permite filtrar por modalidade e ano e ainda exibir o número como o órgão usa.

### D-016 — Exclusão de contrato inteiro
- **Data:** 2026-10-03 · **Estado:** DECIDIDA (por resposta do responsável)
- O Admin pode excluir o contrato por inteiro em caso de cadastro errado. Exclusão física e em cascata (inclui PDFs).
- **Salvaguardas técnicas adotadas:** confirmação explícita na tela; a auditoria guarda o retrato completo do contrato e dos registros ligados a ele antes de apagar; só o perfil Admin tem essa ação.
- **Consequência:** na E8, a exclusão deve devolver à ata o saldo que o contrato consumiu.

### D-017 — Ata de registro de preços guarda os saldos
- **Data:** 2026-10-03 · **Estado:** DECIDIDA (por resposta do responsável)
- A ata não é modalidade; complementa o Pregão Eletrônico e guarda os saldos consumidos pelos contratos.
- **Consequência no roadmap:** saldos passam da E6 para a E8, que vira "Atas e saldos". A E6 fica só com vigências e prorrogações.
- A regra de cálculo do saldo fica em aberto de propósito e será definida ao cadastrar a ata (resposta do responsável em 2026-10-03). O modelo da E8 deve ser flexível.

### D-018 — Código-fonte somente no computador (sem GitHub)
- **Data:** 2026-10-04 · **Estado:** SUBSTITUÍDA pela D-024 em 2026-10-17 (o GitHub passa a ser o repositório oficial). Antes: DECIDIDA (substitui a decisão de 2026-10-03 de usar o GitHub)
- O código fica somente no computador, sem GitHub nem outro serviço externo. Mantém-se um repositório git **local**, só para guardar o histórico de alterações.
- **Consequência:** o código não tem cópia fora do computador; o backup (D-012) precisa incluir também a pasta do projeto, além do banco e dos PDFs.
- **Consequência para o trabalho com o Claude:** o código criado numa sessão fica no ambiente temporário dela. A cada etapa o projeto é entregue como arquivo .zip, que o responsável deve guardar. Uma nova conversa só continua o código se o .zip for anexado de novo (P-013).

### D-019 — PDF do contrato obrigatório
- **Data:** 2026-10-03 · **Estado:** DECIDIDA (por resposta do responsável)
- Todo contrato precisa ter o PDF. Validação na aplicação, no cadastro.

### D-020 — Escolhas técnicas da E4
- **Data:** 2026-10-04 · **Estado:** DECIDIDA (decisão técnica do responsável técnico; reversível enquanto não houver dados)
- Pacotes: Django 5.2 LTS, `psycopg` 3 (binário, sem compilar no Windows), `waitress`, `whitenoise` e `tzdata` (necessária para fuso horário no Windows).
- Perfis são grupos do Django criados automaticamente após cada `migrate`. Admin recebe permissões sobre usuários e acesso à área `/admin/` (campo "staff"); Consulta não recebe permissões de edição. Superusuário conta como Admin; usuário sem perfil entra mas não acessa nada.
- Gerenciamento de usuários pela área administrativa do próprio Django (sem tela própria, por ora) e pelo comando `criar_usuario`.
- Senha mínima de 10 caracteres; sessão encerra após 8 horas sem uso; fuso `America/Belem`; idioma pt-BR.
- Configuração por arquivo `.env` (senhas fora do código); testes usam o mesmo PostgreSQL da produção, por isso o usuário do banco precisa de `CREATEDB`.
- **Limitações conhecidas, a decidir depois:** HTTP sem criptografia; sem bloqueio contra tentativas repetidas de senha; marcar "staff" é manual ao criar um novo Admin pela área administrativa; o sistema não inicia sozinho com o Windows.

## Abertas
### D-012 — Backup e computador servidor (execução local)
- **Estado:** PARCIALMENTE DECIDIDA (2026-10-17). A parte técnica foi implementada na E4.1 (D-022). **Seguem abertas, dependem do responsável:** qual computador será o servidor (ligado nos horários de uso, com IP fixo), onde fica o segundo local dos backups (disco externo ou outro computador) e quem confere os backups.
- **Risco aumentado pela mudança para local:** banco e PDFs ficam em um único computador. Se o disco falhar, o computador for roubado ou formatado, perde-se tudo, e exclusões (de PDF ou de contrato) são irreversíveis.
- Respondido em 2026-10-04: o servidor é um computador com **Windows**.
- Itens que dependem disso: instalação de Python e PostgreSQL no servidor, acesso pela rede interna.

### D-021 — Teste no Railway (ambiente de teste na nuvem)
- **Data:** 2026-10-17 · **Estado:** EXECUTADA. Repositório privado `felipesildiniz/Gestordecontratos` (código enviado pela ferramenta de GitHub) e projeto Railway `gestor-contratos-teste` (PostgreSQL + serviço `gestor`). Resultado: 22/22 testes OK. Ambos podem ser apagados quando o responsável quiser; a hospedagem oficial continua sendo o servidor local (D-011).
- **Para destravar:** vincular o GitHub ao Claude em claude.ai → Configurações → Conectores. Alternativa menos prática: subir os arquivos do .zip pelo site do GitHub; nesse caso cada correção posterior precisaria ser reenviada à mão.
- O responsável pediu o teste no Railway. É **somente teste**, com dados fictícios: não altera a hospedagem local (D-011).
- O Railway só implanta a partir de um repositório GitHub ou de uma imagem Docker pública, e o Railway CLI não está disponível na sessão. O teste exige, portanto, um repositório GitHub (pode ser privado), o que abre uma **exceção temporária** à D-018 (código só no computador).
- **Se aceito:** o responsável cria um repositório privado vazio e informa `dono/nome`; a sessão o anexa, envia o código, cria no Railway um projeto separado com PostgreSQL e o serviço, roda os 22 testes e verifica login e perfis. Ao final, o projeto no Railway e o repositório podem ser apagados.
- **Se recusado:** o teste segue no servidor Windows (`INSTALACAO_WINDOWS.md`).
- Conta do Railway conectada: usuário `felipesildiniz` (confirmar que é a conta pretendida). Nela já existe o projeto `proactive-connection`, que não foi tocado.

## Decididas na E4.1 (decisão técnica do responsável técnico, 2026-10-17; reversíveis)
### D-022 — Política de backup
- **Estado:** DECIDIDA como padrão inicial; o responsável pode mudar horário, quantidade e destino.
- **O que é copiado:** banco (`pg_dump` formato custom), PDFs (`arquivos.zip`) e pasta do sistema com o `.env` (`projeto.zip`, sem `.venv`, `staticfiles`, backups), mais `manifest.json` com tamanho e SHA-256 de cada arquivo.
- **Quando:** todos os dias às 02:00 pela tarefa agendada do Windows (`agendar_backup.bat`), e a qualquer momento por `fazer_backup.bat`.
- **Onde:** `backups\` no servidor **e** um segundo local (`BACKUP_PASTA_COPIA`: disco externo ou pasta de rede). O segundo local é fortemente recomendado, não obrigatório: sem ele cada backup emite um aviso.
- **Retenção:** os 30 backups mais recentes em cada local (`BACKUP_MANTER`); nunca apaga o último. Frequência diária com 30 cópias permite voltar até ~30 dias após uma exclusão por engano.
- **Segurança do backup:** cada backup é gravado como `.parcial` e só vira definitivo depois de conferido (lista do `pg_restore`, SHA-256); a cópia no segundo local também é conferida. Falha na cópia secundária não invalida o backup local, mas devolve código 2 e aviso.
- **Restauração:** por padrão em um banco NOVO (`<banco>_restaurado`) e em pastas vazias, sem tocar no sistema em uso; restaurar por cima exige `--sobrescrever` e digitar o nome do banco. Recusa backup que não confere. Protegida contra caminhos maliciosos dentro do .zip e nomes de banco inválidos.
- **Consequências:** o backup contém o `.env` e os hashes de senha dos usuários: o disco do backup deve ficar em lugar seguro. Todos os PDFs são recompactados a cada backup (simples e confiável para o volume previsto); incremental só se necessário. Se o servidor estiver desligado às 02:00, o backup do dia não ocorre (conferir no Agendador de Tarefas a opção de executar assim que possível).
- **Implementação:** `manutencao/nucleo.py` (sem Django, só biblioteca padrão e ferramentas do PostgreSQL), `fazer_backup.py`, `restaurar_backup.py`, 3 arquivos `.bat`.

### D-023 — Pasta dos PDFs
- **Estado:** DECIDIDA (reversível)
- Os PDFs ficam em uma pasta do servidor definida por `ARQUIVOS_PASTA` (padrão `media/` dentro do sistema), exposta no Django como `MEDIA_ROOT`. O backup copia essa pasta. O formato dos nomes e o upload são definidos na E9.

### D-024 — Sistema na internet; construir e testar no Railway
- **Data:** 2026-10-17 · **Estado:** DECIDIDA (pelo responsável: "mudei de ideia do projeto somente local, podendo estar na internet; podemos ir construindo e testando")
- **Substitui:** D-011 (hospedagem local) e D-018 (código só no computador). A D-021 (Railway como teste) passa a ser o **ambiente de desenvolvimento e teste contínuo**.
- **Efeitos:** o repositório GitHub `felipesildiniz/Gestordecontratos` (privado) é o **repositório oficial** do código; o serviço `gestor` do Railway é o ambiente em que cada etapa é construída e testada. O servidor Windows deixa de ser requisito (os scripts `.bat` e `INSTALACAO_WINDOWS.md` ficam como alternativa de instalação local).
- **O que muda por estar na internet** (tratado na etapa E4.2): HTTPS obrigatório; proteção contra tentativas repetidas de senha (P-015); PDFs em armazenamento que sobreviva a novas implantações (volume ou bucket do Railway), pois o disco do contêiner é apagado a cada deploy; backup em nuvem, porque o backup da E4.1 (`.bat`, agendador do Windows) foi feito para um servidor local; separação entre ambiente de teste (dados fictícios) e produção (dados reais); usuários e senha de teste removidos antes de dados reais; atenção à LGPD (CPF/CNPJ e dados de contratados).
- **Respondido em 2026-10-17:** o Railway será a hospedagem **definitiva** (D-025). **Seguem em aberto:** domínio próprio; quem administra a conta do Railway e do GitHub (hoje conta pessoal `felipesildiniz`).
- **Enquanto não houver produção:** só dados fictícios.

### D-025 — Plano do Railway: Hobby agora, Pro depois
- **Data:** 2026-10-17 · **Estado:** DECIDIDA (pelo responsável)
- **Hospedagem definitiva:** Railway. Começa no plano **Hobby** (US$ 5 mínimos de uso por mês, inclui US$ 5 de crédito, até 5 GB de armazenamento, 1 usuário no workspace, histórico de logs de 7 dias, meta de disponibilidade de 99,9%, suporte da comunidade). Quando tudo estiver organizado, passa para o **Pro** (US$ 20 mínimos de uso por mês, até 1 TB de armazenamento, usuários ilimitados, suporte do Railway, logs de 30 dias, 99,99%). Valores informados pelo responsável a partir da página de planos do Railway; conferir no site antes de contratar.
- **Consequências:** (a) o limite de **5 GB** do Hobby vale para volumes: PDFs de até 10 MB cada comportam centenas de contratos, mas é um teto a monitorar (E9); (b) no Hobby só uma pessoa acessa o painel do Railway (o sistema em si continua com ~20 usuários); (c) logs de apenas 7 dias: a auditoria do sistema (E11) não deve depender dos logs do Railway; (d) a passagem Hobby → Pro não exige mudar código.
- **Revisar** quando o sistema tiver dados reais ou quando houver mais de uma pessoa administrando a hospedagem.

### D-026 — Segurança de acesso na internet (E4.2)
- **Data:** 2026-10-17 · **Estado:** DECIDIDA e implementada (decisão técnica do responsável técnico)
- **HTTPS:** com `DJANGO_USAR_HTTPS=True` o sistema redireciona HTTP para HTTPS, usa cookies seguros e envia HSTS (começa em 3600 s; aumentar para 1 ano depois de validar).
- **Limite de tentativas:** `django-axes`; 5 erros seguidos no mesmo usuário bloqueiam esse usuário por 30 minutos, na tela de login e na área `/admin/`. Bloqueio **por usuário, não por IP**, porque atrás do proxy do Railway o IP de quem acessa depende de configuração extra. **Limite conhecido:** um atacante pode bloquear de propósito a conta de alguém digitando senha errada (negação de acesso temporária). O Admin libera antes do prazo com `python manage.py axes_reset`.
- **Cabeçalhos:** `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, cookie de sessão `HttpOnly`.
- **PDFs:** volume do Railway montado em `/data`, com `ARQUIVOS_PASTA=/data/arquivos`. O comando `verificar_armazenamento` provou que a marca gravada sobrevive a uma reimplantação.

### D-027 — Backup na nuvem (Railway)
- **Data:** 2026-10-17 · **Estado:** DECIDIDA e IMPLEMENTADA em 2026-10-18 (política pelo responsável; mecanismo recomendado adotado: tela "Backup" no sistema). Testada no Railway (66 testes OK); falta o uso real pelo navegador e uma restauração de teste.
- **Informado pelo responsável (2026-10-17):** no plano **Hobby** o backup de volume do Railway **só funciona manualmente** (não há agendamento). Uma **cópia do backup deve ser guardada no computador** do responsável, fora do Railway.
- **Pesquisa (documentação do Railway):** backups de volume cobrem qualquer volume (banco e PDFs); no Pro há agendamento diário (guardado 6 dias), semanal (27) e mensal (89). Só restauram no mesmo projeto e ambiente; apagar o volume apaga os backups dele; restaurar remove os backups mais novos; os manuais são limitados a 50 % do tamanho do volume. Não há ferramenta nesta sessão para disparar ou agendar: é feito no painel. No Pro o agendamento passa a existir (revisar ao migrar, D-025).
- **Problema técnico:** o banco do Railway **não tem acesso público** (sem proxy TCP e sem `DATABASE_PUBLIC_URL`), e os PDFs ficam num volume que só o serviço `gestor` enxerga. Logo, o computador do responsável não consegue puxar a cópia sozinho com os scripts da E4.1.
- **Mecanismo proposto (recomendado):** uma tela **"Backup" só para Admin** dentro do sistema, com o botão "Gerar e baixar backup": o servidor gera um `.zip` com o banco (`pg_dump`) e os PDFs, confere por SHA-256 e o entrega para download; o responsável guarda o arquivo no computador (e, idealmente, em um segundo lugar). Exige: imagem com o `pg_dump` na versão 18 (igual ao banco), adaptar `manutencao/nucleo.py` para **não incluir o `.env`** nem o código (o código está no GitHub e o `.env` guarda segredos), e testes no Railway. Antes de dados reais, fazer uma restauração de teste a partir do arquivo baixado.
- **Alternativa (menos recomendada):** abrir o proxy TCP do banco só nos momentos do backup e usar `fazer_backup.bat` no computador (exige PostgreSQL 18 instalado lá, expõe o banco à internet enquanto aberto e não alcança os PDFs).
- **Pendente do responsável:** testar o botão no navegador e escolher o segundo lugar da cópia (disco externo, outro computador).
- **Implementação (2026-10-18):** `Dockerfile` com `postgresql-client-18`; `manutencao/web.py` (só Admin, POST gera, uma geração por vez, temporário apagado); `nucleo.fazer_backup(incluir_projeto=False)`; o `.zip` tem `banco.dump`, `arquivos.zip` e `manifest.json`. Guia em `INSTALACAO_NUVEM.md`.
- **Código da E4.1 (D-022):** continua válido para servidor local; no Railway será reaproveitado como biblioteca (`manutencao/nucleo.py`).

### D-028 — Produção e teste separados no Railway (E4.2 item 7)
- **Data:** 2026-10-18. **Status:** DECIDIDA (separação); PROPOSTA (execução do ambiente de teste).
- **Decisão do responsável:** o projeto atual do Railway (`e0422d22…`, domínio `gestor-production-5955`) é a **PRODUÇÃO** e deve ser renomeado de `gestor-contratos-teste` para `gestor-contratos`. Teste e produção ficam separados: dados reais só na produção; o teste usa só dados fictícios.
- **Limite das ferramentas:** o Claude não consegue renomear projeto, criar ambiente nem apagar projeto no Railway (nem pela ferramenta de agente). Esses passos são do responsável, pelo painel (ver PROJECT_STATE).
- **Forma recomendada do ambiente de teste:** um segundo *environment* (`teste`) no mesmo projeto, duplicando `production`, com banco e volume próprios, domínio próprio, `DJANGO_SECRET_KEY` diferente e branch `teste`. Custo extra no plano Hobby (outro Postgres e volume); avaliar antes de ligar.
- **Atualização (2026-10-18):** o responsável renomeou a produção para `gestor-contratos` (confirmado) e escolheu o ambiente de teste como **segundo environment `teste` dentro do mesmo projeto**. O Claude não pode criar environment (confirmado também pelo agente do Railway); o responsável o cria pelo painel (Duplicate Environment a partir de `production`). Branch `teste` criada no GitHub; o environment `teste` deve usar essa branch. Variáveis próprias do teste: `DJANGO_SECRET_KEY` nova; banco e volume próprios (conferir que as variáveis `DB_*` apontam para o Postgres do próprio environment). O teste começa sem usuários: o primeiro Admin fictício é criado por um passo no comando de inicialização do `teste`, só lá.
- **Segurança:** o projeto antigo `c0d68ba3…` (domínio `gestor-production-d45a`) está no ar com versão antiga (E4) e deve ser apagado pelo responsável.
- **Operação (2026-10-19):** `connect-service-source` sem `staged` troca a fonte em todos os ambientes; para mexer só no `teste`, usar `staged: true` com `environmentId` e depois `accept-deploy`. O Admin fictício do `teste` (`admin_ficticio`) é criado pelo comando de inicialização do `teste` com a variável `SENHA_ADMIN_TESTE`, que existe só lá.

### D-029 — Segunda cópia do backup: nuvem criptografada fora do Railway
- **Data:** 2026-10-18. **Status:** DECIDIDA (política); NÃO IMPLEMENTADA (etapa E4.4).
- **Decisão do responsável:** a segunda cópia do backup fica numa **nuvem criptografada, fora do Railway (off-site), com a chave sob custódia do responsável** (nunca do Claude nem do servidor). Opcionalmente, uma **terceira cópia em HD externo guardado em outro local**.
- **Desenho proposto (a confirmar na E4.4):** criptografia assimétrica (por exemplo `age` ou GPG): o sistema guarda só a chave **pública** e consegue criptografar, mas não descriptografar; a chave **privada** fica com o responsável, em pelo menos dois lugares seguros. Assim, um vazamento do Railway ou da nuvem não expõe os dados.
- **Respostas do responsável (2026-10-19):** destino **Google Drive**; frequência **semanal**; a **chave privada fica só com o responsável**.
- **Em aberto (E4.4):** qual conta do Google usar (pessoal ou institucional, por se tratar de dados da administração pública) e como o sistema envia ao Drive (conta de serviço ou autorização OAuth, criada pelo responsável); como agendar: o volume de PDFs só se liga a um serviço, então o envio semanal precisa rodar dentro do próprio `gestor` (ou chamar o sistema por endereço protegido); retenção (quantas semanas); e uma cópia da chave privada em segundo lugar seguro, porque **sem ela o backup não abre**. A cópia do Railway (manual, no plano Hobby, D-027) e o `.zip` baixado continuam valendo até lá.

### D-030 — Política de bloqueio de login: temporário e progressivo, com aviso e MFA
- **Data:** 2026-10-18. **Status:** DECIDIDA (política e escolhas); NÃO IMPLEMENTADA (etapa E4.3). Substitui o bloqueio fixo de 5 tentativas por 30 minutos (D-026).
- **Decisão do responsável:** bloqueio **temporário e progressivo**: 5 tentativas erradas, bloqueio de **15 min**; reincidência, **1 h**; nova reincidência, **24 h**. **Evitar bloqueio permanente como padrão.** O usuário é **notificado** do bloqueio. **MFA** (segundo fator) para **contas sensíveis**. Se ocorrer um bloqueio permanente, o **desbloqueio é manual pelo administrador**.
- **Respostas do responsável (2026-10-19):** contas sensíveis = **todo Admin**; MFA = **aplicativo autenticador (TOTP) com códigos de recuperação**; aviso do bloqueio = **na próxima entrada** (sem e-mail).
- **Pontos ainda a definir na E4.3:** quando zera a contagem de reincidência; o que fazer se um Admin perder o aplicativo e os códigos de recuperação (proposta: outro Admin redefine o MFA dele, e o `CENERY` tem um procedimento técnico documentado); como cadastrar o MFA do `CENERY` sem se trancar para fora; manter o bloqueio por usuário (P-015), que continua permitindo bloquear uma conta de propósito, mas agora por tempo limitado e com aviso.
- **Implementação da E4.3a (2026-10-19, branch `teste`, não testada):** modelo próprio `BloqueioLogin` no lugar do `django-axes` (o escalonamento 15 min, 1 h, 24 h e o aviso não cabem no axes sem depender de detalhes internos). Escolha do Claude a confirmar: o nível de reincidência volta a zero depois de 7 dias sem novo bloqueio. O bloqueio continua por usuário (nomes inexistentes também, para não revelar quem tem conta).
