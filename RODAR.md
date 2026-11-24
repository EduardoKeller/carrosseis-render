# Como rodar o agente com o Gemini CLI

O agente é o `GEMINI.md` desta pasta: o Gemini CLI lê esse arquivo automaticamente quando é aberto aqui.

## 1. Instalar (uma vez)

1. Node.js 20+ e Python 3.11+ instalados.
2. `npm install -g @google/gemini-cli` e depois `gemini` uma vez para fazer login com a conta Google.
3. Nesta pasta:
   ```
   git clone https://github.com/EduardoKeller/carrosseis-render.git
   cd carrosseis-render
   npm i
   pip install playwright
   python -m playwright install chromium
   ```
4. Teste o renderizador: `python render.py exemplos/exemplo.json saida` (deve gerar 24 PNGs sem avisos).

## 2. Notion (opcional, mas recomendado)

O agente lê o calendário no Notion para não repetir histórias e rodar os 15 visuais.
Adicione o servidor MCP do Notion no `~/.gemini/settings.json` (seção `mcpServers`), faça o login quando o Gemini pedir e confira com `/mcp` dentro do Gemini.
Sem Notion, o agente ainda gera os ZIPs, mas perde o controle de repetição.

## 3. Uma rodada manual

Dentro da pasta `carrosseis-render`:
```
gemini --yolo -p "Rode uma rodada completa conforme o GEMINI.md."
```
Os ZIPs saem em `entregas/<data>/<rodada>/`, separados por conta, com `RESUMO.txt`.
`--yolo` aprova os comandos sozinho (necessário para rodar sem você olhando).

## 4. Agendar 3x por dia (Windows)

Agendador de Tarefas → Criar Tarefa → 3 gatilhos diários (06:42, 11:42, 16:42) →
Ação: `gemini`, argumentos `--yolo -p "Rode uma rodada completa conforme o GEMINI.md."`,
"Iniciar em": a pasta `carrosseis-render`.
O computador precisa estar ligado nesses horários.
