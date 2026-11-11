// nosound.cpp : remplace sound.cpp (SDL_mixer) et movie.cpp (enregistreur vidéo)
// dans la version « portfolio » web. Le son est retiré pour alléger le
// téléchargement : toutes les fonctions publiques deviennent des no-op.
#include "engine.h"

bool nosound = true;

int usesound = 0, soundchans = 32, soundfreq = 44100, soundbufferlen = 1024;
VARP(soundvol, 0, 0, 255);
VARP(musicvol, 0, 0, 255);
SVAR(audiodriver, "");
VARP(maxsoundsatonce, 0, 7, 100);

void initsound() {}
void clear_sound() {}
void stopsounds() {}
void clearmapsounds() {}
void checkmapsounds() {}
void updatesounds() {}
void preloadsound(int n) {}
void preloadmapsound(int n) {}
void preloadmapsounds() {}
void stopmapsound(extentity *e) {}
void initmumble() {}
void closemumble() {}
void updatemumble() {}
void stopmusic() {}
bool stopsound(int n, int chanid, int fade) { return false; }
int playsound(int n, const vec *loc, extentity *ent, int flags, int loops, int fade, int chanid, int radius, int expire) { return -1; }
int playsoundname(const char *s, const vec *loc, int vol, int flags, int loops, int fade, int chanid, int radius, int expire) { return -1; }

// Commandes cubescript appelées par les .cfg : acceptées mais ignorées.
ICOMMAND(registersound, "si", (char *name, int *vol), intret(0));
ICOMMAND(mapsound, "sii", (char *name, int *vol, int *maxuses), intret(0));
ICOMMAND(altsound, "si", (char *name, int *vol), );
ICOMMAND(altmapsound, "si", (char *name, int *vol), );
ICOMMAND(numsounds, "", (), intret(0));
ICOMMAND(nummapsounds, "", (), intret(0));
ICOMMAND(soundreset, "", (), );
ICOMMAND(mapsoundreset, "", (), );
ICOMMAND(resetsound, "", (), );
ICOMMAND(music, "ss", (char *name, char *cmd), );
ICOMMAND(sound, "i", (int *n), );

// movie.cpp retiré : stubs de l'enregistreur.
namespace recorder
{
    bool isrecording() { return false; }
    void capture(bool overlay) {}
    void stop() {}
    void cleanup() {}
}
