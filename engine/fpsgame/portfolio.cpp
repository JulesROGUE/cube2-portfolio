// portfolio.cpp : la « visite » du portfolio de Jules ROGUE.
//
// Ce module ajoute au mode de jeu FPS de Cube 2, SANS nouvelle surcouche d'interface :
//  - des zones (boîtes alignées sur les axes) déclarées en cubescript avec `pfzone` ;
//  - une petite histoire : 10 « fragments » du portfolio à restaurer, un par salle.
//    L'intro, la découverte de chaque salle et la fin s'affichent sous forme de
//    messages courts dans la console d'origine du jeu ; le détail est sur les
//    panneaux muraux de la carte ;
//  - des bruits de pas pour le joueur local.
//
// Le contenu (textes, coordonnées) vit dans packages/base/portfolio.cfg, généré par
// tools/gen_map.py en même temps que la carte.
#include "game.h"

namespace portfolio
{
    struct zone
    {
        string id;
        vec lo, hi;
        char *title, *text;
        bool found, story; // story = compte dans la progression
        zone() : title(NULL), text(NULL), found(false), story(true) {}
        ~zone() { DELETEA(title); DELETEA(text); }
    };

    static vector<zone *> zones;
    static int current = -1, laststep = 0;
    static bool finished = false, introdone = false, needlight = false;
    VARP(pfautolight, 0, 1, 1); // calcule l'éclairage (lightmaps) au chargement de la carte

    SVAR(pfintro, "");
    SVAR(pfend, "");

    static int storytotal()
    {
        int n = 0;
        loopv(zones) if(zones[i]->story) n++;
        return n;
    }

    static int storyfound()
    {
        int n = 0;
        loopv(zones) if(zones[i]->story && zones[i]->found) n++;
        return n;
    }

    void reset()
    {
        zones.deletecontents();
        current = -1;
        finished = introdone = false;
        needlight = true;
    }
    ICOMMAND(pfreset, "", (), reset());

    // pfzone id x1 y1 z1 x2 y2 z2 "titre" "texte court" [story]
    ICOMMAND(pfzone, "sffffffssi", (char *id, float *x1, float *y1, float *z1, float *x2, float *y2, float *z2, char *title, char *text, int *story),
    {
        zone *z = new zone;
        copystring(z->id, id);
        z->lo = vec(min(*x1, *x2), min(*y1, *y2), min(*z1, *z2));
        z->hi = vec(max(*x1, *x2), max(*y1, *y2), max(*z1, *z2));
        z->title = newstring(title);
        z->text = newstring(text);
        z->story = *story >= 0; // -1 = zone hors progression (Hall, galerie...)
        zones.add(z);
    });

    ICOMMAND(pffound, "", (), intret(storyfound()));
    ICOMMAND(pftotal, "", (), intret(storytotal()));
    ICOMMAND(pfcurrent, "", (), result(zones.inrange(current) ? zones[current]->id : ""));
    ICOMMAND(pfrestart, "", (), { loopv(zones) zones[i]->found = false; finished = false; current = -1; introdone = false; });

    // pfgoto x y z [yaw] [pitch] : téléporte le joueur (tests, hors ligne uniquement)
    ICOMMAND(pfgoto, "fffff", (float *x, float *y, float *z, float *yaw, float *pitch),
    {
        fpsent *d = game::player1;
        if(!d || multiplayer(false)) return;
        d->o = vec(*x, *y, *z);
        d->yaw = *yaw;
        d->pitch = *pitch;
        d->vel = vec(0, 0, 0);
        entinmap(d);
        updatedynentcache(d);
    });
    // pfaim : tourne la vue vers le monstre vivant le plus proche (tests automatisés)
    ICOMMAND(pfaim, "", (),
    {
        fpsent *d = game::player1;
        fpsent *best = NULL;
        if(!d) return;
        float bestdist = 1e16f;
        loopv(game::players)
        {
            fpsent *e = game::players[i];
            if(e == d || e->aitype == AI_NONE || e->state != CS_ALIVE) continue;
            float dist = e->o.dist(d->o);
            if(dist < bestdist) { bestdist = dist; best = e; }
        }
        if(!best) { intret(0); return; }
        conoutf(CON_DEBUG, "pfaim %s %.0f", best->name, bestdist);
        vec dir = vec(best->o).sub(d->o);
        d->yaw = -atan2(dir.x, dir.y)/RAD;
        d->pitch = asin(dir.z/dir.magnitude())/RAD;
        intret(int(bestdist));
    });
    // pfmonsterinfo : liste les monstres (bots) connus de ce client et leur position (tests)
    ICOMMAND(pfmonsterinfo, "", (),
    {
        loopv(game::players)
        {
            fpsent *e = game::players[i];
            if(e->aitype == AI_NONE) continue;
            conoutf("monstre %s %s %.0f %.0f %.0f", e->name, e->state == CS_ALIVE ? "vivant" : "mort", e->o.x, e->o.y, e->o.z);
        }
    });
    ICOMMAND(pfpos, "", (), { fpsent *d = game::player1; if(d) conoutf("pos %.0f %.0f %.0f yaw %.0f", d->o.x, d->o.y, d->o.z, d->yaw); });

    static void footsteps(fpsent *d)
    {
        if(d->state != CS_ALIVE || d->physstate < PHYS_SLOPE || (!d->move && !d->strafe)) return;
        if(d->vel.magnitude2() < 30) return;
        if(lastmillis - laststep < 360) return;
        laststep = lastmillis;
        playsound(S_PF_STEP);
    }

    void update()
    {
        fpsent *d = game::player1;
        if(!d || d->state == CS_SPECTATOR || d->state == CS_EDITING) return;

        // La carte générée n'embarque pas de lightmaps (fichier plus léger) : on les
        // calcule une fois chargée (≈1 s), avec les lumières colorées de chaque salle.
        if(needlight)
        {
            needlight = false;
            if(pfautolight) execute("calclight -1");
            // Les monstres peuvent être initialisés avant la fin du chargement de la carte
            // (qui efface les points de passage) : on recharge le graphe de navigation.
            ai::loadwaypoints();
        }

        if(!introdone && pfintro[0] && d->state == CS_ALIVE)
        {
            introdone = true;
            conoutf("\f2%s", pfintro);
        }

        footsteps(d);

        const vec &p = d->o;
        int inside = -1;
        loopv(zones)
        {
            const zone &z = *zones[i];
            if(p.x >= z.lo.x && p.x <= z.hi.x && p.y >= z.lo.y && p.y <= z.hi.y && p.z >= z.lo.z && p.z <= z.hi.z) { inside = i; break; }
        }
        if(inside == current) return;
        current = inside;
        if(inside < 0) return;
        zone &z = *zones[inside];
        if(z.story && !z.found)
        {
            z.found = true;
            conoutf("\f2[%d/%d] \f7%s \f4- %s", storyfound(), storytotal(), z.title, z.text);
            if(!finished && storyfound() >= storytotal() && storytotal() > 0)
            {
                finished = true;
                if(pfend[0]) conoutf("\f0%s", pfend);
            }
        }
        else conoutf("\f7%s", z.title);
    }
}
