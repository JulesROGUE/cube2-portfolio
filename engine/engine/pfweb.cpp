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

// Mouvements de souris (pointer lock) transmis directement par la coquille web :
// cumulés entre deux images puis appliqués une fois par image (voir checkinput).
int pfmousedx = 0, pfmousedy = 0;
extern "C" EMSCRIPTEN_KEEPALIVE void pf_mousemove(int dx, int dy)
{
    pfmousedx += dx;
    pfmousedy += dy;
}

// Curseur natif (souris libre) : position absolue en fractions du canvas.
extern void pf_setcursor(float x, float y);
extern "C" EMSCRIPTEN_KEEPALIVE void pf_mousepos(float x, float y)
{
    pf_setcursor(x, y);
}

// 1 si un menu est ouvert et attend la souris (les clics lui reviennent).
extern "C" EMSCRIPTEN_KEEPALIVE int pf_guiopen()
{
    return g3d_windowhit(true, false) ? 1 : 0;
}

extern "C" EMSCRIPTEN_KEEPALIVE void pf_resize(int w, int h)
{
    defformatstring(cmd, "screenres %d %d", w, h);
    execute(cmd);
}
