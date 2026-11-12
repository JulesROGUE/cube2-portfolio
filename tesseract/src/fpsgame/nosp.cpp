// nosp.cpp : le mode solo de Sauerbraten (monstres et objets mobiles des campagnes)
// n'est pas utilisé par la visite (les monstres sont des bots, voir aiman.h) ;
// ces fonctions vides remplacent monster.cpp et movable.cpp sur le moteur Tesseract.
#include "game.h"

namespace game
{
    struct monster : fpsent {};
    struct movable : dynent {};
    vector<monster *> monsters;
    vector<movable *> movables;

    void clearmonsters() {}
    void preloadmonsters() {}
    void stackmonster(monster *d, physent *o) {}
    void updatemonsters(int curtime) {}
    void rendermonsters() {}
    void suicidemonster(monster *m) {}
    void hitmonster(int damage, monster *m, fpsent *at, const vec &vel, int gun) {}
    void monsterkilled() {}
    void endsp(bool allkilled) {}
    void spsummary(int accuracy) {}

    void clearmovables() {}
    void stackmovable(movable *d, physent *o) {}
    void updatemovables(int curtime) {}
    void rendermovables() {}
    void suicidemovable(movable *m) {}
    void hitmovable(int damage, movable *m, fpsent *at, const vec &vel, int gun) {}
}
