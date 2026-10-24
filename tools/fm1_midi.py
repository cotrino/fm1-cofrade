"""SysEx por winmm (sin navegador) y trama del protocolo de actualizacion FM1 (ver sdk/WebUpdate.js)."""
import ctypes, os, queue, sys, threading, time
from ctypes import wintypes

w = ctypes.WinDLL('winmm')
HMIDIIN = ctypes.c_void_p
CB = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, wintypes.UINT, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t)


class Caps(ctypes.Structure):
    _fields_ = [('m', wintypes.WORD), ('p', wintypes.WORD), ('v', wintypes.UINT), ('n', ctypes.c_wchar * 32), ('x', ctypes.c_byte * 16)]


class Hdr(ctypes.Structure):
    _fields_ = [('data', ctypes.c_void_p), ('buflen', wintypes.DWORD), ('rec', wintypes.DWORD), ('user', ctypes.c_size_t),
                ('flags', wintypes.DWORD), ('next', ctypes.c_void_p), ('res', ctypes.c_size_t), ('off', wintypes.DWORD),
                ('r', ctypes.c_size_t * 4)]


def ports():
    ins, outs = [], []
    for lst, num, cap in ((ins, w.midiInGetNumDevs, w.midiInGetDevCapsW), (outs, w.midiOutGetNumDevs, w.midiOutGetDevCapsW)):
        for i in range(num()):
            c = Caps(); cap(ctypes.c_size_t(i), ctypes.byref(c), ctypes.sizeof(c)); lst.append(c.n)
    return ins, outs


def pack7(data):
    out, bits, value = [], 0, 0
    for b in data:
        value |= b << bits; bits += 8
        while bits >= 7:
            out.append(value & 127); value >>= 7; bits -= 7
    if bits: out.append(value & 127)
    return out


def frame(cmd, payload=b''):
    s = sum(payload) & 255
    n = len(payload)
    return bytes([0xF0] + pack7([0, 89, cmd, n & 255, n >> 8, 0, *payload, (~s) & 255]) + [0xF7])


def parse(b):
    if len(b) < 10 or b[0] != 0xF0 or b[-1] != 0xF7: return None
    raw, bits, value = [], 0, 0
    for x in b[1:-1]:
        if x > 127: return None
        value |= x << bits; bits += 7
        if bits >= 8: raw.append(value & 255); value >>= 8; bits -= 8
    if bits >= 7 or value or len(raw) < 7 or raw[0] != 0 or raw[1] != 89: return None
    if raw[3] | raw[4] << 8 | raw[5] << 16 != len(raw) - 7: return None
    if sum(raw[6:]) & 255 != 255: return None
    return raw[2], bytes(raw[6:-1])


class Link:
    def __init__(self, in_idx, out_idx):
        self.q = queue.Queue(); self.readd = queue.Queue()
        self.hin = HMIDIIN(); self.hout = ctypes.c_void_p()
        self.cb = CB(self._cb)
        r = w.midiInOpen(ctypes.byref(self.hin), in_idx, self.cb, 0, 0x30000)
        if r: raise OSError(f'midiInOpen {r}')
        self.bufs = []
        for _ in range(8):
            buf = ctypes.create_string_buffer(1024); h = Hdr(); h.data = ctypes.cast(buf, ctypes.c_void_p); h.buflen = 1024
            w.midiInPrepareHeader(self.hin, ctypes.byref(h), ctypes.sizeof(h)); w.midiInAddBuffer(self.hin, ctypes.byref(h), ctypes.sizeof(h))
            self.bufs.append((buf, h))
        threading.Thread(target=self._pump, daemon=True).start()
        w.midiInStart(self.hin)
        r = w.midiOutOpen(ctypes.byref(self.hout), out_idx, 0, 0, 0)
        if r: raise OSError(f'midiOutOpen {r}')

    def _cb(self, hnd, msg, inst, p1, p2):
        # winmm no permite llamar a midiInAddBuffer dentro del callback: lo hace un hilo.
        if msg == 0x3C4:  # MIM_LONGDATA
            h = Hdr.from_address(p1)
            if h.rec: self.q.put(ctypes.string_at(h.data, h.rec))
            self.readd.put(p1)
        elif msg == 0x3C5:  # MIM_LONGERROR
            self.readd.put(p1)

    def _pump(self):
        while True:
            p1 = self.readd.get()
            if p1 is None or self._closing: return
            w.midiInAddBuffer(self.hin, ctypes.c_void_p(p1), ctypes.sizeof(Hdr))

    _closing = False

    def send(self, data):
        buf = ctypes.create_string_buffer(data, len(data)); h = Hdr(); h.data = ctypes.cast(buf, ctypes.c_void_p); h.buflen = len(data)
        w.midiOutPrepareHeader(self.hout, ctypes.byref(h), ctypes.sizeof(h))
        r = w.midiOutLongMsg(self.hout, ctypes.byref(h), ctypes.sizeof(h))
        if r: raise OSError(f'midiOutLongMsg {r}')
        while not (h.flags & 1): time.sleep(0.0005)  # MHDR_DONE
        w.midiOutUnprepareHeader(self.hout, ctypes.byref(h), ctypes.sizeof(h))

    def query(self, cmd, payload=b'', ms=1500):
        while not self.q.empty(): self.q.get_nowait()
        self.send(frame(cmd, payload))
        end = time.time() + ms / 1000
        while time.time() < end:
            try: raw = self.q.get(timeout=0.1)
            except queue.Empty: continue
            p = parse(raw)
            if p and p[0] == cmd: return p[1]
        raise TimeoutError(f'sin respuesta al comando {cmd}')

    def close(self):
        self._closing = True; self.readd.put(None)
        w.midiInStop(self.hin); w.midiInReset(self.hin); time.sleep(0.1)
        for _, h in self.bufs: w.midiInUnprepareHeader(self.hin, ctypes.byref(h), ctypes.sizeof(h))
        w.midiInClose(self.hin)
        w.midiOutReset(self.hout); w.midiOutClose(self.hout)


if __name__ == '__main__':
    ins, outs = ports()
    print('IN ', ins); print('OUT', outs)
