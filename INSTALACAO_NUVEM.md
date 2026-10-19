# Guia da nuvem (Railway) — Gestor de Contratos

Hospedagem definitiva: Railway (D-024, D-025). O projeto `gestor-contratos` tem **dois ambientes separados** (D-028): `production` (a produção) e `teste` (dados fictícios). Dados reais só entram na produção, e só depois da lista "Antes de usar dados reais".

## Como as peças se encaixam
- **GitHub** (`felipesildiniz/gestordecontratos`, privado): código oficial. O Railway constrói a imagem a partir do `Dockerfile` (Python 3.13 + cliente PostgreSQL 18).
- **Dois ambientes no mesmo projeto**, cada um com seu próprio serviço `gestor`, `Postgres` (PostgreSQL 18) e volumes (`postgres-volume`, `gestor-volume` em `/data`). Um não enxerga o banco nem os PDFs do outro.

| | Produção (`production`) | Teste (`teste`) |
|---|---|---|
| Branch do GitHub | `main` | `teste` |
| Endereço | `gestor-production-5955.up.railway.app` | `gestor-teste.up.railway.app` |
| Dados | reais (futuramente) | só fictícios |
| Usuários | `CENERY` (Admin) | `admin_ficticio` (criado no início, senha na variável `SENHA_ADMIN_TESTE`) |
| `DJANGO_SECRET_KEY` | própria | própria e diferente |

- **Comando de início (os dois):** testes → `migrate` → `collectstatic` → `verificar_armazenamento` → `serve.py` (o teste ainda cria o `admin_ficticio` antes de `serve.py`). Se algum teste falhar, o serviço **não sobe** (de propósito).
- **Volume `gestor-volume`** em `/data`: PDFs (`ARQUIVOS_PASTA=/data/arquivos`). Sobrevive a novas implantações.
- Um `git push` **não** implanta sozinho: é preciso aplicar a mudança no ambiente (painel: botão Deploy, ou a sessão do Claude).

## Como publicar uma mudança (fluxo)
1. Envie o código para a branch `teste` e implante **só o ambiente `teste`**. Confira os testes (o log mostra `Ran N tests ... OK`) e use o sistema lá.
2. Se estiver bom, leve a mesma mudança para a `main` e implante a **produção**.
3. **Cuidado:** trocar a fonte do serviço sem restringir ao ambiente vale para **todos** os ambientes e trocaria a branch da produção. Pelo painel, mude a branch dentro do ambiente certo; pela sessão do Claude, a mudança é feita em "preparação" (staged) só para o ambiente e depois aplicada.

## Variáveis do serviço `gestor` (em cada ambiente)
`DJANGO_SECRET_KEY` (**diferente** em cada ambiente), `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_USAR_HTTPS=True`, `DJANGO_HSTS_SEGUNDOS` (produção: `31536000`; teste: padrão), `DB_NOME/DB_USUARIO/DB_SENHA/DB_HOST/DB_PORTA` (referências ao Postgres do **próprio** ambiente), `ARQUIVOS_PASTA=/data/arquivos`, `PYTHONUNBUFFERED=1`. Só no teste: `SENHA_ADMIN_TESTE`.

## Criar o primeiro Admin em um ambiente novo
Um ambiente novo nasce **sem nenhum usuário** e ninguém consegue entrar. Crie o primeiro Admin assim:
1. No serviço `gestor` do ambiente, crie uma variável temporária (por exemplo `SENHA_ADMIN_INICIAL`) com uma senha forte que só você conhece.
2. Acrescente ao comando de início, antes de `serve.py`: `(python manage.py criar_usuario --usuario NOME --perfil admin --senha "$SENHA_ADMIN_INICIAL" || true) &&`
3. Implante, entre com o usuário e **troque a senha** se quiser.
4. **Remova a variável e o trecho do comando de início** e implante de novo.
Depois disso, os demais usuários são criados pelo próprio sistema em `/admin/auth/user/add/`: marque o grupo **Admin** ou **Consulta** (quem é Admin recebe o acesso à área administrativa sozinho).

## Backup (D-027, D-029)
O plano Hobby não agenda backups do Railway; eles são feitos à mão. Faça com frequência e **sempre antes de mudanças importantes**.

1. **Cópia no seu computador:** entre como Admin, "Backup dos dados", **Gerar e baixar backup**. Vem um `.zip` com `banco.dump`, `arquivos.zip` (PDFs) e `manifest.json` (tamanhos e somas SHA-256). Não leva o `.env` nem o código. O arquivo contém dados dos contratos e as senhas dos usuários em forma protegida (hash): não envie por e-mail.
2. **Backup dentro do Railway:** painel, volume `postgres-volume` (e `gestor-volume`), aba **Backups**, criar backup manual. Só restaura no mesmo projeto, e apagar o volume apaga os backups dele. No plano **Pro** passa a haver agendamento.
3. **Segunda cópia, fora do Railway (decidida, ainda não implementada, etapa E4.4):** semanal, para o **Google Drive**, **criptografada**, com a chave privada guardada **só pelo responsável**. O sistema guardará apenas a chave pública (criptografa, mas não descriptografa). Opcional: terceira cópia em HD externo, em outro local.

### Restaurar a partir do `.zip` baixado
1. Descompacte o `.zip`; surge uma pasta `AAAA-MM-DD_HHMMSS`.
2. Num computador com Python e as ferramentas do PostgreSQL **18** (`pg_restore`, `psql`) e com este projeto, rode `python restaurar_backup.py <pasta>`. Por padrão restaura em um banco **novo** e em pastas vazias, sem tocar no que está em uso, e recusa backup que não confere. Ferramentas de versão menor que a 18 **não leem** o dump.
3. Para recolocar os dados no Railway é preciso abrir temporariamente o acesso ao banco (proxy TCP) e usar `pg_restore`; é uma intervenção técnica: peça apoio e **faça um backup novo antes**. Não existe restauração por tela.
4. **Restauração de teste já feita** em 2026-10-18 no Railway (comando `conferir_restauracao`: restaura o `.zip` num banco temporário, compara as contagens com o banco em uso e apaga o temporário). Repita antes de dados reais com um backup novo.

## Antes de usar dados reais (lista)
- [x] Remover `SENHA_TESTE` e os usuários de teste; Admin real `CENERY` criado (2026-10-18).
- [x] Separar ambientes: `teste` (fictício) e `production` (real) (2026-10-19).
- [x] Restauração de teste de um backup baixado, com sucesso (2026-10-18).
- [x] Subir o HSTS da produção para 1 ano (`DJANGO_HSTS_SEGUNDOS=31536000`), depois de confirmar o HTTPS.
- [ ] **E4.3** Acesso seguro: bloqueio progressivo, aviso na próxima entrada e MFA (aplicativo autenticador) para todo Admin (D-030).
- [ ] **E4.4** Backup semanal criptografado no Google Drive, chave privada só do responsável (D-029).
- [ ] Definir domínio próprio (opcional) e quem administra as contas do Railway e do GitHub.
- [ ] Conferir o uso do plano Hobby (5 GB de armazenamento, logs de 7 dias) e o crédito gasto pelos **dois** ambientes.
