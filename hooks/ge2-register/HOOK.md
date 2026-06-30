---
name: ge2-register
description: Register native /ge2 command at gateway startup (Telegram + WebUI)
metadata:
  openclaw:
    emoji: "🛠️"
    events:
      - "gateway:startup"
---

# ge2 register

Registers the native `ge2` command when the gateway boots so all command surfaces route through the same GE2 dispatcher.