// pfweb.cpp : petites aides côté moteur pour la version « portfolio ».
//  - pf_grab()     : capture/relâche la souris (clic / perte du pointer lock) ;
//  - pf_execute()  : exécute du cubescript depuis JavaScript (export C).
#include "engine.h"
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

extern "C" EMSCRIPTEN_KEEPALIVE void pf_execute(const char *script)
{
    if(script && *script) execute(script);
}

// Appelé par la coquille web : 1 = clic dans le canvas, 0 = pointer lock perdu (Échap).
extern bool grabinput;
extern void inputgrab(bool on, bool delay);
extern "C" EMSCRIPTEN_KEEPALIVE void pf_grab(int on)
{
    if((on != 0) != grabinput) inputgrab(grabinput = on != 0, false);
}

extern "C" EMSCRIPTEN_KEEPALIVE void pf_resize(int w, int h)
{
    defformatstring(cmd, "screenres %d %d", w, h);
    execute(cmd);
}
