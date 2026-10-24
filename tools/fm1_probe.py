"""Sonda de solo lectura: pregunta la identidad (cmd 17) y la capacidad (cmd 49) por cada par de puertos."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
import fm1_midi as m

ins, outs = m.ports()
print('IN ', ins); print('OUT', outs)
for i, ni in enumerate(ins):
    for o, no in enumerate(outs):
        if ni and ni == no or (len(ins) == 1 and len(outs) <= 2 and no != 'Microsoft GS Wavetable Synth'):
            print('probando', i, ni, '->', o, repr(no))
            try:
                l = m.Link(i, o)
                try:
                    print('  identidad:', l.query(17, ms=1000))
                    try: print('  capacidad:', l.query(49, ms=1000).hex())
                    except TimeoutError as e: print('  capacidad:', e)
                finally: l.close()
            except Exception as e:
                print('  error', e)
