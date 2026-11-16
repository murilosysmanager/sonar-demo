# Relatório SonarQube Cloud — murilosysmanager_sonar-demo

- Organização: `murilosysmanager`
- Projeto: `murilosysmanager_sonar-demo`
- Data da consulta: 2026-11-16
- Branch analisada: `main` (única; última análise em 2026-11-10 20:31 UTC)
- Escopo: issues com status `OPEN` e security hotspots `TO_REVIEW`
- Resultado: **9 issues abertas** e **0 security hotspots**
- Quality Gate: `OK`. As seis condições do gate são todas sobre código novo (`new_*`), então ele não reflete estas 9 issues.

## Como ler este relatório

- **Tipo no Sonar:** as 9 issues vêm de 8 regras distintas, e todas têm tipo `VULNERABILITY` na definição da regra (consultado via API). Não há bugs, code smells nem hotspots abertos. Por isso o agrupamento abaixo é por **família do problema**, não pelo tipo do Sonar.
- **Prioridade (P1 a P8):** definida por exposição (quem consegue atacar e com que facilidade) e impacto (o que se perde). Ela pode diferir da severidade do Sonar, que aparece em coluna separada.
- Todas as issues estão em `app.py`.

## Resumo por severidade (Sonar)

| Severidade | Qtd |
|---|---|
| BLOCKER | 5 |
| CRITICAL | 2 |
| MAJOR | 1 |
| MINOR | 1 |

## Ordem de correção recomendada

| Ordem | Local | Problema | Grupo |
|---|---|---|---|
| P1 | `app.py:75` | Injeção de comando em `/ping` | A |
| P2 | `app.py:47` | SQL injection em `/user` | A |
| P3 | `app.py:68` | XSS refletido em `/hello` | A |
| P4 | `app.py:97` | `host="0.0.0.0"` com `debug=True` (2 issues, 1 linha) | B |
| P5 | `app.py:83` | MD5 para senhas | C |
| P6 | `app.py:17` | `SECRET_KEY` fixa no código | C |
| P7 | `app.py:13` | Sem proteção CSRF | D |
| P8 | `app.py:90` | XSS em `/register`, **provável falso positivo** | A |

---

## Grupo A — Injeção e XSS (entrada do usuário vira código)

São as mais graves. Basta uma requisição HTTP, sem login.

| Prio | Sev. Sonar | Regra | Linha | Descrição | Exposição e impacto |
|---|---|---|---|---|---|
| P1 | BLOCKER | `pythonsecurity:S2076` | 75 | Command Injection via parâmetro de URL em `app.ping()` | Basta um `GET /ping?host=...`. A entrada é concatenada em `ping -c 1 ` + host e executada com `shell=True`, o que dá execução de comandos no servidor com os privilégios do processo. Impacto máximo. |
| P2 | BLOCKER | `pythonsecurity:S3649` | 47 | SQL Injection via parâmetro de URL em `app.get_user()` | Basta um `GET /user?name=...`. Permite ler qualquer tabela via `UNION`, inclusive os hashes de senha de `users`. O `sqlite3` não aceita várias instruções no mesmo `execute`, então o risco principal é vazamento e alteração de leitura, não `DROP TABLE` encadeado. Combina com P5. |
| P3 | BLOCKER | `pythonsecurity:S5131` | 68 | Reflected XSS via parâmetro de URL em `app.hello()` | A rota devolve `"<h1>Olá, " + name + "</h1>"` como `text/html`. A vítima precisa clicar num link forjado. Executa script no navegador dela. |
| P8 | BLOCKER | `pythonsecurity:S5131` | 90 | Reflected XSS via campo de formulário em `app.register()` | **Provável falso positivo.** A linha 90 é `return {"registered": name}, 201`. O Flask serializa dicionário como `application/json`, e o navegador não interpreta isso como HTML. Confirmar e, se for o caso, marcar como falso positivo no Sonar. |

**Como corrigir:**
- `/ping`: usar `subprocess.run(["ping", "-c", "1", "--", host])` sem `shell=True`, e validar `host` contra um padrão permitido.
- `/user`: usar a query parametrizada que já existe em `/safe/user`.
- `/hello`: escapar a entrada com `markupsafe.escape` ou usar template Jinja.

## Grupo B — Configuração que amplia a exposição

As duas issues estão na **mesma linha** (`app.run(debug=True, host="0.0.0.0")`) e se corrigem juntas.

| Prio | Sev. Sonar | Regra | Linha | Descrição | Exposição e impacto |
|---|---|---|---|---|---|
| P4 | BLOCKER | `python:S8392` | 97 | Servidor ligado a todas as interfaces de rede (`0.0.0.0`) | Qualquer máquina da rede alcança as rotas vulneráveis do grupo A. Usar `127.0.0.1` em desenvolvimento e um servidor WSGI atrás de proxy reverso em produção. |
| P4 | MINOR | `python:S4507` | 97 | Modo debug ativo | Expõe stack traces e o console interativo do Werkzeug. A severidade MINOR (impacto LOW no Sonar) subestima o risco **neste caso**, porque o debug está exposto na rede toda. O console tem PIN, mas isso não deve ser a única barreira. |

## Grupo C — Criptografia e credenciais

| Prio | Sev. Sonar | Regra | Linha | Descrição | Exposição e impacto |
|---|---|---|---|---|---|
| P5 | CRITICAL | `python:S4790` | 83 | MD5 (`hashlib.md5`) usado para guardar senhas | MD5 é rápido e sem sal, então os hashes são quebrados com facilidade. Só é explorável depois de um vazamento do banco, o que o P2 permite. Trocar por Argon2, scrypt, bcrypt ou PBKDF2. |
| P6 | MAJOR | `python:S2068` | 17 | `SECRET_KEY` fixa no código (`"super-secret-key-123"`) | A chave está no repositório e no histórico do git. Hoje o app não usa sessões nem assinatura, então o impacto prático é baixo. Mesmo assim, deve ser tratada como comprometida: ler de variável de ambiente e gerar outra se for usada em outro lugar. |

## Grupo D — Controle de acesso

| Prio | Sev. Sonar | Regra | Linha | Descrição | Exposição e impacto |
|---|---|---|---|---|---|
| P7 | CRITICAL | `python:S4502` | 13 | Aplicação sem `CSRFProtect` | A regra pontua impacto HIGH, mas aqui o risco prático é baixo. O app não tem login nem sessão, e o único endpoint que grava dados é `POST /register`. Passa a importar assim que houver autenticação por cookie. Adotar `Flask-WTF CSRFProtect` ou documentar por que não se aplica (por exemplo, API stateless com token). |

---

## Detalhes das issues

| Chave | Regra | Arquivo:linha | Sev. Sonar | Criada em |
|---|---|---|---|---|
| AaHHKUpJp9gtzVcE_TKo | pythonsecurity:S2076 | app.py:75 | BLOCKER | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKp | pythonsecurity:S3649 | app.py:47 | BLOCKER | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKq | pythonsecurity:S5131 | app.py:68 | BLOCKER | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKr | pythonsecurity:S5131 | app.py:90 | BLOCKER | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKm | python:S8392 | app.py:97 | BLOCKER | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKn | python:S4507 | app.py:97 | MINOR | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKl | python:S4790 | app.py:83 | CRITICAL | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKj | python:S4502 | app.py:13 | CRITICAL | 2026-11-10 |
| AaHHKUpJp9gtzVcE_TKk | python:S2068 | app.py:17 | MAJOR | 2026-11-10 |

## Observações

- O projeto foi feito de propósito com estas falhas, para testar o scanner (ver `README.md`). Este relatório trata os achados como reais.
- A análise e a leitura do `app.py` foram só de consulta. Nenhuma issue teve o status alterado no SonarQube Cloud, e nenhum outro arquivo do projeto foi modificado.
