# senha-brasileira

Gerador de senhas brasileiras memoráveis que se **atualiza diariamente com as
notícias do dia**. Referência cultural (das manchetes de hoje) + verbo
conjugado + número marcante.

Tudo em Python puro (biblioteca padrão, **zero dependências**) + um front-end
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
> `atualizar_bancos.py` só produz os *ingredientes* (palavras). A senha em si é
> sorteada no seu navegador com `crypto.getRandomValues` e nunca sai dele.

## Rodar localmente

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

## Atualizar diariamente

### Opção A — GitHub Actions (recomendado: nuvem, grátis, sem servidor)

Já incluído em `.github/workflows/atualizar.yml`. Suba o repositório no GitHub e
ele roda sozinho às 06:00 (Brasília) todo dia, regenerando `bancos.json` e
commitando a mudança. Combina com GitHub Pages pra hospedar o `index.html` de
graça. Rode manualmente em **Actions → Atualizar bancos → Run workflow**.

### Opção B — cron (seu servidor ou Mac/Linux)

```bash
crontab -e
```

Adicione (troque o caminho pelo seu):

```cron
0 6 * * *  cd /caminho/para/senha-brasileira && /usr/bin/python3 atualizar_bancos.py >> atualizar.log 2>&1
```

Roda todo dia às 06:00. `>> atualizar.log` guarda o histórico de execução.

### Testar sem gravar

```bash
python3 atualizar_bancos.py --dry-run   # mostra o que faria e imprime o JSON
```

## Ajustar as fontes

As fontes de notícia ficam na lista `FEEDS`, no topo de `atualizar_bancos.py`.
Adicione qualquer RSS de cultura/entretenimento brasileiro. Feeds que caírem são
ignorados sem quebrar o resto.

Os verbos conjugados (`VERBS_SEED`) são curados à mão de propósito — conjugar
verbo automaticamente a partir de notícia é frágil, e são eles que tiram a senha
de qualquer dicionário de ataque.
