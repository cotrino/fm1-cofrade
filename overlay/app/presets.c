/* SPDX-License-Identifier: GPL-3.0-only WITH GPL-3.0-linking-exception */
/* FM1 Cofrade: proyectos de fabrica de Semana Santa.
 * Sustituye a app/presets.c del SDK oficial FM1 Open (V14). Cada proyecto es
 * una marcha original de cuatro compases cuyas notas viven en
 * cofrade_marchas.h (generado por tools/gen_marchas.py). El resultado es un
 * proyecto normal y editable, sin escribir en los slots del usuario ni tocar
 * el estado en vivo. Las marchas son composiciones originales "al estilo de". */
#include "instrument.h"
#include "fm_patch.h"
#include "drum808.h"
#include "sampledrum.h"
#include <string.h>

struct cofrade_track {
    uint8_t source, tone, level, sends;
    uint8_t bar[4]; /* index into the shared, de-duplicated bar table */
};
struct cofrade_scene {
    char name[13];
    uint8_t bpm, swing, decay, delay, feedback, fx_level, pages, count, first;
};
#include "cofrade_marchas.h"

/* Cofrade voice -> program of the factory FM bank (see tools/gen_marchas.py TONES):
 * brass, woodwind, organ, voice and bell voices that ship with the FM1. */
static const uint8_t fm_program[16] = {
    64, 68, 1, 72, 76, 65, 69, 120, 32, 73, 80, 67, 71, 84, 77, 112
};static void preset(struct groove_preset *p, const struct cofrade_track *v, unsigned pages)
{
    p->type = v->source; p->volume = v->level; p->modified = 1;
    p->controls.envelope[2] = 100;
    p->sequence_pages = (uint8_t)pages;
    if (v->source == GROOVE_DX7) {
        groove_fm_factory(p->data, fm_program[v->tone]); p->program = fm_program[v->tone]; p->modified = 0;
    } else if (v->source == GROOVE_808) {
        /* Public D8_PRESET_BYTES format: selectors, then two parameter sets.
         * Sound selectors must match each set for a lossless store/load. */
        unsigned at = D8_NUM;
        for (unsigned variant = 0; variant < 2; ++variant)
            for (unsigned part = 0; part <= D8_NUM; ++part)
                for (int i = 0; i < drum808_nparams((int)part); ++i) {
                    const fm1_param_t *d = drum808_param((int)part, i);
                    static const uint8_t levels[D8_NUM] = {78,56,46,42,38,40,46,34,30,30,29};
                    static const uint8_t pans[D8_NUM] = {64,64,49,64,79,54,72,80,47,77,72};
                    unsigned value = d->def;
                    if (!strcmp(d->name, "Sound")) value = variant;
                    if (part < D8_NUM) {
                        if (!strcmp(d->name, "Level")) value = levels[part];
                        else if (!strcmp(d->name, "Pan")) value = pans[part];
                        else if (!strcmp(d->name, "Rev")) value = part == D8_SD || part == D8_CP ? 24 : 9;
                        else if (!strcmp(d->name, "Dly")) value = part == D8_RS ? 12 : 0;
                        else if (!strcmp(d->name, "Decay") && part == D8_SD) value = 84;
                    }
                    p->data[at++] = (uint8_t)value;
                }
    } else if (v->source == GROOVE_PLUCK) {
        static const uint8_t pluck[3][4] = {{88,70,24,48},{103,52,24,66},{79,89,24,42}};
        memcpy(p->data, pluck[v->tone], 4);
    } else {
        p->program = p->data[0] = v->tone; p->data[1] = 16;
        p->data[2] = 24; p->data[3] = 38;
    }
    p->data[209] = v->sends;
}
const char *groove_factory_name(unsigned index)
{
    return index < GROOVE_FACTORY_PROJECTS ? cofrade_scenes[index].name : NULL;
}
/* Pitched record (16 bits): step | (note - 40) << 4 | length index << 10 |
 * chord << 13 | tie << 15. Drum record (3 bytes): pad | velocity index << 4,
 * then the hit mask of that pad and velocity in the bar. A held note repeats on
 * consecutive steps with the tie flag; the engine keeps the same pitch sounding
 * and releases it when the last step ends. */
static void decode(struct groove_step *cells, const struct cofrade_track *t, unsigned bar_steps)
{
    static const uint8_t velocity[3] = {54, 92, 116}, lengths[8] = {1, 2, 3, 4, 6, 8, 12, 16};
    for (unsigned b = 0; b < 4; ++b) {
        const uint8_t *e = cofrade_ev + cofrade_bar_at[t->bar[b]];
        const uint8_t *end = cofrade_ev + cofrade_bar_at[t->bar[b] + 1];
        unsigned base = b * bar_steps;
        if (t->source == GROOVE_808) {
            for (; e < end; e += 3)
                for (unsigned s = 0; s < bar_steps; ++s) {
                    struct groove_step *n = &cells[base + s];
                    unsigned vel = velocity[(e[0] >> 4) & 3U];
                    if (!((e[1] | e[2] << 8) >> s & 1U)) continue;
                    if (n->velocity < vel) n->velocity = (uint8_t)vel;
                    n->drums |= (uint16_t)(1U << (e[0] & 15U));
                }
            continue;
        }
        for (; e < end; e += 2) {
            unsigned word = e[0] | e[1] << 8, at = base + (word & 15U), length = lengths[word >> 10 & 7U];
            unsigned tie = word >> 15;
            for (unsigned k = 0; k < length && at + k < GROOVE_STEPS; ++k) {
                struct groove_step *n = &cells[at + k];
                unsigned last = k + 1U == length, hold = !last || tie;
                n->note = (uint8_t)((word >> 4 & 63U) + 40U); n->velocity = 92;
                n->drums = (uint16_t)((word >> 13 & 3U) | ((hold ? 15U : length == 1 ? 12U : 14U) << 5) | (hold << 12));
            }
        }
    }
}int groove_factory_build(unsigned index, struct groove_project *p)
{
    if (!p || index >= GROOVE_FACTORY_PROJECTS) return GROOVE_PROJECT_INVALID;
    const struct cofrade_scene *s = &cofrade_scenes[index];
    memset(p, 0, sizeof *p);
    memset(p->name, ' ', sizeof p->name); memcpy(p->name, s->name, strlen(s->name));
    p->tempo = s->bpm; p->mute = (uint8_t)(255U << s->count);
    /* Delay sincronizado al tempo: 1/16, 1/16, 1/16D, 1/8, 1/8D. */
    static const uint8_t delay[5] = {131, 131, 133, 134, 135};
    p->effects[0] = s->decay;
    p->effects[1] = delay[s->delay > 4 ? 4 : s->delay];
    p->effects[2] = s->feedback; p->effects[3] = s->fx_level;
    groove_sequence_defaults(&p->sequence); p->sequence.swing = s->swing;
    groove_project_arp_defaults(p);
    for (unsigned t = 0; t < GROOVE_TRACKS; ++t) {
        static const struct cofrade_track empty = {GROOVE_PSG, 0, 100, 0, {0}};
        const struct cofrade_track *v = t < s->count ? &cofrade_tracks[s->first + t] : &empty;
        preset(&p->preset[t], v, s->pages);
        if (t < s->count) decode(p->step[t], v, s->pages == 3 ? 12U : 16U);
    }
    return groove_project_valid(p) ? 0 : GROOVE_PROJECT_INVALID;
}
