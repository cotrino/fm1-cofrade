#!/usr/bin/env python3
"""Valida con el motor real del simulador (WASM) que las 16 marchas generan proyectos validos.

Uso: python tools/check_factory.py build/work/build/web/simulator.wasm   (requiere: pip install wasmtime)
"""
import sys

from wasmtime import Engine, Linker, Module, Store, WasiConfig

engine = Engine()
store = Store(engine)
store.set_wasi(WasiConfig())
linker = Linker(engine)
linker.define_wasi()
instance = linker.instantiate(store, Module.from_file(engine, sys.argv[1]))
exports = instance.exports(store)
if '_initialize' in exports:
    exports['_initialize'](store)
memory = exports['memory']


def text(ptr):
    data = memory.read(store, ptr, ptr + 32)
    return bytes(data).split(b'\0')[0].decode('latin1')


bad = 0
for i in range(16):
    result = exports['sim_factory_project'](store, i)
    print('%2d %-13s %s' % (i, text(exports['sim_factory_name'](store, i)),
                           'OK' if result == 0 else 'INVALIDO (%d)' % result))
    bad += result != 0
print('%d proyectos invalidos' % bad if bad else 'Los 16 proyectos son validos')
sys.exit(1 if bad else 0)
