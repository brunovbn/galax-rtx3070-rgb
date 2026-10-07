# SignalRGB — texto para o fórum (Plugin Development) ou Discord (#plugin-dev)

**Título:** New SMBUS plugin: GALAX GeForce RTX 3070 1-Click OC LHR (10DE:153A) — GALAX v1 controller at 0x23

**Corpo:**

Hi all,

I wrote a SignalRGB user plugin for the **GALAX GeForce RTX 3070 1-Click OC (LHR)**, which SignalRGB does not detect today. Sharing it here so it can be reviewed for the official plugin set (the signal-plugins GitLab repo does not allow forks, and plugins@whirlwindfx.com bounces with "recipient address rejected").

Plugin file: https://github.com/brunovbn/galax-rtx3070-rgb/blob/main/signalrgb/GALAX_Ampere_GPU.js
Repo with notes, register dump and a stand-alone probe script: https://github.com/brunovbn/galax-rtx3070-rgb

**Board**
- Vendor / Device: 0x10DE / 0x2488
- Sub-vendor / Sub-device: 0x10DE / 0x153A (GALAX ships NVIDIA's own sub-vendor id, so vendor matching on 0x1B4C never finds it)
- I2C address 0x23, register 0x00 (signature) reads 0x11

**Protocol** (GALAX "v1" controller, same family OpenRGB drives on other GALAX boards)
- 0x02 / 0x03 / 0x04 = R / G / B
- 0x05 / 0x06 = mode (0x00/0x01 static, 0x04/0x00 breathing, 0x84/0x02 rainbow, 0x84/0x40 cycle breathing)
- Quirk: the colour registers only take effect when a mode register is written afterwards, so Render writes R, G, B and then 0x06 = 0x01 (four byte writes per frame, single zone). No inter-write delay needed. The controller keeps its last state across reboots.

**Plugin**
- Scan by PCI ids on the NVIDIA bus, returns 0x23
- Initialize: logs the signature, static mode, black
- Render: R, G, B, mode
- Shutdown: Shutdown Color (black on suspend)
- ImageUrl points at the generic PNY GPU image for now
- The id table also lists the two other v1 boards OpenRGB has at 0x23 (3070 1-Click OC non-LHR 0x146B, 3080 SG 0x1455), untested here; happy to drop them.

Tested on SignalRGB 2.5.74 / Windows 11: detection and name, Forced colour (0,155,222) shows light blue on the card, Canvas follows the effect, disable/enable, restart.

A matching merge request is open on OpenRGB: https://gitlab.com/CalcProgrammer1/OpenRGB/-/merge_requests/3712

Written by Claude (Anthropic) together with me; I own the card and checked every colour by eye.
