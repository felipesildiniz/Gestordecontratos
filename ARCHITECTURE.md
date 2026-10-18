# ARCHITECTURE

## Estado atual (2026-10-17)
Esqueleto Django (E4) e preparação para a internet (E4.2, em andamento) executados e testados no Railway (ver PROJECT_STATE.md). Nenhuma funcionalidade de negócio existe; só login com limite de tentativas, perfis, usuários e rotinas de backup (E4.1).

Fluxo: navegador → HTTPS do Railway → `waitress` → Django (o `whitenoise` entrega o CSS) → PostgreSQL. Os PDFs ficam no volume `/data` do Railway (`ARQUIVOS_PASTA`).

Estrutura adicional: `manutencao/` (backup e restauração sem Django) e `fazer_backup.py`, `restaurar_backup.py`.

Estrutura do código:
```
config/     settings, urls, wsgi, env.py (leitura do .env)
accounts/   login e saída, perfis Admin/Consulta, comando criar_usuario, testes
templates/  base, login, início
static/     CSS
serve.py    servidor de produção (waitress)
manutencao/ backup e restauração (E4.1)
*.bat       criar_ambiente, iniciar_servidor, executar_testes (Windows)
```

## Módulos funcionais previstos (escopo declarado)
1. Contratos administrativos
2. Atas
3. Vigências
4. Saldos
5. Termos aditivos
6. Documentos
7. Alertas
8. Auditoria
9. Relatórios

## Requisitos arquiteturais já identificados
- **Rastreabilidade:** a auditoria é requisito declarado; toda alteração relevante deve ser registrável.
- **Dados temporais:** vigências e alertas dependem de datas e de cálculo de prazos.
- **Dados financeiros:** saldos exigem precisão decimal e histórico de movimentações.
- **Arquivos:** módulo de documentos exige armazenamento de arquivos vinculados a contratos/atas.

## Requisitos confirmados na E2 (2026-10-03)
- Aplicação **web**, cerca de **20 usuários** iniciais (porte pequeno: arquitetura simples, um servidor, sem necessidade de escalonamento).
- **Login e perfis** de acesso com permissões distintas.
- **PDFs armazenados no sistema**, vinculados ao contrato.
- **Alertas internos** (sem e-mail ou integrações externas).
- Sem migração de dados legados.

## Arquitetura definida (E2, confirmada em 2026-10-03)
- **Stack:** Python + Django (D-003), PostgreSQL (D-004).
- **Forma:** aplicação web monolítica; um único serviço, simples de operar e de fazer backup.
- **Arquivos:** PDFs em uma pasta do servidor (`ARQUIVOS_PASTA`, padrão `media/`, D-023), referenciados pelo banco.
- **Perfis:** Admin e Consulta (D-010), implementados com grupos e permissões do Django.
- **Hospedagem:** na internet, construída e testada no Railway (D-024, que substitui a D-011); o servidor local Windows fica como alternativa. Servidor de produção: `waitress` com arquivos estáticos pelo `whitenoise`; banco PostgreSQL do Railway. Pontos de atenção da internet na E4.2.
- Código-fonte no GitHub (privado, `felipesildiniz/Gestordecontratos`), repositório oficial (D-024, que substitui a D-018); o Railway implanta a partir dele.
- Alertas calculados na consulta, sem tabela própria (D-013).
- Modelo de dados lógico em DATABASE.md (E3).
- Escolhas técnicas da E4: ver D-020.

## Pendente
- Apps de negócio (contratos, atas, documentos, auditoria) e suas camadas: definir ao iniciar a E5.
- Armazenamento dos PDFs (pasta de mídia, limite de 10 MB): E9.
- Rotina de backup incremental (hoje o backup copia todos os PDFs a cada vez): só se a pasta de PDFs crescer muito.
