// pfweb.cpp : petites aides côté moteur pour la version « portfolio ».
//  - pfrect()      : rectangle semi-transparent pour les panneaux du HUD ;
//  - pf_execute()  : exécute du cubescript depuis JavaScript (export C).
#include "engine.h"
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

void pfrect(float x, float y, float w, float h, int color, float alpha)
{
    hudnotextureshader->set();
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    gle::colorf(((color>>16)&0xFF)/255.0f, ((color>>8)&0xFF)/255.0f, (color&0xFF)/255.0f, alpha);
    gle::defvertex(2);
    gle::begin(GL_TRIANGLE_STRIP);
    gle::attribf(x, y);
    gle::attribf(x+w, y);
    gle::attribf(x, y+h);
    gle::attribf(x+w, y+h);
    gle::end();
    gle::colorf(1, 1, 1, 1);
    hudshader->set();
}

extern "C" EMSCRIPTEN_KEEPALIVE void pf_execute(const char *script)
{
    if(script && *script) execute(script);
}

extern "C" EMSCRIPTEN_KEEPALIVE void pf_resize(int w, int h)
{
    defformatstring(cmd, "screenres %d %d", w, h);
    execute(cmd);
}
