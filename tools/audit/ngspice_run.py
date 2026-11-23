"""Headless ngspice driver using KiCad's bundled ngspice.dll via ctypes."""
import ctypes, sys, os

DLL = r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\bin\ngspice.dll"
d = ctypes.WinDLL(DLL)

CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int)
messages = []
def on_char(s, kind):
    try: messages.append(s.decode("utf-8", "replace"))
    except Exception: pass
    return 0
_cb = CALLBACK(on_char)

d.ngSpice_Init.argtypes = [ctypes.c_void_p]*6
d.ngSpice_Init.restype = ctypes.c_int
d.ngSpice_Command.argtypes = [ctypes.c_char_p]
d.ngSpice_Command.restype = ctypes.c_int

def run(deck, extra=None):
    deck = os.path.abspath(deck)
    rc = d.ngSpice_Init(_cb, None, None, None, None, None)
    print("ngSpice_Init rc =", rc)
    print("version rc =", d.ngSpice_Command(b"version"))
    print("source rc =", d.ngSpice_Command(("source " + deck).encode()))
    if extra:
        for c in extra:
            print(f"cmd {c!r} rc =", d.ngSpice_Command(c.encode()))
    print("--- ngspice output ---")
    for m in messages[:60]:
        print(m.rstrip())
    print("--- end output ---")

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2:])
