---
name: acer-ssh
description: >
  SSH to the shop-floor server acer. Use when WarPuppy says server, acer,
  ssh, 192.168.1.10, llama.cpp host, or GPU box.
---

# acer SSH

Host alias: `server`. User: `warpuppy`. IP: `192.168.1.10`.

```
ssh -o BatchMode=yes -o ConnectTimeout=5 server 'hostname; whoami'
```

Local Lenovo commands: run in `terminal` with no ssh. Server commands: wrap in `ssh server '...'`.
Never invent a password. Never SSH off the LAN.
