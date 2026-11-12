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
