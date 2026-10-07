export function Name() { return "GALAX Ampere GPU"; }
export function Publisher() { return "Claude (Anthropic) & Bruno Vilas Boas Nunes"; }
export function Type() { return "SMBUS"; }
export function Size() { return [3, 1]; }
export function DefaultPosition() { return [5, 2]; }
export function DefaultScale() { return 2.5; }
export function LedNames() { return vLedNames; }
export function LedPositions() { return vLedPositions; }
export function DeviceType() { return "gpu"; }
export function ConflictingProcesses() { return ["XtremeTuner.exe", "XtremeTunerPlus.exe"]; }
/* global
shutdownColor:readonly
LightingMode:readonly
forcedColor:readonly
*/
export function ControllableParameters() {
	return [
		{"property":"shutdownColor", "group":"lighting", "label":"Shutdown Color", description: "This color is applied to the device when the System, or SignalRGB is shutting down", "min":"0", "max":"360", "type":"color", "default":"#000000"},
		{"property":"LightingMode", "group":"lighting", "label":"Lighting Mode", description: "Determines where the device's RGB comes from. Canvas will pull from the active Effect, while Forced will override it to a specific color", "type":"combobox", "values":["Canvas", "Forced"], "default":"Canvas"},
		{"property":"forcedColor", "group":"lighting", "label":"Forced Color", description: "The color used when 'Forced' Lighting Mode is enabled", "min":"0", "max":"360", "type":"color", "default":"#009bde"},
	];
}
export function DeviceMessages() {
	return [
		{property: "Single Zone Control", message:"Single RGB Zone", tooltip: "This GPU's controller exposes a single RGB zone."},
	];
}

const vLedNames = [ "GPU" ];
const vLedPositions = [ [1, 0] ];

/*
 * GALAX / KFA2 "v1" LED controller (same family OpenRGB drives at 0x23 / 0x32).
 *
 * Registers (I2C address 0x23, NVAPI port 1):
 *   0x00  controller signature (0x11 on the RTX 3070 LHR 153A; OpenRGB knows 0x27 / 0x30 on other boards)
 *   0x02  Red
 *   0x03  Green
 *   0x04  Blue
 *   0x05  Mode register 1
 *   0x06  Mode register 2   (0x00/0x01 = static, 0x04/0x00 = breathing, 0x84/0x02 = rainbow, 0x84/0x40 = cycle breathing)
 *
 * Quirk measured on the 3070 LHR: writing 0x02-0x04 only updates the registers; the LED itself is refreshed
 * when a mode register (0x05/0x06) is written. So every colour update must be followed by a mode write.
 * Bursts with no delay between the writes work fine. Factory state read from this board:
 * R,G,B = 243,245,255 with mode 0x00/0x20. The controller keeps the last state across reboots.
 */

/** @param {FreeAddressBus} bus */
export function Scan(bus) {
	const FoundAddresses = [];

	if (!bus.IsNvidiaBus()) {
		return [];
	}

	for(const GPU of GalaxGPUIDs) {
		if(CheckForIdMatch(bus, GPU)) {
			bus.log(`Found GALAX GPU by PCI ids: [${GPU.Name}] at address 0x${GPU.Address.toString(16)}`, {toFile : true});
			FoundAddresses.push(GPU.Address);
		}
	}

	return FoundAddresses;
}

export function Initialize() {
	const signature = bus.ReadByte(GalaxGPU.registers.Signature);
	device.log(`GALAX controller signature register 0x00 = 0x${signature.toString(16)}`, {toFile : true});

	// Colour first, then mode: the controller applies the colour on the mode write.
	GalaxGPU.setMode(GalaxGPU.modes.static);
	sendColors("#000000");
	SetGPUNameFromBusIds();
}

export function Render() {
	sendColors();
}

export function Shutdown(SystemSuspending) {
	if(SystemSuspending){
		sendColors("#000000"); // Go Dark on System Sleep/Shutdown
	}else{
		sendColors(shutdownColor);
	}
}

function CheckForIdMatch(bus, Gpu) {
	return Gpu.Vendor === bus.Vendor() &&
		Gpu.SubVendor === bus.SubVendor() &&
		Gpu.Device === bus.Product() &&
		Gpu.SubDevice === bus.SubDevice();
}

function SetGPUNameFromBusIds() {
	for(const GPU of GalaxGPUIDs) {
		if(CheckForIdMatch(bus, GPU)) {
			device.setName(GPU.Name);
		}
	}
}

function sendColors(overrideColor) {
	const iPxX = vLedPositions[0][0];
	const iPxY = vLedPositions[0][1];
	let color;

	if(overrideColor) {
		color = hexToRgb(overrideColor);
	} else if (LightingMode === "Forced") {
		color = hexToRgb(forcedColor);
	} else {
		color = device.color(iPxX, iPxY);
	}

	bus.WriteByte(GalaxGPU.registers.Red, color[0]);
	bus.WriteByte(GalaxGPU.registers.Green, color[1]);
	bus.WriteByte(GalaxGPU.registers.Blue, color[2]);
	// The controller only pushes the colour registers to the LED when a mode register is written,
	// so re-write Mode2 (static) after every colour update. Four byte writes per frame, single zone.
	bus.WriteByte(GalaxGPU.registers.Mode2, GalaxGPU.modes.static[1]);
}

class GalaxGPUController {
	constructor() {
		this.registers = {
			Signature : 0x00,
			Red       : 0x02,
			Green     : 0x03,
			Blue      : 0x04,
			Mode1     : 0x05,
			Mode2     : 0x06,
		};
		this.modes = {
			static         : [0x00, 0x01],
			breathing      : [0x04, 0x00],
			rainbow        : [0x84, 0x02],
			cycleBreathing : [0x84, 0x40],
		};
	}
	setMode(mode) {
		bus.WriteByte(this.registers.Mode1, mode[0]);
		bus.WriteByte(this.registers.Mode2, mode[1]);
	}
}
const GalaxGPU = new GalaxGPUController();

class GPUIdentifier {
	constructor(Vendor, SubVendor, Device, SubDevice, Address, Name, Model = "") {
		this.Vendor = Vendor;
		this.SubVendor = SubVendor;
		this.Device = Device;
		this.SubDevice = SubDevice;
		this.Address = Address;
		this.Name = Name;
		this.Model = Model;
	}
}

class GalaxGPUIdentifier extends GPUIdentifier {
	constructor(Device, SubDevice, Name, Address = 0x23, Model = "") {
		// GALAX / KFA2 boards ship with NVIDIA's own sub-vendor id (0x10DE).
		super(0x10DE, 0x10DE, Device, SubDevice, Address, Name, Model);
	}
}

export function BrandGPUList() { return GalaxGPUIDs; }

const GalaxGPUIDs =
[
	new GalaxGPUIdentifier(0x2488, 0x153A, "GALAX GeForce RTX 3070 1-Click OC (LHR)"), // measured: signature 0x11 at 0x23
	// From OpenRGB's GalaxGPUControllerDetect.cpp (same v1 controller, address 0x23):
	new GalaxGPUIdentifier(0x2484, 0x146B, "GALAX GeForce RTX 3070 1-Click OC"),
	new GalaxGPUIdentifier(0x2206, 0x1455, "GALAX GeForce RTX 3080 SG"),
];

function hexToRgb(hex) {
	const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
	const colors = [];
	colors[0] = parseInt(result[1], 16);
	colors[1] = parseInt(result[2], 16);
	colors[2] = parseInt(result[3], 16);

	return colors;
}

export function ImageUrl() {
	return "https://assets.signalrgb.com/devices/brands/pny/gpus/gpu.png";
}
