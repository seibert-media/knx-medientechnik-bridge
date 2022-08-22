## Useful Wireshark Filters:

KNX/IP with GW, excluding confirmations and only relevant Group-Range (3/0/0 - 3/0/16)

```
(ip.addr == 10.5.35.11 && kip && !(cemi.mc == 0x2e) && cemi.da >= 0x1800 && cemi.da <= 0x1810)
```

PJLink with EventSpace Beamer

```
(ip.addr == 10.5.32.12 && tcp.port == 4352 && data)
```

Telnet with ZeeVee Bridge

```
(ip.addr == 10.5.33.2 && tcp.port = 23 && telnet)
```
