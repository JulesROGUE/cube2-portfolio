#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthèse de tous les sons du jeu (aucun son tiers) -> packages/sounds/pf/*.wav

- effets : tirs de chaque arme, explosions, impacts, pas, saut, ramassages,
  douleur / mort du joueur, cris des monstres (virus, bug, glitch) ;
- ambiances en boucle propres à chaque salle (entités « mapsound » de la carte).

WAV mono 16 bits à 16 kHz (format natif de SDL_mixer, pas de décodeur à embarquer).
Usage : gen_sounds.py <dossier_sortie>
"""
import os
import sys
import wave

import numpy as np

SR = 16000
OUT = sys.argv[1] if len(sys.argv) > 1 else "build/gamedata"
rng = np.random.default_rng(1234)


def t_(dur):
    return np.arange(int(SR * dur)) / SR


def env(n, a=0.005, d=None, curve=4.0):
    """Enveloppe attaque linéaire + déclin exponentiel."""
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    dur = n / SR
    dec = np.exp(-curve * t / (d or dur))
    return att * dec


def lowpass(x, cutoff):
    """Filtre passe-bas du premier ordre (cutoff en Hz, scalaire ou tableau)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def noise(dur):
    return rng.uniform(-1, 1, int(SR * dur))


def tone(freq, dur, kind="sine"):
    t = t_(dur)
    f = np.broadcast_to(np.asarray(freq, dtype=float), t.shape)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "sine":
        return np.sin(ph)
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    raise ValueError(kind)


def sweep(f0, f1, dur, kind="sine"):
    return tone(np.geomspace(f0, f1, int(SR * dur)), dur, kind)


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def pad(x, dur):
    n = int(SR * dur)
    return np.concatenate([x, np.zeros(max(0, n - len(x)))])


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def write(name, x, peak=0.9):
    x = norm(np.asarray(x, dtype=float), peak)
    path = os.path.join(OUT, "packages", "sounds", "pf", name + ".wav")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def loop(x, fade=0.25):
    """Rend une ambiance bouclable : fondu enchaîné fin -> début."""
    n = int(SR * fade)
    head, tail = x[:n].copy(), x[-n:]
    k = np.linspace(0, 1, n)
    x = x[:-n].copy()
    x[:n] = head * k + tail * (1 - k)
    return x

# ---------------------------------------------------------------------------
# Effets
# ---------------------------------------------------------------------------


def gunshot(dur, cut0, cut1, body=0.0, bodyf=90, d=None):
    n = noise(dur)
    x = lowpass(n, np.geomspace(cut0, cut1, len(n))) * env(len(n), 0.001, d or dur, 5)
    if body:
        x += body * sweep(bodyf * 2, bodyf, dur) * env(len(n), 0.001, dur * 0.6, 6)
    return x


def explosion(dur=1.2):
    n = noise(dur)
    x = lowpass(n, np.geomspace(2500, 120, len(n))) * env(len(n), 0.002, dur, 3.5)
    x += 0.8 * sweep(90, 35, dur) * env(len(n), 0.002, dur * 0.7, 4)
    return x


def blip(f0, f1, dur, kind="square", vol=1.0):
    x = sweep(f0, f1, dur, kind)
    return vol * x * env(len(x), 0.003, dur, 3)


def chord(freqs, dur, kind="tri", step=0.0):
    parts = []
    for i, f in enumerate(freqs):
        x = tone(f, dur, kind) * env(int(SR * dur), 0.01, dur, 3)
        parts.append(np.concatenate([np.zeros(int(SR * step * i)), x]))
    return mix(*parts)


def voice(f0, f1, dur, rough=0.3, vib=0.0):
    """Cri synthétique : dent de scie filtrée + bruit (« grognement »)."""
    t = t_(dur)
    f = np.geomspace(f0, f1, len(t)) * (1 + vib * np.sin(2 * np.pi * 9 * t))
    x = tone(f, dur, "saw") + rough * noise(dur)
    x = lowpass(x, 1800) * env(len(x), 0.02, dur, 2.5)
    return x


def effects():
    S = {}
    S["jump"] = mix(blip(220, 520, 0.18, "tri"), 0.3 * lowpass(noise(0.12), 900) * env(int(SR * 0.12)))
    S["land"] = mix(lowpass(noise(0.16), 400) * env(int(SR * 0.16), 0.001, 0.16, 6), 0.5 * sweep(110, 60, 0.12) * env(int(SR * 0.12)))
    S["step"] = lowpass(noise(0.07), 700) * env(int(SR * 0.07), 0.001, 0.07, 7)
    S["rifle"] = mix(gunshot(0.5, 6000, 400, 0.6, 140), 0.4 * sweep(1800, 300, 0.25, "saw") * env(int(SR * 0.25)))
    S["punch"] = mix(lowpass(noise(0.12), 1200) * env(int(SR * 0.12), 0.001, 0.12, 6), 0.6 * sweep(160, 70, 0.1))
    S["shotgun"] = gunshot(0.6, 5000, 250, 0.9, 80)
    S["chaingun"] = gunshot(0.12, 7000, 900, 0.4, 160)
    S["rlfire"] = mix(lowpass(noise(0.8), np.geomspace(800, 3000, int(SR * 0.8))) * env(int(SR * 0.8), 0.05, 0.8, 3), 0.4 * sweep(120, 260, 0.8))
    S["rlhit"] = explosion(1.3)
    S["weapload"] = mix(blip(900, 900, 0.05), np.concatenate([np.zeros(int(SR * 0.09)), blip(600, 600, 0.06)]))
    S["itemammo"] = chord([523, 659], 0.25, "square", 0.06)
    S["itemhealth"] = chord([523, 659, 784, 1046], 0.5, "tri", 0.07)
    S["itemarmour"] = chord([392, 523, 784], 0.45, "square", 0.05)
    S["itempup"] = chord([440, 554, 659, 880, 1108], 0.8, "saw", 0.08)
    S["itemspawn"] = blip(300, 1200, 0.3, "sine")
    S["teleport"] = lowpass(sweep(200, 2000, 0.6, "saw"), 3000) * env(int(SR * 0.6), 0.05, 0.6, 2)
    S["noammo"] = blip(160, 140, 0.12, "square")
    S["pupout"] = blip(900, 200, 0.6, "tri")
    for i in range(6):
        S["pain%d" % (i + 1)] = voice(320 - i * 20, 200 - i * 10, 0.3, 0.4)
    S["die1"] = voice(300, 70, 0.9, 0.5)
    S["die2"] = voice(260, 60, 1.0, 0.6, 0.05)
    S["flaunch"] = mix(lowpass(noise(0.3), 2000) * env(int(SR * 0.3), 0.001, 0.3, 5), 0.6 * sweep(300, 120, 0.25))
    S["fexplode"] = explosion(1.0)
    S["splash1"] = lowpass(noise(0.4), 2500) * env(int(SR * 0.4), 0.01, 0.4, 4)
    S["splash2"] = lowpass(noise(0.5), 1500) * env(int(SR * 0.5), 0.01, 0.5, 4)
    S["grunt1"] = voice(180, 140, 0.25, 0.5)
    S["grunt2"] = voice(150, 120, 0.25, 0.5)
    S["rumble"] = lowpass(noise(1.5), 150) * env(int(SR * 1.5), 0.2, 1.5, 2)
    # Monstres : virus (aigu, « bulles »), bug (cliquetis), glitch (bit-crush), 4e type de secours
    S["virus_pain"] = mix(voice(700, 500, 0.3, 0.2, 0.15), 0.4 * blip(1200, 800, 0.2, "sine"))
    S["virus_death"] = mix(voice(800, 120, 0.9, 0.3, 0.2), 0.5 * lowpass(noise(0.9), 3000) * env(int(SR * 0.9)))
    clicks = np.zeros(int(SR * 0.4))
    for k in range(8):
        i = int(k * SR * 0.045)
        c = lowpass(noise(0.01), 5000) * env(int(SR * 0.01), 0.0005, 0.01, 6)
        clicks[i:i + len(c)] += c
    S["bug_pain"] = mix(clicks, 0.5 * voice(260, 220, 0.3, 0.8))
    S["bug_death"] = mix(np.tile(clicks, 2), 0.7 * voice(240, 60, 0.8, 0.9))
    sq = tone(np.repeat(rng.uniform(200, 1400, 12), int(SR * 0.03)), 0.36, "square")
    S["glitch_pain"] = sq * env(len(sq), 0.001, 0.36, 2)
    sq2 = tone(np.repeat(rng.uniform(80, 2000, 30), int(SR * 0.03)), 0.9, "square")
    S["glitch_death"] = sq2 * env(len(sq2), 0.001, 0.9, 2.5)
    S["spare_pain"] = voice(200, 160, 0.3, 0.6)
    S["spare_death"] = voice(220, 50, 0.8, 0.7)
    S["iceball"] = blip(1500, 400, 0.3, "sine")
    S["slimeball"] = lowpass(blip(200, 600, 0.3, "saw"), 1500)
    S["jumppad"] = blip(150, 900, 0.45, "tri")
    S["pistol"] = gunshot(0.35, 7000, 500, 0.5, 200)
    S["announce"] = chord([660, 880], 0.4, "tri", 0.1)
    S["flag"] = chord([440, 660], 0.4, "square", 0.1)
    S["burn"] = lowpass(noise(0.6), 1200) * env(int(SR * 0.6), 0.05, 0.6, 2)
    S["saw_attack"] = lowpass(tone(110 + 40 * np.sin(2 * np.pi * 30 * t_(0.5)), 0.5, "saw"), 3000) * env(int(SR * 0.5), 0.01, 0.5, 1.5)
    S["saw_idle"] = 0.5 * lowpass(tone(70 + 10 * np.sin(2 * np.pi * 18 * t_(0.6)), 0.6, "saw"), 1200)
    S["hit"] = blip(1600, 1600, 0.05, "square")
    S["flagfail"] = blip(300, 200, 0.3, "square")
    for name, x in S.items():
        write(name, x, 0.8 if name not in ("step",) else 0.5)

# ---------------------------------------------------------------------------
# Ambiances de salle (boucles de 4 à 6 s)
# ---------------------------------------------------------------------------


def place(buf, x, at):
    i = int(at * SR)
    j = min(len(buf), i + len(x))
    buf[i:j] += x[:j - i]


def ambiences():
    A = {}
    D = 6.0
    n = int(SR * D)
    # Hall : souffle grave + carillon lointain
    x = 0.25 * lowpass(noise(D), 220)
    for at, f in ((0.5, 784), (0.8, 988), (1.1, 1175)):
        place(x, 0.12 * tone(f, 1.6, "sine") * env(int(SR * 1.6), 0.01, 1.6, 3), at)
    A["amb_hall"] = x
    # Profil : bibliothèque — tic-tac d'horloge + nappe chaude
    x = 0.12 * mix(tone(220, D, "tri"), 0.6 * tone(277, D, "tri"), 0.5 * tone(330, D, "tri")) * (0.6 + 0.4 * np.sin(2 * np.pi * t_(D) / D))
    for k in range(12):
        place(x, 0.4 * highpass(noise(0.015), 2000) * env(int(SR * 0.015), 0.0005, 0.015, 6), k * 0.5)
    A["amb_profil"] = x
    # Compétences : ventilateurs de serveurs + bips
    x = 0.4 * lowpass(noise(D), 900) + 0.08 * tone(120, D, "saw")
    for at, f in ((0.7, 1800), (2.3, 2400), (2.45, 2400), (4.6, 1500)):
        place(x, 0.15 * tone(f, 0.08, "sine") * env(int(SR * 0.08), 0.002, 0.08, 2), at)
    A["amb_competences"] = x
    # Leboncoin : garage — moteur au ralenti + cliquetis d'outils
    t = t_(D)
    eng = tone(32 + 2 * np.sin(2 * np.pi * 0.5 * t), D, "saw") * (0.7 + 0.3 * np.sin(2 * np.pi * 8 * t))
    x = 0.35 * lowpass(eng, 300) + 0.05 * lowpass(noise(D), 600)
    for at in (1.3, 1.45, 4.2):
        place(x, 0.4 * highpass(noise(0.05), 3000) * env(int(SR * 0.05), 0.0005, 0.05, 5), at)
    A["amb_leboncoin"] = x
    # Magic Shape : salle rythmique — boucle de batterie 120 bpm + arpège
    x = np.zeros(n)
    beat = 0.5
    for k in range(int(D / beat)):
        place(x, 0.8 * sweep(150, 45, 0.18) * env(int(SR * 0.18), 0.001, 0.18, 5), k * beat)
        place(x, 0.15 * highpass(noise(0.04), 6000) * env(int(SR * 0.04), 0.0005, 0.04, 6), k * beat + beat / 2)
    for k, f in enumerate([440, 554, 659, 880] * 6):
        place(x, 0.12 * tone(f, 0.22, "square") * env(int(SR * 0.22), 0.002, 0.22, 4), k * 0.25)
    A["amb_magic"] = x
    # Mineport : vent doux + gazouillis
    x = 0.2 * lowpass(noise(D), 400 + 200 * np.sin(2 * np.pi * t_(D) / D))
    for at in (0.8, 1.0, 3.5, 3.65, 3.8):
        place(x, 0.12 * sweep(3000, 4200, 0.07, "sine") * env(int(SR * 0.07), 0.005, 0.07, 3), at)
    A["amb_mineport"] = x
    # Cube 2 : arène — bourdon grave + sifflements
    x = 0.25 * tone(55, D, "saw") * 0.5 + 0.1 * lowpass(noise(D), 300)
    x = lowpass(x, 400)
    place(x, 0.15 * lowpass(sweep(800, 200, 1.0, "saw"), 1500) * env(int(SR * 1.0), 0.2, 1.0, 2), 2.0)
    A["amb_cube2"] = x
    # Portfolio OS : nappe « démarrage » + clics de clavier
    x = 0.1 * mix(tone(196, D, "sine"), tone(294, D, "sine"), 0.7 * tone(392, D, "sine"))
    rr = np.random.default_rng(5)
    for at in np.sort(rr.uniform(0.2, D - 0.2, 14)):
        place(x, 0.25 * highpass(noise(0.02), 2500) * env(int(SR * 0.02), 0.0005, 0.02, 6), at)
    A["amb_portfolioos"] = x
    # Certificats : accord solennel (fanfare douce)
    x = 0.12 * mix(tone(262, D, "tri"), tone(330, D, "tri"), tone(392, D, "tri"), 0.5 * tone(523, D, "tri"))
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * t_(D) * 2 / D) ** 2
    A["amb_certificats"] = x
    # Tux World : vent arctique + cris de manchots
    x = 0.35 * lowpass(noise(D), 600 + 400 * np.sin(2 * np.pi * t_(D) / D) ** 2)
    for at in (1.2, 1.5, 4.0):
        place(x, 0.18 * voice(900, 1100, 0.18, 0.1, 0.3), at)
    A["amb_tux"] = x
    # Contact : bureau de poste — sonnerie de téléphone + tampon
    x = 0.08 * lowpass(noise(D), 500)
    ring = mix(tone(440, 0.8, "sine"), tone(480, 0.8, "sine")) * (np.sin(2 * np.pi * 20 * t_(0.8)) > 0)
    place(x, 0.12 * ring, 1.0)
    place(x, 0.4 * lowpass(noise(0.08), 900) * env(int(SR * 0.08), 0.001, 0.08, 6), 3.5)
    place(x, 0.4 * lowpass(noise(0.08), 900) * env(int(SR * 0.08), 0.001, 0.08, 6), 4.1)
    A["amb_contact"] = x
    for name, x in A.items():
        write(name, loop(pad(x, D)), 0.6)


if __name__ == "__main__":
    effects()
    ambiences()
    print("sons générés dans", os.path.join(OUT, "packages/sounds/pf"))
