# Guia da nuvem (Railway) — Gestor de Contratos

Hospedagem definitiva: Railway (D-024, D-025). Hoje existe um projeto de teste (`gestor-contratos-teste`) com dados fictícios. Antes de dados reais, ver "Antes de usar dados reais".

## Como as peças se encaixam
- **GitHub** (`felipesildiniz/gestordecontratos`, privado): código oficial. O Railway constrói a imagem a partir do `Dockerfile` (Python 3.13 + cliente PostgreSQL 18).
- **Serviço `gestor`**: roda o sistema. Comando de início: testes → `migrate` → `collectstatic` → `verificar_armazenamento` → criação dos usuários de teste → `serve.py`. Se algum teste falhar, o serviço **não sobe** (de propósito).
- **Serviço `Postgres`** (PostgreSQL 18, volume `postgres-volume`): o banco.
- **Volume `gestor-volume`** em `/data`: PDFs (`ARQUIVOS_PASTA=/data/arquivos`). Sobrevive a novas implantações.
- Um `git push` **não** implanta sozinho: é preciso reconectar a origem do serviço (a sessão faz isso) ou usar "Deploy" no painel.

## Variáveis do serviço `gestor`
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_USAR_HTTPS=True`, `DB_NOME/DB_USUARIO/DB_SENHA/DB_HOST/DB_PORTA` (referências ao serviço Postgres), `ARQUIVOS_PASTA=/data/arquivos`, `PYTHONUNBUFFERED=1`. Só no teste: `SENHA_TESTE`.

## Backup (D-027) — Hobby: só manual
O plano Hobby não agenda backups do Railway; eles são feitos à mão. Faça os dois abaixo, com frequência e **sempre antes de mudanças importantes**.

1. **Cópia no seu computador (a que protege contra perda da conta ou do projeto):**
   entre no sistema como Admin → "Backup dos dados" → **Gerar e baixar backup**. Vem um `.zip` com `banco.dump` (banco), `arquivos.zip` (PDFs) e `manifest.json` (tamanhos e somas SHA-256 para conferir). Não leva o `.env` nem o código. Guarde em lugar seguro e, de preferência, em dois lugares (computador + disco externo). O arquivo contém dados dos contratos e as senhas dos usuários em forma protegida (hash): não envie por e-mail.
2. **Backup dentro do Railway (restauração rápida):** painel do Railway → projeto → volume `postgres-volume` (e `gestor-volume`) → aba **Backups** → criar backup manual. Só restaura no mesmo projeto, e apagar o volume apaga os backups dele. No plano **Pro** passa a haver agendamento (diário/semanal/mensal): ativar ao migrar.

### Restaurar a partir do `.zip` baixado
1. Descompacte o `.zip`; surge uma pasta `AAAA-MM-DD_HHMMSS`.
2. Num computador com Python e as ferramentas do PostgreSQL 18 (`pg_restore`, `psql`) e com este projeto, rode `python restaurar_backup.py <pasta>`. Por padrão restaura em um banco **novo** (`<banco>_restaurado`) e em pastas vazias, sem tocar no que está em uso, e recusa backup que não confere.
3. Para recolocar os dados no Railway é preciso abrir temporariamente o acesso ao banco (proxy TCP) e usar `pg_restore`; isso é uma intervenção técnica: peça apoio e **faça um backup novo antes**. (A restauração dentro do Railway por tela do sistema não existe.)
4. Antes de dados reais, faça **uma restauração de teste** de um backup baixado, para saber que o caminho funciona.

## Antes de usar dados reais (lista)
- [ ] Remover `SENHA_TESTE` e os usuários `admin_teste` e `consulta_teste`; criar os Admin reais (`python manage.py criar_usuario` ou área administrativa) com senhas fortes.
- [ ] Separar ambientes: um projeto de **teste** (dados fictícios) e um de **produção** (dados reais).
- [ ] Subir o HSTS: `DJANGO_HSTS_SEGUNDOS=31536000` depois de confirmar que tudo funciona em HTTPS.
- [ ] Fazer e **restaurar de teste** um backup baixado (acima); definir onde ficam as cópias e quem as faz.
- [ ] Definir domínio próprio (opcional) e quem administra as contas do Railway e do GitHub.
- [ ] Conferir o uso do plano Hobby (limite de 5 GB de armazenamento; histórico de logs de 7 dias).
