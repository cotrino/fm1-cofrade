#!/usr/bin/env python3
"""Genera overlay/app/cofrade_marchas.h a partir de las marchas escritas aqui.

Notacion de pista melodica (un compas por segmento, separados por '|'):
    NOTA[M|m][!|^]:duracion[~]     duracion en pasos (semicorcheas)
    r:duracion                     silencio
  M / m  = acorde mayor / menor sobre la nota (sin sufijo: nota sola)
  !  acento   ^  suave   ~  ligado con lo siguiente (pads)
Notacion de percusion: una linea de 'x' (normal), 'X' (acento), 'g' (fantasma)
y '.' por cada paso, compases separados por '|'. Las claves son pads 808.

Todas las musicas son composiciones ORIGINALES "al estilo de"; no se incluye
ninguna transcripcion de obras protegidas ni de memoria de obras concretas.
"""
import pathlib
import re
import sys

PADS = dict(BD=0, SD=1, LT=2, MT=3, HT=4, RS=5, CP=6, CB=7, CY=8, OH=9, CH=10)
TONES = dict(CORNETA=0, TROMPETA=1, ORGANO=2, TUBA=3, FLISCORNO=4, CLARINETE=5,
             FLAUTA=6, CAMPANA=7, GUITARRA=8, OBOE=9, TROMBON=10, SAETA=11,
             CORO=12, BOMBARDINO=13, SAXO=14, CAMPANILLA=15)
SEMI = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)
TOKEN = re.compile(r'^([A-G][#b]?\d|r)([Mm]?)([!^]?):(\d+)(~?)$')
CHORD = dict(M=1, m=2)
VEL = {'': 92, '!': 110, '^': 68}
DRUM_VEL = {'x': 92, 'X': 116, 'g': 54}


def midi(name):
    n = SEMI[name[0]]
    rest = name[1:]
    if rest[0] == '#':
        n += 1
        rest = rest[1:]
    elif rest[0] == 'b':
        n -= 1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + n


def melodic(text, bar):
    events, step = [], 0
    bars_ = [b.strip() for b in text.split('|')]
    assert len(bars_) == 4, (len(bars_), text)
    for number, chunk in enumerate(bars_):
        used = 0
        for tok in chunk.split():
            m = TOKEN.match(tok)
            assert m, 'token invalido: ' + tok
            pitch, quality, mark, length, tie = m.groups()
            length = int(length)
            assert 1 <= length <= 16, tok
            if pitch != 'r':
                note = midi(pitch)
                assert 24 <= note <= 100, tok
                events.append((step + used, note, VEL[mark] | (0x80 if tie else 0),
                               ((length - 1) << 4) | CHORD.get(quality, 0)))
            used += length
        assert used == bar, 'compas %d suma %d en: %s' % (number + 1, used, chunk)
        step += bar
    return events


def drums(pattern, bar):
    cells = {}
    for pad, text in pattern.items():
        bars_ = text.split('|')
        assert len(bars_) == 4 and all(len(b) == bar for b in bars_), (pad, text)
        for step, ch in enumerate(''.join(bars_)):
            if ch != '.':
                mask, vel = cells.get(step, (0, 0))
                cells[step] = (mask | (1 << PADS[pad]), max(vel, DRUM_VEL[ch]))
    return [(s, m & 255, v, m >> 8) for s, (m, v) in sorted(cells.items())]


def fm(tone, level, rev, dly, notes):
    return dict(src='DX7', tone=TONES[tone], level=level, sends=rev + 16 * dly, notes=notes)


def pluck(tone, level, rev, dly, notes):
    return dict(src='PLUCK', tone=tone, level=level, sends=rev + 16 * dly, notes=notes)


def perc(level, pattern):
    return dict(src='808', tone=0, level=level, sends=0, notes=pattern)


def bars(*b):
    return ' | '.join(b)


LENTO = dict(
    BD='x.......x.......|x.......x.......|x.......x.......|x.......x.......',
    SD='X...g.g.X...g.g.|X...g.g.X...g.g.|X...g.g.X...g.g.|X...g.g.XgXgXgXg',
    CB='x...............|................|x...............|................')

SONGS = [
    # 0 ------------------------------------------------------------ aprender: toque de corneta
    dict(name='DIANA ILLO', bpm=120, swing=0, decay=60, delay=2, fb=24, fx=60, pages=0, tracks=[
        fm('CORNETA', 100, 3, 1, bars('G4:2 G4:2 C5:6 r:2 E5:4', 'G5:6 r:2 E5:4 C5:4',
                                      'G4:2 G4:2 C5:6 r:2 E5:4', 'G5:4 E5:4 C5:4 G4:4')),
        fm('TROMPETA', 88, 3, 1, bars('E4:2 E4:2 G4:6 r:2 C5:4', 'E5:6 r:2 C5:4 G4:4',
                                      'E4:2 E4:2 G4:6 r:2 C5:4', 'E5:4 C5:4 G4:4 E4:4')),
        fm('TUBA', 92, 0, 0, bars('C3:8 G3:8', 'C3:8 G3:8', 'C3:8 G3:8', 'G3:8 C3:8')),
        perc(86, dict(BD='x.......x.......|x.......x.......|x.......x.......|x...x...x.......',
                      SD='....x.......x...|....x.......x...|....x.......x...|....x...x.xXxxxX',
                      CY='................|................|................|x...............')),
    ]),
    # 1 ------------------------------------------------------------ aprender: tambores
    dict(name='REDOBLE ILLO', bpm=100, swing=0, decay=40, delay=0, fb=10, fx=30, pages=0, tracks=[
        fm('CAMPANA', 84, 4, 2, bars('C5:4 r:12', 'r:16', 'C5:4 r:12', 'C5:4 G4:4 C5:8')),
        fm('TUBA', 90, 0, 0, bars('G2:16', 'G2:16', 'G2:16', 'G2:16')),
        perc(92, dict(
            SD='x...x...x...x...|x.x.x.x.x.x.x.x.|XxxxXxxxXxxxXxxx|XxxXxXxxXxxXxxXX',
            BD='x.......x.......|x.......x.......|x.......x.......|x.......x...x...',
            CB='X...x...x...x...|X...x...x...x...|X...x...x...x...|X...x...x...x...',
            CP='................|................|................|............x.x.',
            CY='................|................|................|X...............')),
    ]),
    # 2 ------------------------------------------------------------ aprender: cadencia andaluza
    dict(name='POR ANDALUZA', bpm=88, swing=0, decay=72, delay=3, fb=30, fx=70, pages=0, tracks=[
        fm('OBOE', 96, 5, 3, bars('A4:4 C5:4 B4:4 A4:4', 'G4:4 B4:4 A4:4 G4:4',
                                  'F4:4 A4:4 G4:4 F4:4', 'E4:6 F4:2 E4:8')),
        pluck(0, 92, 4, 2, bars(
            'A3:2 E4:2 A4:2 C5:2 A4:2 E4:2 A3:2 E4:2', 'G3:2 D4:2 G4:2 B4:2 G4:2 D4:2 G3:2 D4:2',
            'F3:2 C4:2 F4:2 A4:2 F4:2 C4:2 F3:2 C4:2', 'E3:2 B3:2 E4:2 G#4:2 E4:2 B3:2 E3:2 B3:2')),
        fm('TUBA', 88, 0, 0, bars('A2:8 A2:8', 'G2:8 G2:8', 'F2:8 F2:8', 'E2:8 E2:8')),
        perc(78, dict(CP='....x.......x...|....x.......x...|....x.......x...|....x.......x...',
                      BD='x.......x.......|x.......x.......|x.......x.......|x.......x.......',
                      RS='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x...x...x.')),
    ]),
    # 3 ------------------------------------------------------------ saeta
    dict(name='SAETA BALCON', bpm=56, swing=0, decay=88, delay=4, fb=44, fx=86, pages=0, tracks=[
        fm('SAETA', 100, 7, 3, bars('B4:4 C5:2 B4:2 A4:4 G#4:2 F4:2', 'E4:8 F4:2 G#4:2 F4:2 E4:2',
                                    'B4:4 C5:2 D5:2 C5:2 B4:2 A4:2 G#4:2', 'F4:2 G#4:2 F4:4 E4:8')),
        pluck(1, 86, 5, 2, bars(
            'E3:2 B3:2 E4:2 G#4:2 E4:2 B3:2 E3:2 B3:2', 'E3:2 B3:2 E4:2 G#4:2 E4:2 B3:2 E3:2 B3:2',
            'F3:2 C4:2 F4:2 A4:2 F4:2 C4:2 F3:2 C4:2', 'E3:2 B3:2 E4:2 G#4:2 E4:2 B3:2 E3:2 B3:2')),
        fm('CORO', 64, 8, 0, bars('E3M:16~', 'E3M:16~', 'F3M:16~', 'E3M:16~')),
        perc(70, dict(CB='x...............|................|x...............|................',
                      BD='................|........x.......|................|x...............')),
    ]),
    # 4 ------------------------------------------------------------ marcha de palio
    dict(name='PASO LENTO', bpm=66, swing=0, decay=80, delay=3, fb=32, fx=78, pages=0, tracks=[
        fm('TROMPETA', 100, 5, 3, bars('G4:6 G4:2 C5:4 B4:2 C5:2', 'Ab4:6 Ab4:2 C5:4 Bb4:2 Ab4:2',
                                       'B4:4 D5:4 B4:4 G4:4', 'C5:8 G4:8')),
        fm('FLISCORNO', 86, 5, 3, bars('Eb4:6 Eb4:2 G4:4 F4:2 G4:2', 'F4:6 F4:2 Ab4:4 G4:2 F4:2',
                                       'G4:4 B4:4 G4:4 D4:4', 'G4:8 Eb4:8')),
        fm('TUBA', 92, 0, 0, bars('C3:8 G3:8', 'F3:8 C3:8', 'G3:8 D3:8', 'C3:16')),
        perc(84, LENTO),
    ]),
    # 5 ------------------------------------------------------------ chicotÃ¡
    dict(name='LA CHICOTA', bpm=84, swing=0, decay=62, delay=2, fb=26, fx=64, pages=0, tracks=[
        fm('CORNETA', 98, 3, 2, bars('D5:4 D5:2 F5:2 E5:4 D5:4', 'C5:4 C5:2 E5:2 D5:4 C5:4',
                                     'Bb4:4 Bb4:2 D5:2 C5:4 Bb4:4', 'A4:6 C#5:2 D5:8')),
        fm('TROMBON', 84, 3, 1, bars(
            'r:2 D3m:2 r:2 D3m:2 r:2 D3m:2 r:2 D3m:2', 'r:2 C3M:2 r:2 C3M:2 r:2 C3M:2 r:2 C3M:2',
            'r:2 Bb2M:2 r:2 Bb2M:2 r:2 Bb2M:2 r:2 Bb2M:2', 'r:2 A2M:2 r:2 A2M:2 r:2 A2M:2 r:2 A2M:2')),
        fm('TUBA', 94, 0, 0, bars('D3:4 A2:4 D3:4 A2:4', 'C3:4 G2:4 C3:4 G2:4',
                                  'Bb2:4 F2:4 Bb2:4 F2:4', 'A2:4 E3:4 A2:8')),
        perc(90, dict(BD='x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...',
                      SD='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x...xxxxxX',
                      CY='X...............|................|X...............|X...............')),
    ]),
    # 6 ------------------------------------------------------------ a la iguala
    dict(name='A LA IGUALA', bpm=76, swing=0, decay=58, delay=2, fb=24, fx=60, pages=0, tracks=[
        fm('TROMPETA', 98, 4, 2, bars('E5:2 E5:2 G5:4 r:2 E5:2 D5:4', 'C5:4 B4:4 A4:4 B4:4',
                                      'E5:2 E5:2 G5:4 r:2 E5:2 D5:4', 'B4:4 E5:12')),
        fm('CAMPANA', 80, 5, 3, bars('B4:2 r:14', 'r:16', 'B4:2 r:14', 'r:16')),
        fm('TUBA', 92, 0, 0, bars('E3:8 B2:8', 'A2:8 E3:8', 'E3:8 B2:8', 'B2:8 E3:8')),
        perc(92, dict(CB='X...x...x...x...|X...x...x...x...|X...x...x...x...|X...x...x...x...',
                      BD='x.....x.x.......|x.....x.x.......|x.....x.x.......|x.....x.x...x...',
                      SD='................|......x.......x.|................|..x.x.x.xxxxxXXX',
                      CP='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|................')),
    ]),
    # 7 ------------------------------------------------------------ marcha fÃºnebre
    dict(name='FUNEBRE ARTE', bpm=52, swing=0, decay=90, delay=4, fb=40, fx=84, pages=0, tracks=[
        fm('OBOE', 96, 6, 3, bars('G4:6 G4:2 G4:4 Eb4:4', 'Ab4:6 Ab4:2 Ab4:4 F4:4',
                                  'G4:6 G4:2 F4:4 Eb4:4', 'D4:8 C4:8')),
        fm('TROMBON', 84, 5, 2, bars('Eb4:6 Eb4:2 Eb4:4 C4:4', 'F4:6 F4:2 F4:4 D4:4',
                                     'Eb4:6 Eb4:2 D4:4 C4:4', 'B3:8 G3:8')),
        fm('TUBA', 94, 0, 0, bars('C3:8 G2:8', 'F3:8 C3:8', 'C3:8 G2:8', 'G2:8 C3:8')),
        perc(80, dict(BD='x...............|x...............|x...............|x.......x.......',
                      SD='g.g.g.g.g.g.g.g.|g.g.g.g.g.g.g.g.|g.g.g.g.g.g.g.g.|g.g.g.g.XgXgXgXg',
                      CB='x...............|................|x...............|................')),
    ]),
    # 8 ------------------------------------------------------------ madrugÃ¡
    dict(name='LA MADRUGA', bpm=72, swing=0, decay=84, delay=3, fb=36, fx=80, pages=0, tracks=[
        fm('CORNETA', 98, 6, 3, bars('E5:4 E5:2 F5:2 E5:4 D5:4', 'C5:4 C5:2 D5:2 C5:4 B4:4',
                                     'A4:4 A4:2 B4:2 C5:4 D5:4', 'E5:12 r:4')),
        fm('FLAUTA', 78, 6, 4, bars(
            'A4:2 C5:2 E5:2 C5:2 A4:2 C5:2 E5:2 C5:2', 'A4:2 C5:2 F5:2 C5:2 A4:2 C5:2 F5:2 C5:2',
            'A4:2 D5:2 F5:2 D5:2 A4:2 D5:2 F5:2 D5:2', 'B4:2 E5:2 G#5:2 E5:2 B4:2 E5:2 G#5:2 E5:2')),
        fm('TUBA', 92, 0, 0, bars('A2:8 E3:8', 'F2:8 C3:8', 'D3:8 A2:8', 'E3:8 E3:8')),
        perc(82, dict(BD='x.......x.......|x.......x.......|x.......x.......|x.......x.......',
                      SD='X.g.g.g.X.g.g.g.|X.g.g.g.X.g.g.g.|X.g.g.g.X.g.g.g.|X.g.g.g.XgXgXgXg',
                      CB='x...............|................|x...............|................')),
    ]),
    # 9 ------------------------------------------------------------ cornetas y tambores
    dict(name='CORNETAS YA', bpm=120, swing=0, decay=56, delay=2, fb=22, fx=58, pages=0, tracks=[
        fm('CORNETA', 100, 3, 1, bars('G4:2 B4:2 D5:4 B4:2 G4:2 D5:4', 'E5:4 D5:2 C5:2 B4:4 A4:4',
                                      'G4:2 B4:2 D5:4 B4:2 G4:2 D5:4', 'C5:4 B4:2 A4:2 G4:8')),
        fm('TROMPETA', 86, 3, 1, bars('D4:2 G4:2 B4:4 G4:2 D4:2 B4:4', 'C5:4 B4:2 A4:2 G4:4 F#4:4',
                                      'D4:2 G4:2 B4:4 G4:2 D4:2 B4:4', 'A4:4 G4:2 F#4:2 D4:8')),
        fm('TROMBON', 80, 3, 0, bars(
            'r:2 G3M:2 r:2 G3M:2 r:2 G3M:2 r:2 G3M:2', 'r:2 C4M:2 r:2 C4M:2 r:2 G3M:2 r:2 G3M:2',
            'r:2 G3M:2 r:2 G3M:2 r:2 G3M:2 r:2 G3M:2', 'r:2 C4M:2 r:2 D4M:2 r:2 G3M:2 r:2 G3M:2')),
        fm('TUBA', 94, 0, 0, bars('G2:4 D3:4 G2:4 D3:4', 'C3:4 G2:4 G2:4 D3:4',
                                  'G2:4 D3:4 G2:4 D3:4', 'C3:4 D3:4 G2:8')),
        perc(94, dict(BD='x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...',
                      SD='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x.xxxxxxXX',
                      CY='X...............|................|X...............|X...............')),
    ]),
    # 10 ----------------------------------------------------------- Triana
    dict(name='VIVA TRIANA', bpm=108, swing=8, decay=60, delay=2, fb=26, fx=64, pages=0, tracks=[
        fm('CLARINETE', 98, 4, 2, bars('F5:4 E5:2 D5:2 C5:4 A4:4', 'Bb4:4 A4:2 G4:2 F4:4 A4:4',
                                       'C5:4 D5:2 E5:2 F5:4 C5:4', 'D5:4 C5:2 Bb4:2 F4:8')),
        fm('CAMPANILLA', 78, 6, 3, bars(
            'F5:2 r:2 C5:2 r:2 A4:2 r:2 C5:2 r:2', 'F5:2 r:2 D5:2 r:2 Bb4:2 r:2 D5:2 r:2',
            'G5:2 r:2 E5:2 r:2 C5:2 r:2 E5:2 r:2', 'F5:2 r:2 C5:2 r:2 A4:2 r:2 F4:2 r:2')),
        fm('TUBA', 94, 0, 0, bars('F2:4 C3:4 F2:4 C3:4', 'Bb2:4 F3:4 Bb2:4 F3:4',
                                  'C3:4 G3:4 C3:4 G3:4', 'Bb2:4 C3:4 F2:8')),
        perc(90, dict(BD='x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...',
                      SD='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x...xxxxxX',
                      CP='.x.x.x.x.x.x.x.x|.x.x.x.x.x.x.x.x|.x.x.x.x.x.x.x.x|................')),
    ]),
    # 11 ----------------------------------------------------------- levantÃ¡
    dict(name='LEVANTA YA', bpm=96, swing=0, decay=66, delay=2, fb=24, fx=62, pages=0, tracks=[
        fm('CORNETA', 102, 4, 1, bars('C5:2 C5:2 C5:4 E5:4 G5:4', 'G5:6 E5:2 G5:4 r:4',
                                      'F5:2 F5:2 F5:4 D5:4 F5:4', 'G5:4 E5:4 C5:8')),
        fm('TROMPETA', 90, 4, 1, bars('G4:2 G4:2 G4:4 C5:4 E5:4', 'E5:6 C5:2 E5:4 r:4',
                                      'A4:2 A4:2 A4:4 B4:4 D5:4', 'E5:4 C5:4 G4:8')),
        fm('TROMBON', 82, 4, 0, bars('C3M:16', 'C3M:16', 'F3M:16', 'G3M:8 C3M:8')),
        fm('TUBA', 94, 0, 0, bars('C3:4 G3:4 C3:4 G3:4', 'C3:4 G3:4 C3:4 G3:4',
                                  'F3:4 C3:4 F3:4 C3:4', 'G3:8 C3:8')),
        perc(94, dict(BD='x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...',
                      SD='x.xxx.xxx.xxx.xx|x.xxx.xxx.xxx.xx|x.xxx.xxx.xxx.xx|x.xxx.xxX...X...',
                      CY='X...............|X...............|X...............|X.......X.......')),
    ]),
    # 12 ----------------------------------------------------------- soleÃ¡ (compÃ¡s de 12 pulsos)
    dict(name='SOLEA PALIO', bpm=34, swing=0, decay=80, delay=3, fb=34, fx=76, pages=3, bar=12, tracks=[
        fm('OBOE', 94, 5, 3, bars('E5:3 D5:1 C5:1 B4:1 A4:3 B4:1 C5:1 r:1', 'D5:3 C5:1 B4:1 A4:1 G4:3 A4:1 B4:2',
                                  'C5:3 B4:1 A4:1 G4:1 F4:3 G4:1 A4:2', 'B4:3 C5:1 B4:1 A4:1 G#4:3 F4:1 E4:2')),
        pluck(0, 90, 4, 2, bars(
            'A3:1 E4:1 A4:1 C5:1 A4:1 E4:1 A3:1 E4:1 A4:1 C5:1 A4:1 E4:1',
            'G3:1 D4:1 G4:1 B4:1 G4:1 D4:1 G3:1 D4:1 G4:1 B4:1 G4:1 D4:1',
            'F3:1 C4:1 F4:1 A4:1 F4:1 C4:1 F3:1 C4:1 F4:1 A4:1 F4:1 C4:1',
            'E3:1 B3:1 E4:1 G#4:1 E4:1 B3:1 E3:1 B3:1 E4:1 G#4:1 E4:1 B3:1')),
        fm('TUBA', 84, 0, 0, bars('A2:6 A2:6', 'G2:6 G2:6', 'F2:6 F2:6', 'E2:6 E2:6')),
        perc(80, dict(CP='..x..x.x.x.x|..x..x.x.x.x|..x..x.x.x.x|..x..x.x.x.X',
                      BD='x.....x.....|x.....x.....|x.....x.....|x.....x.....',
                      SD='g.g.g.g.g.g.|g.g.g.g.g.g.|g.g.g.g.g.g.|g.g.g.g.g.g.')),
    ]),
    # 13 ----------------------------------------------------------- campanilleros (estilo)
    dict(name='CAMPANILLERO', bpm=96, swing=10, decay=70, delay=3, fb=30, fx=70, pages=0, tracks=[
        fm('FLAUTA', 96, 5, 3, bars('D5:4 D5:2 B4:2 G4:4 B4:4', 'C5:4 C5:2 A4:2 F#4:4 A4:4',
                                    'B4:4 B4:2 G4:2 D5:4 B4:4', 'A4:4 F#4:4 G4:8')),
        fm('CAMPANILLA', 80, 6, 4, bars(
            'G5:2 r:2 D5:2 r:2 B4:2 r:2 D5:2 r:2', 'G5:2 r:2 C5:2 r:2 A4:2 r:2 C5:2 r:2',
            'G5:2 r:2 D5:2 r:2 B4:2 r:2 D5:2 r:2', 'F#5:2 r:2 D5:2 r:2 G4:2 r:6')),
        pluck(2, 88, 4, 1, bars('G3:4 D4:4 G3:4 D4:4', 'C3:4 G3:4 C3:4 G3:4',
                                'G3:4 D4:4 G3:4 D4:4', 'D3:4 A3:4 G3:8')),
        fm('TUBA', 86, 0, 0, bars('G2:8 D3:8', 'C3:8 D3:8', 'G2:8 D3:8', 'D3:8 G2:8')),
        perc(76, dict(CB='x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...',
                      CP='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x...x...x.',
                      BD='x.......x.......|x.......x.......|x.......x.......|x.......x.......')),
    ]),
    # 14 ----------------------------------------------------------- costalero
    dict(name='COSTALERO', bpm=58, swing=0, decay=86, delay=4, fb=38, fx=82, pages=0, tracks=[
        fm('TROMBON', 98, 5, 3, bars('E4:8 G4:4 B4:4', 'A4:6 G4:2 A4:4 C5:4',
                                     'B4:8 D#5:4 F#5:4', 'E5:12 r:4')),
        fm('BOMBARDINO', 84, 5, 3, bars('G3:8 B3:4 D4:4', 'C4:6 B3:2 C4:4 E4:4',
                                        'F#4:8 A4:4 B4:4', 'G4:12 r:4')),
        fm('TUBA', 94, 0, 0, bars('E2:8 B2:8', 'A2:8 E3:8', 'B2:8 F#3:8', 'E2:16')),
        perc(92, dict(BD='x...x...x...x...|x...x...x...x...|x...x...x...x...|x.......x.......',
                      SD='..g...g...g...g.|..g...g...g...g.|..g...g...g...g.|..g...g.XgXgXgXX',
                      CY='X...............|................|................|X...............')),
    ]),
    # 15 ----------------------------------------------------------- Domingo de ResurrecciÃ³n
    dict(name='RESURRECCION', bpm=126, swing=0, decay=62, delay=2, fb=24, fx=64, pages=0, tracks=[
        fm('CORNETA', 100, 4, 1, bars('C5:4 E5:2 G5:2 E5:4 C5:4', 'D5:4 F5:2 D5:2 B4:4 G4:4',
                                      'E5:4 G5:2 E5:2 C5:4 E5:4', 'D5:4 B4:2 G4:2 C5:8')),
        fm('TROMPETA', 86, 4, 1, bars('E4:4 G4:2 C5:2 G4:4 E4:4', 'B4:4 D5:2 B4:2 G4:4 D4:4',
                                      'C5:4 E5:2 C5:2 G4:4 C5:4', 'B4:4 G4:2 D4:2 E4:8')),
        fm('TROMBON', 80, 3, 0, bars(
            'r:2 C4M:2 r:2 C4M:2 r:2 C4M:2 r:2 C4M:2', 'r:2 G3M:2 r:2 G3M:2 r:2 G3M:2 r:2 G3M:2',
            'r:2 C4M:2 r:2 C4M:2 r:2 C4M:2 r:2 C4M:2', 'r:2 G3M:2 r:2 G3M:2 r:2 C4M:2 r:2 C4M:2')),
        fm('TUBA', 94, 0, 0, bars('C3:4 G3:4 C3:4 G3:4', 'G2:4 D3:4 G2:4 D3:4',
                                  'C3:4 G3:4 C3:4 G3:4', 'G2:4 D3:4 C3:8')),
        perc(94, dict(BD='x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...',
                      SD='..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x.xxxxxxXX',
                      CY='X...............|X...............|X...............|X...X...X...X...',
                      CP='.x.x.x.x.x.x.x.x|.x.x.x.x.x.x.x.x|.x.x.x.x.x.x.x.x|................')),
    ]),
]


VELOCITIES = (54, 92, 116)


LENGTHS = (1, 2, 3, 4, 6, 8, 12, 16)


def pack(e):
    # 16-bit little endian: step | (note - 40) << 4 | length index << 10 | chord << 13 | tie << 15
    step, note, vel, c = e
    assert step < 16 and 40 <= note < 104 and vel & 127 == 92 and (c & 15) < 3
    word = step | (note - 40) << 4 | LENGTHS.index((c >> 4) + 1) << 10 | (c & 15) << 13 | (vel >> 7) << 15
    return (word & 255, word >> 8)


def drum_bars(pattern, bar):
    # One 3-byte line per (pad, velocity) and bar: pad | velocity index << 4, then
    # the 16-step hit mask (low, high).
    out = [[] for _ in range(4)]
    for pad, text in sorted(pattern.items(), key=lambda kv: PADS[kv[0]]):
        bars_ = text.split('|')
        assert len(bars_) == 4 and all(len(b) == bar for b in bars_), (pad, text)
        for n, chunk in enumerate(bars_):
            for ch, vel in sorted(DRUM_VEL.items(), key=lambda kv: kv[1]):
                mask = sum(1 << i for i, c in enumerate(chunk) if c == ch)
                if mask:
                    out[n].append((PADS[pad] | VELOCITIES.index(vel) << 4, mask & 255, mask >> 8))
    return [tuple(sorted(x)) for x in out]


def emit(out):
    assert len(SONGS) == 16
    ev_blob, bar_at, bar_key, tracks, scenes = [], [], {}, [], []
    for s in SONGS:
        assert len(s['name']) <= 12 and s['name'] == s['name'].upper(), s['name']
        assert len(s['tracks']) <= 8
        bar = s.get('bar', 16)
        scenes.append((s, len(tracks)))
        for t in s['tracks']:
            drum = t['src'] == '808'
            if drum:
                keys = drum_bars(t['notes'], bar)
            else:
                ev = melodic(t['notes'], bar)
                assert ev and ev[-1][0] < 4 * bar
                keys = [tuple(pack((e[0] - b * bar,) + tuple(e[1:])) for e in ev if e[0] // bar == b)
                        for b in range(4)]
            slots = []
            for key in keys:
                key = (drum, key)
                if key not in bar_key:
                    bar_key[key] = len(bar_at)
                    bar_at.append(len(ev_blob))
                    for e in key[1]:
                        ev_blob.extend(e)
                slots.append(bar_key[key])
            assert max(slots) < 256 and len(ev_blob) < 65536
            tracks.append('{GROOVE_%s, %d, %d, %d, {%s}}' % (
                t['src'], t['tone'], t['level'], t['sends'], ','.join(map(str, slots))))
    bar_at.append(len(ev_blob))
    lines = ['/* Generado por tools/gen_marchas.py. No editar a mano. */',
             '#ifndef FM1_COFRADE_MARCHAS_H', '#define FM1_COFRADE_MARCHAS_H', '',
             'static const uint8_t cofrade_ev[] = {%s};' % ','.join(map(str, ev_blob)),
             'static const uint16_t cofrade_bar_at[] = {%s};' % ','.join(map(str, bar_at)),
             'static const struct cofrade_track cofrade_tracks[] = {', '    ' + ',\n    '.join(tracks), '};',
             '', 'static const struct cofrade_scene cofrade_scenes[GROOVE_FACTORY_PROJECTS] = {']
    for s, first in scenes:
        lines.append('    {"%s", %d, %d, %d, %d, %d, %d, %d, %d, %d},' % (
            s['name'], s['bpm'], s['swing'], s['decay'], s['delay'], s['fb'], s['fx'],
            s['pages'], len(s['tracks']), first))
    lines += ['};', '', '#endif', '']
    pathlib.Path(out).write_text('\n'.join(lines), encoding='ascii', newline='\n')
    print('OK: %d marchas, %d pistas, %d compases unicos, %d bytes de eventos -> %s' % (
        len(SONGS), len(tracks), len(bar_at) - 1, len(ev_blob), out))


if __name__ == '__main__':
    root = pathlib.Path(__file__).resolve().parent.parent
    emit(sys.argv[1] if len(sys.argv) > 1 else root / 'overlay' / 'app' / 'cofrade_marchas.h')
