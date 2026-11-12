// webport.cpp : adaptation de Tesseract au navigateur (WebAssembly / WebGL2).
// Fonctions OpenGL de bureau absentes de WebGL2 : remplacées ou sans effet.
#include "engine.h"

#ifdef __EMSCRIPTEN__
extern "C" {
void glPolygonMode(GLenum face, GLenum mode) {}
void glDrawBuffer(GLenum buf)
{
    // OpenGL ES : l'attachement n doit être à l'indice n du tableau
    GLint fbo = 0;
    glGetIntegerv(GL_FRAMEBUFFER_BINDING, &fbo);
    if(!fbo) { GLenum b = buf == GL_NONE ? GL_NONE : GL_BACK; glDrawBuffers(1, &b); return; }
    if(buf >= GL_COLOR_ATTACHMENT0 && buf < GL_COLOR_ATTACHMENT0 + 8)
    {
        GLenum bufs[8];
        int n = buf - GL_COLOR_ATTACHMENT0;
        for(int i = 0; i < n; i++) bufs[i] = GL_NONE;
        bufs[n] = buf;
        glDrawBuffers(n + 1, bufs);
    }
    else { GLenum b = GL_NONE; glDrawBuffers(1, &b); }
}
void glGetTexLevelParameteriv(GLenum target, GLint level, GLenum pname, GLint *params) { if(params) *params = 0; }
void glGetCompressedTexImage(GLenum target, GLint level, void *img) {}
}

// Attributs de sommet « normalisés » de l'OpenGL de bureau, absents d'OpenGL ES :
// convertis en glVertexAttrib4f.
static void APIENTRY web4Nub(GLuint i, GLubyte x, GLubyte y, GLubyte z, GLubyte w) { glVertexAttrib4f(i, x/255.0f, y/255.0f, z/255.0f, w/255.0f); }
static void APIENTRY web4Nubv(GLuint i, const GLubyte *v) { web4Nub(i, v[0], v[1], v[2], v[3]); }
static void APIENTRY web4Nbv(GLuint i, const GLbyte *v) { glVertexAttrib4f(i, max(v[0]/127.0f, -1.0f), max(v[1]/127.0f, -1.0f), max(v[2]/127.0f, -1.0f), max(v[3]/127.0f, -1.0f)); }
static void APIENTRY web4Niv(GLuint i, const GLint *v) { glVertexAttrib4f(i, v[0]/2147483647.0f, v[1]/2147483647.0f, v[2]/2147483647.0f, v[3]/2147483647.0f); }
static void APIENTRY web4Nuiv(GLuint i, const GLuint *v) { glVertexAttrib4f(i, v[0]/4294967295.0f, v[1]/4294967295.0f, v[2]/4294967295.0f, v[3]/4294967295.0f); }
static void APIENTRY web4Nusv(GLuint i, const GLushort *v) { glVertexAttrib4f(i, v[0]/65535.0f, v[1]/65535.0f, v[2]/65535.0f, v[3]/65535.0f); }
static void APIENTRY web4usv(GLuint i, const GLushort *v) { glVertexAttrib4f(i, v[0], v[1], v[2], v[3]); }

static void APIENTRY webFramebufferTexture3D(GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level, GLint layer)
{
    glFramebufferTextureLayer(target, attachment, texture, level, layer);
}

void webport_glfuncs()
{
    glFramebufferTexture3D_ = webFramebufferTexture3D;
    glVertexAttrib4Nub_ = web4Nub;
    glVertexAttrib4Nubv_ = web4Nubv;
    glVertexAttrib4Nbv_ = web4Nbv;
    glVertexAttrib4Niv_ = web4Niv;
    glVertexAttrib4Nuiv_ = web4Nuiv;
    glVertexAttrib4Nusv_ = web4Nusv;
    glVertexAttrib4usv_ = web4usv;
}
#endif

// --- Interface avec la coquille web (web/portfolio.js) ---------------------------
#ifdef __EMSCRIPTEN__
#include <emscripten.h>

extern "C" EMSCRIPTEN_KEEPALIVE void pf_execute(const char *script)
{
    if(script && *script) execute(script);
}

// 1 = pointer lock obtenu (clic dans le canvas), 0 = perdu (Échap, focus...)
extern bool grabinput;
extern void inputgrab(bool on, bool delay);
extern "C" EMSCRIPTEN_KEEPALIVE void pf_grab(int on)
{
    if((on != 0) != grabinput) inputgrab(grabinput = on != 0, false);
}

// mouvements relatifs (pointer lock), cumulés puis appliqués une fois par image
extern int pfmousedx, pfmousedy;
extern "C" EMSCRIPTEN_KEEPALIVE void pf_mousemove(int dx, int dy)
{
    pfmousedx += dx;
    pfmousedy += dy;
}

// curseur natif (souris libre) : position absolue en fractions du canvas
extern "C" EMSCRIPTEN_KEEPALIVE void pf_mousepos(float x, float y) { UI::setcursorpos(x, y); }
extern "C" EMSCRIPTEN_KEEPALIVE int pf_guiopen() { return UI::hascursor() ? 1 : 0; }
extern "C" EMSCRIPTEN_KEEPALIVE int pf_guihover() { return UI::cursorinwindow() ? 1 : 0; }

extern "C" EMSCRIPTEN_KEEPALIVE void pf_resize(int w, int h)
{
    defformatstring(cmd, "screenres %d %d", w, h);
    execute(cmd);
}

// `js "..."` : message vers la coquille web (Module.interop)
void js(const char *script)
{
    char *result = (char *)EM_ASM_INT({ return Module.interop(UTF8ToString($0)); }, script);
    if(result) stringret(result);
}
COMMAND(js, "s");
#endif
