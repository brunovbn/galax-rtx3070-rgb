"""LED da GPU GALAX/KFA2 via I2C (NVAPI I2CReadEx/WriteEx), replicando o protocolo do OpenRGB.

Uso:
  python galax_led.py           -> sonda (só leitura) os endereços 0x23/0x32 (v1) e 0x50/0x51 (v2)
  python galax_led.py off       -> desliga (v1: cor preta, sem mexer no modo; v2: modo OFF + salvar)
  python galax_led.py on        -> liga (v1: cor original da placa, branco-azulado 243,245,255; v2: estático branco + salvar)

Placa do Bruno (07/10/2026): GALAX/KFA2 RTX 3070 LHR (dev 0x2488, subsys 10DE:153A), controlador v1 em 0x23
com reg0=0x11 (OpenRGB espera 0x27/0x30, por isso o OpenRGB não a detecta). Cor de fábrica lida: R=243 G=245 B=255,
modo de fábrica 0x05=0x00 / 0x06=0x20. Só cor preta NÃO apaga; é preciso modo estático (0x06=0x01) + preta.
"""
import ctypes, sys
from ctypes import c_uint32, c_uint8, c_void_p, c_int, POINTER, Structure, byref, sizeof

nv = ctypes.WinDLL("nvapi64.dll")
QI = nv.nvapi_QueryInterface; QI.restype = c_void_p; QI.argtypes = [c_uint32]

def fn(fid, argtypes):
    p = QI(fid)
    if not p: raise RuntimeError(f"QueryInterface(0x{fid:08x}) NULL")
    return ctypes.CFUNCTYPE(c_int, *argtypes)(p)

class I2CInfo(Structure):
    _fields_ = [("version", c_uint32), ("displayMask", c_uint32), ("bIsDDCPort", c_uint8), ("i2cDevAddress", c_uint8),
                ("pbI2cRegAddress", POINTER(c_uint8)), ("regAddrSize", c_uint32), ("pbData", POINTER(c_uint8)),
                ("cbSize", c_uint32), ("i2cSpeed", c_uint32), ("i2cSpeedKhz", c_uint32), ("portId", c_uint8), ("bIsPortIdSet", c_uint32)]

Initialize = fn(0x0150e828, [])
Unload = fn(0xd22bdd7e, [])
GetErrorMessage = fn(0x6c2d048c, [c_int, ctypes.c_char * 64])
EnumPhysicalGPUs = fn(0xe5ac921f, [POINTER(c_void_p * 64), POINTER(c_uint32)])
GetPCIIdentifiers = fn(0x2ddfb66e, [c_void_p, POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint32), POINTER(c_uint32)])
I2CReadEx = fn(0x4d7b0709, [c_void_p, POINTER(I2CInfo), POINTER(c_uint32)])
I2CWriteEx = fn(0x283ac65a, [c_void_p, POINTER(I2CInfo), POINTER(c_uint32)])

def err(st):
    b = (ctypes.c_char * 64)(); GetErrorMessage(st, b); return f"{st} ({b.value.decode(errors='replace')})"

def xfer(h, addr, reg, write=None):
    regb = c_uint8(reg); data = (c_uint8 * 1)(write if write is not None else 0)
    info = I2CInfo(); info.version = sizeof(I2CInfo) | (3 << 16)
    info.bIsDDCPort = 0; info.i2cDevAddress = (addr << 1) & 0xFF
    info.pbI2cRegAddress = ctypes.cast(byref(regb), POINTER(c_uint8)); info.regAddrSize = 1
    info.pbData = ctypes.cast(data, POINTER(c_uint8)); info.cbSize = 1
    info.i2cSpeed = 0xFFFF; info.i2cSpeedKhz = 0; info.portId = 1; info.bIsPortIdSet = 1
    unk = c_uint32(0)
    st = (I2CWriteEx if write is not None else I2CReadEx)(h, byref(info), byref(unk))
    return st, data[0]

def rd(h, addr, reg):
    st, v = xfer(h, addr, reg)
    return v if st == 0 else None

def wr(h, addr, reg, val):
    st, _ = xfer(h, addr, reg, val)
    if st != 0: raise RuntimeError(f"write {addr:#04x}[{reg:#04x}]={val:#04x}: {err(st)}")

def detect(h):
    found = []
    for addr in (0x23, 0x32, 0x50, 0x51):
        st, r0 = xfer(h, addr, 0x00)
        r1 = rd(h, addr, 0x01) if st == 0 else None
        print(f"  addr {addr:#04x}: reg0 -> {err(st) if st else f'{r0:#04x}'}; reg1 -> {None if r1 is None else f'{r1:#04x}'}")
        if st != 0: continue
        if addr == 0x32 and r0 in (0x27, 0x26) and r1 in (0x10, 0x20): found.append(("v1", addr))
        if addr == 0x23 and r0 in (0x27, 0x30, 0x11): found.append(("v1", addr))
        if addr == 0x51 and r0 == 0x80: found.append(("v2", addr))
        if addr == 0x50 and r0 == 0x01 and r1 == 0x08: found.append(("v2", addr))
    return found

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    st = Initialize()
    if st: raise SystemExit(f"Initialize: {err(st)}")
    try:
        gpus = (c_void_p * 64)(); n = c_uint32()
        EnumPhysicalGPUs(byref(gpus), byref(n))
        for i in range(n.value):
            h = gpus[i]
            dev = c_uint32(); sub = c_uint32(); rev = c_uint32(); ext = c_uint32()
            GetPCIIdentifiers(h, byref(dev), byref(sub), byref(rev), byref(ext))
            print(f"GPU {i}: dev={dev.value>>16:#06x} ven={dev.value&0xffff:#06x} subdev={sub.value>>16:#06x} subven={sub.value&0xffff:#06x}")
            found = detect(h)
            print(f"  controladores GALAX detectados: {found or 'nenhum'}")
            for kind, addr in found:
                if kind == "v1":
                    regs = {r: rd(h, addr, r) for r in (0x02, 0x03, 0x04, 0x05, 0x06)}
                    print(f"  v1@{addr:#04x} R,G,B={regs[2]},{regs[3]},{regs[4]} mode1={regs[5]:#04x} mode2={regs[6]:#04x}")
                    if mode == "off":
                        wr(h, addr, 0x02, 0); wr(h, addr, 0x03, 0); wr(h, addr, 0x04, 0)
                        wr(h, addr, 0x05, 0x00); wr(h, addr, 0x06, 0x01)      # modo estático por último: o chip aplica a cor ao gravar o modo
                        print("  -> v1: modo estático + cor preta (LED apagado; confirmado visualmente em 07/10/2026)")
                    elif mode == "on":
                        wr(h, addr, 0x02, 243); wr(h, addr, 0x03, 245); wr(h, addr, 0x04, 255)
                        wr(h, addr, 0x05, 0x00); wr(h, addr, 0x06, 0x20)      # modo de fábrica lido antes de mexer
                        print("  -> v1: cor e modo de fábrica restaurados")
                    if mode in ("off", "on"):
                        print("  leitura de volta R,G,B,m1,m2 =", [rd(h, addr, r) for r in (0x02, 0x03, 0x04, 0x05, 0x06)])
                else:
                    regs = {r: rd(h, addr, r) for r in (0x02, 0x03, 0x04, 0x21, 0x27, 0x2D, 0x30)}
                    print(f"  v2@{addr:#04x} R,G,B={regs[2]},{regs[3]},{regs[4]} speed={regs[0x21]} sync={regs[0x27]} bri={regs[0x2D]} mode={regs[0x30]:#04x}")
                    if mode == "off":
                        wr(h, addr, 0x30, 0x19); wr(h, addr, 0x40, 0x5A)
                        print("  -> v2: modo OFF gravado")
                    elif mode == "on":
                        wr(h, addr, 0x02, 255); wr(h, addr, 0x03, 255); wr(h, addr, 0x04, 255)
                        wr(h, addr, 0x30, 0x01); wr(h, addr, 0x40, 0x5A)
                        print("  -> v2: modo estático branco gravado")
    finally:
        Unload()

if __name__ == "__main__":
    main()
