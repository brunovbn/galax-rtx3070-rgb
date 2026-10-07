# GALAX GeForce RTX 3070 1-Click OC (LHR) — LED control

RGB control for the GALAX / KFA2 GeForce RTX 3070 1-Click OC **LHR** revision (PCI `10DE:2488`, sub-system `10DE:153A`), a board that neither SignalRGB nor OpenRGB recognised out of the box. Everything here was reverse-engineered on one card on 2026-10-07 and verified visually.

*Em português: controle do LED da GALAX RTX 3070 1-Click OC LHR. O plugin do SignalRGB está em `signalrgb/`, o script avulso em `galax_led.py` e o patch do OpenRGB em `openrgb/`.*

## What is in here

| Path | What |
|---|---|
| `signalrgb/GALAX_Ampere_GPU.js` | SignalRGB user plugin. Copy to `Documents\WhirlwindFX\Plugins\GALAX\` and restart SignalRGB. |
| `galax_led.py` | Stand-alone Python script (NVAPI I2C via ctypes). `py -3 galax_led.py off` / `on` / no argument to probe. Only use it with the SignalRGB device disabled, otherwise both fight over the chip. |
| `openrgb/0001-*.patch` | Patch for OpenRGB: new sub-device id, signature `0x11`, mode re-write after colour writes. |
| `openrgb_mr.md`, `signalrgb_mr.md` | Merge request texts for the two upstream projects. |
| `docs/` | Notes and dumps gathered while reverse-engineering. |

## The controller

GALAX ships this board with NVIDIA's own sub-vendor id, so vendor-matching on `0x1B4C` never finds it. The LED controller is the GALAX "v1" family OpenRGB already drives on other boards, reachable over the GPU's I2C bus (NVAPI port 1) at address **0x23**.

| Register | Meaning |
|---|---|
| `0x00` | signature: **0x11** on this board (OpenRGB knows `0x27` / `0x30` on others) |
| `0x02` / `0x03` / `0x04` | R / G / B |
| `0x05` / `0x06` | mode: `0x00/0x01` static, `0x04/0x00` breathing, `0x84/0x02` rainbow, `0x84/0x40` cycle breathing |

Factory state read before touching anything: colour `(243, 245, 255)`, mode `0x00 / 0x20`. The chip keeps its last state across reboots.

**Quirk that cost an afternoon:** writing `0x02`-`0x04` only updates the registers (they read back fine) but the LED keeps the old colour. The LED is refreshed when a mode register is written afterwards. So every colour update must be followed by a mode write; a burst with no delay between the writes is fine. Writing the mode *before* the colour applies the *previous* colour.

Register dump at `0x23`, factory state:

```
00: 11 00 f3 f5 ff 00 20 05 00 01 00 00 c7 c7 c7 c7
10: c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7 c7
```

## How it was found

1. SignalRGB listed no GPU; its device-info page showed sub-vendor NVIDIA, sub-device `0x153A`.
2. NVAPI's Client Illumination API (the one Founders Edition cards use) reported zero zones.
3. Leftovers of GALAX Xtreme Tuner on disk gave the brand away; OpenRGB's `GalaxGPUControllerDetect.cpp` gave the I2C address and register map.
4. A Python probe over `NvAPI_I2CReadEx` found a device at `0x23` answering with coherent colour registers.
5. Pure red, pure blue and `(0, 155, 222)` writes, checked visually, pinned down the channel order and the mode-write quirk.

## Authors

Claude (Anthropic) with Bruno Vilas Boas Nunes, who owns the card and checked every colour by eye.

## License

MIT for the files in this repository. The OpenRGB patch is contributed under OpenRGB's GPL-2.0-or-later.
