# SignalRGB merge request (gitlab.com/signalrgb/signal-plugins)

**Arquivo a enviar:** `Plugins/GALAX/GALAX_Ampere_GPU.js` (cópia de `C:\Users\Bruno\Documents\WhirlwindFX\Plugins\GALAX\GALAX_Ampere_GPU.js`)

**Título:** Add GALAX Ampere GPU plugin (GALAX GeForce RTX 3070 1-Click OC LHR, 10DE:153A)

**Descrição (colar no GitLab):**

## Summary

New SMBUS plugin for GALAX / KFA2 Ampere GPUs that use the "v1" LED controller at I2C address 0x23. Tested on a **GALAX GeForce RTX 3070 1-Click OC (LHR)**.

| | |
|---|---|
| Vendor / Device | 0x10DE / 0x2488 |
| Sub-vendor / Sub-device | 0x10DE / 0x153A (GALAX ships NVIDIA's own sub-vendor id) |
| I2C address | 0x23 |
| Register 0x00 (signature) | 0x11 |

## Protocol

| Register | Meaning |
|---|---|
| 0x00 | controller signature (0x11 on this board) |
| 0x02 / 0x03 / 0x04 | R / G / B |
| 0x05 / 0x06 | mode registers (0x00/0x01 static, 0x04/0x00 breathing, 0x84/0x02 rainbow, 0x84/0x40 cycle breathing) |

Quirk: writing the colour registers only updates them; the LED is refreshed when a mode register is written afterwards. The plugin writes R, G, B and then `0x06 = 0x01` on every Render (four byte writes per frame, single zone). Bursts with no delay between the writes work. The controller keeps its last state across reboots, so Shutdown Color (default black) is what the card shows while the OS boots.

## What the plugin does

- `Scan`: matches on the NVIDIA bus by vendor / sub-vendor / device / sub-device, returns 0x23.
- `Initialize`: logs register 0x00, writes static mode and black.
- `Render`: R, G, B then mode register.
- `Shutdown`: Shutdown Color (black on system suspend).

The ID table also carries the two other v1 boards OpenRGB lists at 0x23 (RTX 3070 1-Click OC non-LHR 0x146B and RTX 3080 SG 0x1455). They were **not** tested here; happy to drop them if you prefer only verified ids.

`ImageUrl()` points at the generic PNY GPU image for now because there is no GALAX asset yet.

## Testing

SignalRGB 2.5.74, Windows 11. Verified: detection and name in the Devices page, Forced colour (0,155,222) shows as light blue on the card, Canvas mode follows the active effect, device disable/enable, SignalRGB restart.

Authored by Claude (Anthropic) with Bruno Vilas Boas Nunes, who owns the card and verified every step visually.
