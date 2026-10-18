# Instalação no servidor Windows

> **Situação (E4 — PRECISA REVISÃO):** este código foi escrito, mas **ainda não foi executado**: o ambiente onde ele foi criado não conseguiu baixar o Django. A primeira instalação no seu servidor é, portanto, parte da verificação. Se qualquer passo falhar, copie a mensagem de erro **inteira** e envie na conversa: o objetivo é corrigir o código, não fazer você contornar o problema.

Tempo estimado: 40 a 60 minutos. Faça com o login de administrador do Windows.

## O que será instalado

| Programa | Para que serve |
|---|---|
| Python 3.12 | Executa o sistema |
| PostgreSQL 16 (ou 17) | Guarda os dados |

Os dois são gratuitos. O sistema em si é a pasta `gestor_contratos` que acompanha este guia.

## Passo 1 — Instalar o Python

1. Baixe o Python 3.12 em https://www.python.org/downloads/windows/ (instalador "Windows installer 64-bit").
2. Abra o instalador e **marque a caixa "Add python.exe to PATH"** (fica na primeira tela, embaixo). Sem isso, nada funciona.
3. Clique em "Install Now" e conclua.

## Passo 2 — Instalar o PostgreSQL

1. Baixe o PostgreSQL 16 em https://www.postgresql.org/download/windows/ (instalador da EDB).
2. Durante a instalação, mantenha as opções padrão (porta **5432**).
3. Quando pedir a **senha do superusuário `postgres`**, escolha uma senha forte e **anote em lugar seguro**.

## Passo 3 — Criar o banco e o usuário do sistema

1. No menu Iniciar, abra **SQL Shell (psql)**.
2. Aperte Enter em "Server", "Database", "Port" e "Username" (aceita os padrões) e digite a senha do `postgres` do passo 2.
3. Digite os dois comandos abaixo, **trocando `ESCOLHA-UMA-SENHA`** por uma senha nova (diferente da do `postgres`; não use aspas dentro dela). Cada comando termina com `;`:

```sql
CREATE ROLE gestor WITH LOGIN PASSWORD 'ESCOLHA-UMA-SENHA' CREATEDB;
CREATE DATABASE gestor_contratos OWNER gestor ENCODING 'UTF8';
```

   A permissão `CREATEDB` é necessária para os testes automáticos, que criam um banco temporário.

4. Se o segundo comando der erro falando em "encoding" ou "template database", use esta versão no lugar dele:

```sql
CREATE DATABASE gestor_contratos OWNER gestor ENCODING 'UTF8' TEMPLATE template0 LC_COLLATE 'Portuguese_Brazil.1252' LC_CTYPE 'Portuguese_Brazil.1252';
```

5. Digite `\q` para sair.

## Passo 4 — Copiar o sistema

1. Descompacte o arquivo `.zip` recebido em `C:\GestorContratos` (ou outra pasta sem acentos e sem espaços).
2. Guarde o `.zip` original em outro lugar: ele é a única cópia do código fora desse computador.

## Passo 5 — Criar o ambiente

Dê dois cliques em **`criar_ambiente.bat`**. Ele baixa as bibliotecas do sistema (precisa de internet) e termina com "Ambiente criado com sucesso".

## Passo 6 — Configurar o arquivo `.env`

1. Na pasta do sistema, copie `.env.example` e cole com o nome **`.env`** (sem nada antes do ponto).
2. Abra o `.env` no Bloco de Notas e preencha:
   - `DJANGO_SECRET_KEY`: abra o Prompt de Comando na pasta, rode `.venv\Scripts\activate` e depois `python -c "import secrets; print(secrets.token_urlsafe(50))"`. Copie o texto gerado para o `.env`.
   - `DB_SENHA`: a senha do usuário `gestor` criada no passo 3.
   - `DJANGO_ALLOWED_HOSTS`: some o IP do servidor na rede (rode `ipconfig` e veja "Endereço IPv4"). Exemplo: `localhost,127.0.0.1,192.168.0.10`.
3. Salve. **Nunca envie o `.env` a ninguém**: ele contém as senhas.

## Passo 7 — Rodar os testes

Dê dois cliques em **`executar_testes.bat`**. São 22 testes. No final deve aparecer **`OK`**.
Se aparecer `FAILED` ou `ERROR`, envie todo o texto da janela.

## Passo 8 — Criar o primeiro usuário Admin

1. Abra o Prompt de Comando **na pasta do sistema** (na barra de endereço do Explorer, digite `cmd` e Enter).
2. Rode:

```
.venv\Scripts\activate
python manage.py migrate
python manage.py criar_usuario --usuario seu.login --perfil admin --nome "Seu Nome"
```

3. O sistema pede a senha duas vezes (ela não aparece enquanto você digita). Mínimo de 10 caracteres, sem ser só números nem uma senha comum.

## Passo 9 — Iniciar o sistema

Dê dois cliques em **`iniciar_servidor.bat`** e **deixe a janela aberta**: fechá-la desliga o sistema. Abra o navegador em `http://localhost:8000` e entre com o usuário criado.

## Passo 10 — Liberar o acesso pela rede

Para os outros computadores acessarem:

1. Abra o Prompt de Comando **como Administrador** e rode (libera só a rede local):

```
netsh advfirewall firewall add rule name="Gestor de Contratos" dir=in action=allow protocol=TCP localport=8000 remoteip=localsubnet
```

2. Nos outros computadores, acesse `http://IP-DO-SERVIDOR:8000`.
3. Peça a quem cuida da rede para **fixar o IP** do servidor; senão o endereço pode mudar.

## Cadastrar os demais usuários

Entre como Admin, clique em **Gerenciar usuários** → **Adicionar usuário**. Na tela seguinte:

- Em **Grupos**, escolha `Admin` ou `Consulta`.
- Para quem for `Admin`, marque a caixa da **equipe** (em inglês, "staff status"); sem ela o acesso a esta área não abre. Para `Consulta`, deixe desmarcada.
- **Não** marque "status de superusuário".

## Backup (etapa E4.1)

O backup copia **três coisas**: o banco de dados, os PDFs e a pasta do sistema (inclusive o arquivo `.env`). Cada backup é uma pasta `backups\AAAA-MM-DD_HHMMSS` com `banco.dump`, `arquivos.zip`, `projeto.zip` e `manifest.json` (tamanhos e somas de verificação, usados para conferir se nada se corrompeu).

### Configurar (uma vez)
No `.env`, preencha (os nomes estão no `.env.example`):
- `BACKUP_PASTA_COPIA` — **segundo local**: um disco externo (exemplo `E:\backups-gestor`) ou pasta de outro computador. **Sem isso, se o disco do servidor falhar, os backups se perdem junto.** O sistema avisa a cada backup enquanto isso não estiver configurado.
- `BACKUP_MANTER` — quantos backups guardar em cada local (padrão 30; os mais antigos são apagados).
- `PG_BIN` — só se aparecer "Não encontrei o programa pg_dump": informe a pasta `bin` do PostgreSQL (exemplo `C:\Program Files\PostgreSQL\17\bin`).

### Fazer um backup agora
Dê dois cliques em `fazer_backup.bat`. No final deve aparecer **BACKUP OK**. O histórico fica em `backups\backup.log`.

### Backup automático diário
Clique com o botão direito em `agendar_backup.bat` → **Executar como administrador**. Ele cria uma tarefa no Windows que faz o backup **todos os dias às 02:00**. O computador precisa estar ligado nesse horário. Para mudar o horário, ou para marcar "executar assim que possível se um horário for perdido", abra o **Agendador de Tarefas** do Windows. Confira de vez em quando se há um backup recente em `backups`.

### Testar a restauração (faça uma vez, e de tempos em tempos)
Um backup que nunca foi restaurado não é garantia. Dê dois cliques em `restaurar_backup.bat`, digite o nome de uma pasta de `backups` e confira o resultado. Isso **não altera o sistema em uso**: cria um banco novo chamado `NOME_DO_BANCO_restaurado` e extrai os PDFs e o código em `restauracao\<backup>`.

### Se o servidor quebrar (recuperação)
1. Em um computador (o mesmo, formatado, ou outro), refaça os passos 1 e 2 (Python e PostgreSQL) e o passo 3 (banco e usuário).
2. Copie a pasta do backup mais recente (do disco externo) para o computador.
3. Extraia `projeto.zip` em uma pasta nova (por exemplo `C:\Gestor`). Ele já traz o `.env`. Se o IP mudou, ajuste `DJANGO_ALLOWED_HOSTS`.
4. Execute o passo 5 (`criar_ambiente.bat`).
5. Restaure o banco por cima do banco vazio recém-criado, no terminal da pasta do sistema:
   `python restaurar_backup.py CAMINHO\DO\BACKUP --banco gestor_contratos --sobrescrever --so-banco`
   (o programa pede que você digite o nome do banco para confirmar).
6. Extraia `arquivos.zip` na pasta `media` do sistema (ou na pasta definida em `ARQUIVOS_PASTA`).
7. Abra `iniciar_servidor.bat` e confira o login e alguns contratos.

### Cuidados
- O backup contém o `.env` (senhas) e o banco (inclusive os usuários): **guarde o disco externo em lugar seguro** e não envie os backups por e-mail ou serviços públicos.
- Excluir um contrato ou PDF no sistema é definitivo (D-016); a única forma de recuperá-lo é um backup anterior à exclusão. Por isso vale manter vários backups.
- O backup compacta todos os PDFs a cada vez. Se a pasta de PDFs ficar muito grande, avise para a rotina ser mudada para incremental.

## Avisos importantes

- **Antes de usar dados reais**, configure o backup (seção anterior), faça um backup e **teste a restauração**. O teste no servidor Windows ainda não foi feito (veja PROJECT_STATE.md).
- O acesso é por `http` (sem criptografia) na rede interna. **Não exponha o servidor à internet.**
- O sistema não inicia sozinho quando o computador liga; é preciso abrir `iniciar_servidor.bat`.

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `python` não é reconhecido | O Python foi instalado sem a caixa "Add python.exe to PATH" (refaça o passo 1) |
| `password authentication failed` | `DB_SENHA` no `.env` diferente da senha do usuário `gestor` |
| `permission denied to create database` (nos testes) | O usuário `gestor` foi criado sem `CREATEDB` (refaça o passo 3) |
| `connection refused` | O serviço do PostgreSQL não está em execução |
| Outro computador mostra "Bad Request (400)" | O IP do servidor não está em `DJANGO_ALLOWED_HOSTS` |
| Outro computador não abre a página | Regra de firewall do passo 10 ausente, ou IP errado |
