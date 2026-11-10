# sonar-demo

Mini API Flask criada para testar o **SonarQube Cloud**.

> ⚠️ O código tem **falhas de segurança propositais** (SQL injection, XSS,
> injeção de comando, MD5, segredo fixo, debug ligado). Serve só para
> o scanner encontrar problemas. **Não faça deploy.**

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest --cov=app --cov-report=term
python app.py
```

## O que o Sonar deve encontrar

| Local | Problema | OWASP Top 10 |
|-------|----------|--------------|
| `SECRET_KEY` | Segredo fixo no código | A02 / A07 |
| `/user` | SQL injection | A03 |
| `/hello` | XSS refletido | A03 |
| `/ping` | Injeção de comando (`shell=True`) | A03 |
| `/register` | Hash MD5 para senha | A02 |
| `app.run(debug=True)` | Debug ligado | A05 |

A rota `/safe/user` mostra a forma correta (query parametrizada).

## Configuração no SonarQube Cloud

Veja as instruções que acompanham a entrega. Resumo: criar a organização,
importar o repositório, desativar a Automatic Analysis, criar o secret
`SONAR_TOKEN` no GitHub e fazer push na branch `main`.
