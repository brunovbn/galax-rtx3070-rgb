# OpenRGB merge request

**Título:** GalaxGPUv1Controller: add GALAX RTX 3070 1-Click OC LHR (10DE:153A), signature 0x11, re-apply mode after colour writes

**Branch:** galax-rtx3070-1click-oc-lhr (patch: 0001-GalaxGPUv1Controller-add-GALAX-RTX-3070-1-Click-OC-L.patch nesta pasta)

**Descrição (colar no GitLab):**

## Summary

Adds support for the LHR revision of the **GALAX GeForce RTX 3070 1-Click OC** to the GALAX v1 GPU controller, and fixes colour updates on that board.

| | |
|---|---|
| Vendor / Device | 0x10DE / 0x2488 (GA104, RTX 3070 LHR) |
| Sub-vendor / Sub-device | 0x10DE / 0x153A |
| I2C address | 0x23 (NVAPI I2C, port 1) |
| Register 0x00 (signature) | **0x11** (the detector currently only accepts 0x27 / 0x30) |
| VBIOS | 94.04.46.00.F6 |

## Changes

1. `pci_ids.h`: new `GALAX_RTX_3070_1_CLICK_OC_LHR_SUB_DEV 0x153A`.
2. `GalaxGPUControllerDetect.cpp`: accept signature `0x11` at address `0x23`; register the detector for `NVIDIA_RTX3070_LHR_DEV` / `0x153A`.
3. `GalaxGPUv1Controller`: the controller remembers the active mode registers and re-writes them after every colour write.

## Why the mode re-write

On this board, writing `0x02`-`0x04` only updates the registers (they read back correctly) but the LED keeps showing the previous colour. The LED is refreshed when a mode register (`0x05`/`0x06`) is written afterwards. Verified with pure red, pure blue and (0,155,222):

- colour only → LED unchanged
- colour then `0x06 = 0x01` → LED updates, no delay needed between the writes

Without this, Direct mode would never update the LED on this board. For the other v1 boards (0x27/0x30) the extra two writes are a no-op in static/Direct mode; in effect modes they re-write the same mode value that is already set.

## Register dump (factory state, address 0x23)

```
00: 11 00 f3 f5 ff 00 20 05 00 01 00 00 c7 c7 c7 c7
10: c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7
20: c7 ...
```

Factory colour is (243, 245, 255) with mode registers `0x00` / `0x20`. The controller keeps its last state across reboots.

## Testing

Tested on Windows 11 with the board above through the NVAPI I2C path (NvAPI_I2CReadEx / NvAPI_I2CWriteEx, port 1), the same path OpenRGB uses on Windows. Colours and modes verified visually. I do not have other GALAX v1 boards to regression-test the mode re-write.

Co-authored with Bruno Vilas Boas Nunes, who owns the board and verified every step visually.
