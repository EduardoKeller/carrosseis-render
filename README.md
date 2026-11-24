# carrosseis-render

Renderizador dos carrosséis do Projeto Mídias (Instagram 1080×1350 e TikTok 1080×1920).

```bash
npm i                      # fontes (@fontsource)
pip install playwright --break-system-packages && python3 -m playwright install chromium   # se faltar
python3 render.py exemplos/exemplo.json saida
```

O JSON escolhe o mundo visual em `"look"`. São 15:

| look | mundo |
|---|---|
| impacto | fundo escuro, manchete condensada gigante, virada em bloco de cor |
| caderno | papel pautado, caneta azul, marca-texto, fita adesiva |
| recorte | colagem de papéis recortados sobre a cor do pilar |
| tela | interface de celular: notificação, notas, busca, widget |
| placar | painel de embarque, letras em plaquinhas |
| recibo | cupom fiscal térmico, fonte monoespaçada, código de barras |
| quadrinho | HQ: quadros com contorno, retícula, balões |
| rotulo | tabela nutricional: filetes grossos, Archivo condensada |
| riso | impressão risográfica em duas tintas |
| bauhaus | geometria: círculo, barra preta, caixa alta condensada |
| pixel | RPG 8 bits: caixas de diálogo, fonte pixelada |
| quadro | lousa verde com giz e moldura de madeira |
| mural | cortiça com post-its e alfinete |
| tabloide | capa de jornal popular, faixa de título |
| telegrama | formulário amarelo com tiras datilografadas |

Tipos de slide: `cover`, `story`, `big`, `reveal`, `versus`, `chat`, `dots`, `cta`, `follow`.
Avisos no stderr: `OVERFLOW` (texto não coube), `CONTRASTE BAIXO`, `FONTE NAO CARREGOU`.
`ONLY=instagram` renderiza só um formato.
