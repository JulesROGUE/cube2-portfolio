// webstubs.cpp : fonctions OpenGL « desktop » absentes de WebGL 2.
// Elles ne servent qu'à l'éditeur (fil de fer) ou à la sauvegarde de textures
// compressées : on les neutralise proprement au lieu d'ignorer les symboles.
#include "engine.h"

extern "C" {
void glDrawBuffer(GLenum mode) {}
void glPolygonMode(GLenum face, GLenum mode) {}
void glGetTexLevelParameteriv(GLenum target, GLint level, GLenum pname, GLint *params) { if(params) *params = 0; }
void glGetCompressedTexImage(GLenum target, GLint level, void *img) {}
}
