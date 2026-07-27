# senha-brasileira

Gerador de senhas brasileiras que se **atualiza diariamente com as
notícias do dia**. Referência cultural (das manchetes de hoje) + verbo
conjugado + número marcante.

Tudo em Python (biblioteca padrão, **zero dependências**) + um front-end
estático em HTML.

```
senha-brasileira/
├── atualizar_bancos.py   # busca notícias RSS → escreve bancos.json  (roda 1x/dia)
├── gerar.py              # gerador na linha de comando (usa `secrets`)
├── bancos.json           # dados do dia (gerado automaticamente)
├── index.html            # o site — lê bancos.json no navegador
└── .github/workflows/atualizar.yml   # agendamento diário na nuvem (grátis)
```

## Como funciona

1. `atualizar_bancos.py` baixa feeds RSS de cultura pop do Brasil (G1/Globo),
   extrai nomes próprios e termos das manchetes (`"Pantera Negra"` →
   `panteranegra`) e grava tudo em `bancos.json`.
2. `index.html` faz `fetch("bancos.json")` e monta as senhas com os termos do
   dia. Se o JSON não carregar (offline / `file://`), ele usa uma lista de
   reserva embutida — nunca fica sem funcionar.
3. Um agendador roda o passo 1 todo dia. As notícias mudam → as senhas mudam.

> **Privacidade:** nenhuma senha é gerada ou salva no servidor. O
> `atualizar_bancos.py` só produz a lógica das palavras. A senha em si é
> sorteada no seu navegador com `crypto.getRandomValues` e nunca sai dele.

## Para Rodar localmente

```bash
# 1. gerar os bancos do dia
python3 atualizar_bancos.py

# 2a. usar na linha de comando
python3 gerar.py -n 5
python3 gerar.py --site instagram

# 2b. ou abrir o site (precisa de servidor pro fetch funcionar)
python3 -m http.server 8000
#   → abra http://localhost:8000
```

Requer apenas **Python 3.8+**. Nada de `pip install`.

## Atualização diária

## Via GitHub Actions 

O repositório no GitHub roda sozinho às 06:00 (Brasília) todo dia, regenerando `bancos.json` e
commitando a mudança. Usando a hospedagem do GitHub Pages.

