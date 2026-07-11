# wumpusnuker

TUI para apagar **suas próprias mensagens** de um canal, DM ou servidor inteiro do Discord.
Sem dependências externas — só a biblioteca padrão do Python.

```
  ◈ wumpusnuker  ·  discord message wiper
```

## ⚠ Aviso

Automatizar uma conta de usuário com o token dela ("self-bot") **viola os Termos de
Serviço do Discord** e pode resultar em **banimento permanente**. Use por sua conta e
risco, de preferência numa conta descartável. **Nunca compartilhe seu token** — ele dá
acesso total à conta.

A API do Discord só permite apagar mensagens **suas**, salvo se o token tiver a permissão
*Manage Messages* no canal.

## Requisitos

- Python 3.8+
- Terminal com suporte a UTF-8 e ANSI (Windows Terminal, não o `cmd.exe` legado)

## Uso

```bash
python wumpusnuker.py
```

Fluxo:

1. Cole o token da conta (input oculto).
2. Escolha o alvo: **canal/DM** (Channel ID) ou **servidor inteiro** (Guild ID).
3. Informe o ID e o delay entre deleções.
4. Confirme digitando `SIM`.
5. Ao terminar, escolha rodar em outro alvo ou sair.

## Como pegar os IDs

Discord → **Configurações → Avançado → Modo desenvolvedor** (ON).
Clique direito no canal/servidor → **Copiar ID**.

## Como pegar o token

Discord no navegador → **F12 → aba Network** → filtre por `api` → abra qualquer request
para `discord.com/api` → **Headers → `authorization`** → copie o valor exato.

## Recursos

- Apaga só suas mensagens (canal, DM ou servidor inteiro)
- Trata rate limit (429) automático, respeitando `retry_after`
- Delay ajustável entre deleções
- Barra de progresso, spinner e feedback ao vivo
- Loop para múltiplos alvos sem relogar

## Notas

- A API não faz bulk-delete de mensagens antigas (>14 dias) — é uma por uma, então
  servidor grande leva tempo.
- Delay muito baixo gera mais 429. Padrão `0.8s` é seguro.

## Licença

MIT

---

by crypt0xf
