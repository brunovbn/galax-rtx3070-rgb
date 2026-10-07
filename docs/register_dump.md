# Register dump — GALAX RTX 3070 1-Click OC LHR, I2C address 0x23 (NVAPI port 1)

Factory state, 2026-10-07, before any write:

```
00: 11 00 f3 f5 ff 00 20 05 00 01 00 00 c7 c7 c7 c7
10: c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7
20: c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7
30: c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7
```

Addresses 0x32, 0x50 and 0x51 (the other GALAX controllers OpenRGB knows) return NVAPI_ERROR (no device).

## Experiments (all checked by eye on the card)

| Writes, in order | LED |
|---|---|
| factory `0x00/0x20`, colour `0,0,0` | still white (no change) |
| mode `0x00/0x01` with colour already `0,0,0` | off |
| mode `0x00/0x01` then colour `0,0,0` (fast burst) | blue — applied the previous colour; last writes not applied |
| colour `0,0,0` then mode `0x00/0x01` | off |
| colour `255,0,0` then mode | red |
| colour `0,0,255` then mode | blue |
| colour `0,155,222`, no mode write | unchanged (still blue) |
| colour `0,155,222` then `0x06=0x01`, no delays | light blue |
| SignalRGB streaming R,G,B without mode write | stuck on a stale colour ("dark green") |

Conclusion: the LED is refreshed from the colour registers when a mode register is written. No inter-write delay is needed.

## PCI identity

```
PCI\VEN_10DE&DEV_2488&SUBSYS_153A10DE&REV_A1
VBIOS 94.04.46.00.f6, GPU part 2488-302-A1
```

NVAPI Client Illumination API (NvAPI_GPU_ClientIllumDevicesGetInfo / ZonesGetInfo): 0 devices, 0 zones.
