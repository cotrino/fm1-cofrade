"""Flashea dist\\FM1_COFRADE.fwsc por USB-MIDI sin navegador (ruta 'legacy' forzada de sdk/WebUpdate.js).

Uso: python tools\\fm1_flash.py --go
Sin --go solo muestra lo que haria.
"""
import argparse, json, os, queue, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import fm1_midi as m

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('--go', action='store_true')
ap.add_argument('--fwsc', default=os.path.join(ROOT, 'dist', 'FM1_COFRADE.fwsc'))
ap.add_argument('--stock', action='store_true', help='paquete V15 original (identidad FM-1_015, loader ota-FM-1_015)')
ap.add_argument('--phase1-only', action='store_true')
args = ap.parse_args()
if args.stock and args.fwsc.endswith('FM1_COFRADE.fwsc'):
    args.fwsc = os.path.join(ROOT, 'vendor', 'fm1_open', 'sdk', 'firmware', 'FM-1_015.fwsc')

raw = open(args.fwsc, 'rb').read()
build_id = '' if args.stock else json.load(open(os.path.join(ROOT, 'dist', 'build-identity.json')))['build_id']
image = bytearray(len(raw) - 20)
product = ''
for i in range(20):
    image[i * 47:i * 47 + 47] = raw[i * 48:i * 48 + 47]
    mk = raw[i * 48 + 47]
    if mk != 125:
        product += chr((mk - i - 1) & 255)
image[940:] = raw[960:]
image = bytes(image)
loader_identity = 'ota-FM-1_015' if args.stock else 'ota-FM1C_' + build_id[:16]
print(f'paquete {len(raw)} B, imagen {len(image)} B, producto {product}, build {build_id[:16]}, loader {loader_identity}')

ARM = bytes([0xF0, 0x22, 0x24, 0x35, 0x7F, 0xF7])


def ident(link):
    r = link.query(17, ms=1000)
    return r.rstrip(b'\0').decode('ascii')


def find(timeout=0, want=None):
    end = time.time() + timeout
    while True:
        ins, outs = m.ports()
        for i, ni in enumerate(ins):
            for o, no in enumerate(outs):
                if ni == no and 'Wavetable' not in no:
                    try:
                        l = m.Link(i, o)
                    except OSError:
                        continue
                    try:
                        idn = ident(l)
                        if want is None or want(idn): return l, idn
                    except TimeoutError:
                        pass
                    l.close()
        if time.time() >= end: return None, None
        time.sleep(0.7)


def le(b, at, n): return int.from_bytes(b[at:at + n], 'little')


def serve(link, finish, idle):
    start = last = time.time(); done = bytearray((len(image) + 7) // 8); total = 0; shown = -1
    while True:
        if time.time() - last > idle: raise RuntimeError('el dispositivo dejo de pedir datos')
        if time.time() - start > max(idle * 3, 120): raise RuntimeError('tiempo maximo excedido')
        try: pk = m.parse(link.q.get(timeout=0.25))
        except queue.Empty: continue
        if not pk or pk[0] != 48 or len(pk[1]) != 8:
            if os.environ.get('FM1_DEBUG'): print('  ?', pk)
            continue
        p = pk[1]; addr = le(p, 1, 4); n = le(p, 5, 3)
        if os.environ.get('FM1_DEBUG'): print(f'  req tok={p[0]} addr={addr:#x} n={n}', flush=True)
        if not 0 < n <= 512: raise RuntimeError('longitud pedida invalida')
        if addr in (0xE0000000, 0xF0000000):
            if addr != finish or n != 8: raise RuntimeError('fase del loader inesperada')
            ok = m.frame(48, bytes([p[0], *p[1:8]]) + b'success\0')
            link.send(ok)
            end = time.time() + 0.6
            while time.time() < end:
                try: again = m.parse(link.q.get(timeout=0.1))
                except queue.Empty: continue
                if again and again[0] == 48 and len(again[1]) == 8 and le(again[1], 1, 4) == finish: link.send(ok)
            return
        if addr > len(image) or n > len(image) - addr: raise RuntimeError('lectura fuera de la imagen')
        last = time.time()
        time.sleep(0.01)
        link.send(m.frame(48, bytes([p[0], *p[1:8]]) + image[addr:addr + n]))
        for k in range(addr, addr + n):
            if not done[k >> 3] & (1 << (k & 7)): done[k >> 3] |= 1 << (k & 7); total += 1
        pc = total * 100 // len(image)
        if pc != shown and pc % 5 == 0: shown = pc; print(f'  {pc}%', flush=True)


link, idn = find(5)
if not link: sys.exit('No hay ningun FM1 respondiendo por MIDI.')
print('dispositivo:', idn)
if not args.go:
    link.close(); sys.exit('(simulacro) usa --go para escribir')
if idn.lower().startswith('ota-'):
    print('ya esta en modo actualizacion: se omite la fase 1')
    link.close(); link = None
else:
    try:
        try: cap = link.query(49, ms=1000)
        except TimeoutError: cap = None
        print('capacidad:', cap.hex() if cap else 'sin comando 49 -> ruta legacy forzada')
        assert ident(link) == idn
        print('1/3 cargando programa de actualizacion...')
        link.send(ARM)
        time.sleep(2)
        serve(link, 0xE0000000, int(os.environ.get("FM1_IDLE", "10")))
    finally:
        link.close()
    if args.phase1_only: sys.exit('fase 1 completada (--phase1-only)')
    time.sleep(3)
print('esperando loader', loader_identity)
link, idn2 = find(40, lambda s: s.lower().startswith('ota-'))
if not link: sys.exit('El loader no reaparecio; reconecta el USB y reintenta con el mismo comando.')
print('loader:', idn2)
try:
    print('2/3 escribiendo firmware...')
    link.send(ARM)
    time.sleep(2)
    serve(link, 0xF0000000, 180)
finally:
    link.close()
time.sleep(3)
print('3/3 reiniciando y verificando...')
link, idn3 = find(60, lambda s: s == product)
if not link: sys.exit('No reaparecio con la identidad ' + product)
try:
    if args.stock:
        print('identidad:', idn3, '\nVERIFICACION OK (V15 oficial)'); sys.exit(0)
    c = link.query(49, ms=2000)
    ok = c[:4] == b'FMC1' and c[5] == 7 and c[6] == 0 and c[14:46].hex() == build_id
    print('identidad:', idn3, '| build en dispositivo:', c[14:46].hex()[:16], '| estado:', c[6])
    print('VERIFICACION', 'OK' if ok else 'FALLO')
    sys.exit(0 if ok else 2)
finally:
    link.close()
