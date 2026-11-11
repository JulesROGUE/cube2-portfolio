// portfolio.cpp : la « visite » du portfolio de Jules ROGUE.
//
// Ce module ajoute au mode de jeu FPS de Cube 2 :
//  - des zones (boîtes alignées sur les axes) déclarées en cubescript avec
//    `pfzone`, chacune associée à un titre et à un texte de présentation ;
//  - un suivi de progression (zones découvertes) qui sert de fil narratif :
//    une introduction, un objectif courant, puis une fin quand tout a été visité ;
//  - un panneau HUD qui affiche le texte de la zone où se trouve le joueur,
//    ainsi qu'une notification à chaque nouvelle découverte.
//
// Tout le contenu (textes, coordonnées) vit dans packages/base/portfolio.cfg,
// généré par tools/gen_map.py en même temps que la carte.
#include "game.h"

extern void pfrect(float x, float y, float w, float h, int color, float alpha);

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

    // Les littéraux C++ sont en UTF-8 alors que le moteur travaille avec son
    // propre jeu de caractères : on convertit (é, è, à... sont supportés).
    static const char *fr(const char *utf8)
    {
        static string bufs[4];
        static int idx = 0;
        char *b = bufs[idx++&3];
        size_t n = decodeutf8((uchar *)b, MAXSTRLEN-1, (const uchar *)utf8, strlen(utf8));
        b[n] = '\0';
        return b;
    }

    static vector<zone *> zones;
    static int current = -1, toastzone = -1, toastmillis = 0, endmillis = 0, startmillis = 0;
    static bool finished = false;

    SVAR(pfintrotitle, "Bienvenue");
    SVAR(pfintrotext, "");
    SVAR(pfendtitle, "Fin de la visite");
    SVAR(pfendtext, "");
    SVAR(pfobjective, "Explore les salles du portfolio");
    VARP(pfhud, 0, 1, 1);
    VARP(pfintrotime, 0, 20000, 120000);

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
        current = toastzone = -1;
        toastmillis = endmillis = 0;
        finished = false;
        startmillis = totalmillis;
    }
    ICOMMAND(pfreset, "", (), reset());

    // pfzone id x1 y1 z1 x2 y2 z2 "titre" "texte" [story]
    ICOMMAND(pfzone, "sffffffssi", (char *id, float *x1, float *y1, float *z1, float *x2, float *y2, float *z2, char *title, char *text, int *story),
    {
        zone *z = new zone;
        copystring(z->id, id);
        z->lo = vec(min(*x1, *x2), min(*y1, *y2), min(*z1, *z2));
        z->hi = vec(max(*x1, *x2), max(*y1, *y2), max(*z1, *z2));
        z->title = newstring(title);
        z->text = newstring(text);
        z->story = *story >= 0; // -1 = zone hors progression (couloirs...)
        zones.add(z);
    });

    ICOMMAND(pffound, "", (), intret(storyfound()));
    ICOMMAND(pftotal, "", (), intret(storytotal()));
    ICOMMAND(pfcurrent, "", (), result(zones.inrange(current) ? zones[current]->id : ""));
    ICOMMAND(pfrestart, "", (), { loopv(zones) zones[i]->found = false; finished = false; endmillis = 0; startmillis = totalmillis; current = -1; });

    // pfgoto x y z [yaw] [pitch] : téléporte le joueur (tests / débogage, hors ligne)
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
        conoutf(CON_DEBUG, "pfgoto %.0f %.0f %.0f", d->o.x, d->o.y, d->o.z);
    });
    ICOMMAND(pfpos, "", (), { fpsent *d = game::player1; if(d) conoutf("pos %.0f %.0f %.0f yaw %.0f", d->o.x, d->o.y, d->o.z, d->yaw); });

    void update()
    {
        fpsent *d = game::player1;
        if(!d || d->state == CS_SPECTATOR || d->state == CS_EDITING) return;
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
        if(!z.found)
        {
            z.found = true;
            if(z.story)
            {
                toastzone = inside;
                toastmillis = totalmillis;
                conoutf(fr("\f2Zone découverte : \f7%s \f4(%d/%d)"), z.title, storyfound(), storytotal());
                if(!finished && storyfound() >= storytotal() && storytotal() > 0)
                {
                    finished = true;
                    endmillis = totalmillis;
                    conoutf("\f0%s", pfendtitle);
                }
            }
        }
    }

    // Panneau : titre + texte avec retour à la ligne automatique.
    static void drawpanel(const char *title, const char *text, int x, int y, int width, int accent)
    {
        int pad = 30, tw, th, bw, bh;
        text_bounds(title, tw, th, width - 2*pad);
        text_bounds(text, bw, bh, width - 2*pad);
        int h = pad + th + 20 + bh + pad;
        pfrect(x, y, width, h, 0x101820, 0.72f);
        pfrect(x, y, 10, h, accent, 0.95f);
        draw_text(title, x + pad, y + pad, (accent>>16)&0xFF, (accent>>8)&0xFF, accent&0xFF, 255, -1, width - 2*pad);
        draw_text(text, x + pad, y + pad + th + 20, 235, 235, 235, 255, -1, width - 2*pad);
    }

    static int panelheight(const char *title, const char *text, int width)
    {
        int pad = 30, tw, th, bw, bh;
        text_bounds(title, tw, th, width - 2*pad);
        text_bounds(text, bw, bh, width - 2*pad);
        return pad + th + 20 + bh + pad;
    }

    void drawhud(int w, int h)
    {
        if(!pfhud || zones.empty()) return;
        fpsent *d = game::player1;
        if(!d || d->state == CS_EDITING) return;

        pushhudmatrix();
        hudmatrix.scale(h/1800.0f, h/1800.0f, 1);
        flushhudmatrix();

        int vw = w*1800/h, margin = 40;

        // Objectif courant (en haut à droite)
        {
            defformatstring(obj, "%s  \f2%d/%d", finished ? fr("Visite terminée, merci !") : pfobjective, storyfound(), storytotal());
            int ow, oh;
            text_bounds(obj, ow, oh);
            pfrect(vw - ow - margin - 40, margin, ow + 40, oh + 20, 0x101820, 0.6f);
            draw_text(obj, vw - ow - margin - 20, margin + 10, 255, 255, 255, 255);
        }

        int panelw = min(1400, vw - 2*margin);
        int px = (vw - panelw)/2;

        if(finished && endmillis && totalmillis - endmillis < 25000)
        {
            drawpanel(pfendtitle, pfendtext, px, 240, panelw, 0x60FF90);
        }
        else if(pfintrotime && totalmillis - startmillis < pfintrotime && pfintrotext[0] && (current < 0 || !strcmp(zones[current]->id, "accueil")))
        {
            drawpanel(pfintrotitle, pfintrotext, px, 240, panelw, 0xFFC040);
        }

        bool intro = false;
        if(finished && endmillis && totalmillis - endmillis < 25000)
            intro = true;
        else if(pfintrotime && totalmillis - startmillis < pfintrotime && pfintrotext[0] && (current < 0 || !strcmp(zones[current]->id, "accueil")))
            intro = true;

        if(zones.inrange(current) && !(intro && !zones[current]->story))
        {
            zone &z = *zones[current];
            if(z.text && z.text[0])
            {
                int ph = panelheight(z.title, z.text, panelw);
                drawpanel(z.title, z.text, px, 1800 - ph - 60, panelw, z.story ? 0x40B0FF : 0xA0A0A0);
            }
        }

        if(zones.inrange(toastzone) && totalmillis - toastmillis < 4000)
        {
            defformatstring(msg, fr("\f2Nouvelle zone découverte : \f7%s  (%d/%d)"), zones[toastzone]->title, storyfound(), storytotal());
            int mw, mh;
            text_bounds(msg, mw, mh);
            pfrect((vw - mw)/2 - 30, 130, mw + 60, mh + 30, 0x000000, 0.6f);
            draw_text(msg, (vw - mw)/2, 145);
        }

        pophudmatrix();
    }
}
