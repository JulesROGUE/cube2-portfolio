// portfolio.cpp : la « visite » du portfolio de Jules ROGUE (côté client).
//
// Sans aucune nouvelle interface (seulement de courts messages dans la console
// d'origine), ce module gère la progression :
//   1. exploration : des zones (`pfzone`) donnent des fragments du portfolio ;
//   2. parkour : des parcours (`pfcourse`) entre les bâtiments ; une chute ramène
//      au départ du parcours (pas de mort), l'arrivée donne un fragment ;
//   3. combat : en entrant dans une arène, le client prévient le serveur qui lance
//      une vague de monstres ; l'arène est fermée (barrière) jusqu'à la fin de la
//      vague, qui donne un fragment aux joueurs présents ;
//   4. boss : avec les 10 fragments, le client demande le boss au serveur ; sa
//      défaite (annoncée par le serveur) conclut l'histoire.
// Contenu et coordonnées : packages/base/portfolio.cfg (généré par tools/gen_map.py).
#include "game.h"
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

// Mesures automatisées (tests de fluidité de la caméra) : orientation du joueur local.
extern "C" EMSCRIPTEN_KEEPALIVE float pf_getyaw() { return game::player1 ? game::player1->yaw : 0; }
extern "C" EMSCRIPTEN_KEEPALIVE float pf_getpitch() { return game::player1 ? game::player1->pitch : 0; }

namespace portfolio
{
    struct fragment
    {
        string id;
        char *title;
        bool found;
        fragment() : title(NULL), found(false) {}
        ~fragment() { DELETEA(title); }
    };

    // kind : 0 zone normale, 1 armement d'un parcours, 2 chute, 3 arrivée, 4 arène
    struct zone
    {
        string id, tag;    // tag : fragment donné ("profil"), groupe ("projets*"), parcours ou arène
        vec lo, hi;
        char *title, *text;
        int kind;
        bool found;
        zone() : title(NULL), text(NULL), kind(0), found(false) { id[0] = tag[0] = '\0'; }
        ~zone() { DELETEA(title); DELETEA(text); }
        bool inside(const vec &p) const { return p.x >= lo.x && p.x <= hi.x && p.y >= lo.y && p.y <= hi.y && p.z >= lo.z && p.z <= hi.z; }
    };

    struct course
    {
        string id;
        char *title;
        vec start;
        float yaw;
        bool armed, done;
        course() : title(NULL), yaw(0), armed(false), done(false) {}
        ~course() { DELETEA(title); }
    };

    enum { NUMARENAS = 2 };
    static vector<fragment *> fragments;
    static vector<zone *> zones;
    static vector<course *> courses;
    static int current = -1, lastarenamsg[NUMARENAS] = { 0, 0 }, lastbarrier = 0;
    static bool arenaactive[NUMARENAS] = { false, false }, inarena[NUMARENAS] = { false, false };
    // Durée maximale pendant laquelle une vague retient les joueurs dans l'arène : au-delà,
    // le mur d'énergie s'efface (un monstre sorti de l'arène ou coincé ne bloque plus personne).
    enum { ARENALOCK = 60000 };
    static int arenastart[NUMARENAS] = { 0, 0 };
    // Vie (lifesequence) pendant laquelle le joueur est retenu dans l'arène : une mort,
    // une réapparition ou un Respawn changent la vie et libèrent de l'arène. (update()
    // n'est pas appelé tant que le joueur est mort : on ne peut pas s'y fier pour ça.)
    static int arenalife[NUMARENAS] = { -1, -1 };
    static vec lastinside[NUMARENAS];
    static bool bossasked = false, bossdone = false, needlight = false;
    VARP(pfautolight, 0, 1, 1); // calcule l'éclairage (lightmaps) au chargement de la carte

    SVAR(pfintro, "");
    SVAR(pfend, "");

    // Les littéraux C++ sont en UTF-8 alors que le moteur utilise son propre jeu de
    // caractères (accents compris) : conversion avant affichage.
    static const char *fr(const char *utf8)
    {
        static string bufs[4];
        static int idx = 0;
        char *b = bufs[idx++&3];
        size_t n = decodeutf8((uchar *)b, MAXSTRLEN-1, (const uchar *)utf8, strlen(utf8));
        b[n] = '\0';
        return b;
    }

    static int numfound() { int n = 0; loopv(fragments) if(fragments[i]->found) n++; return n; }

    static fragment *getfragment(const char *id)
    {
        loopv(fragments) if(!strcmp(fragments[i]->id, id)) return fragments[i];
        return NULL;
    }

    static zone *arenazone(int a)
    {
        defformatstring(tag, "%d", a);
        loopv(zones) if(zones[i]->kind == 4 && !strcmp(zones[i]->tag, tag)) return zones[i];
        return NULL;
    }

    static void grant(const char *id, const char *detail = NULL)
    {
        fragment *f = getfragment(id);
        if(!f || f->found) return;
        f->found = true;
        if(detail && detail[0]) conoutf("\f2[%d/%d] \f7%s \f4- %s", numfound(), fragments.length(), f->title, detail);
        else conoutf("\f2[%d/%d] \f7%s", numfound(), fragments.length(), f->title);
        if(numfound() >= fragments.length() && !bossasked)
            conoutf(fr("\f0Les %d fragments sont restaurés ! Le boss final s'éveille au Colisée..."), fragments.length());
    }

    void reset()
    {
        fragments.deletecontents();
        zones.deletecontents();
        courses.deletecontents();
        current = -1;
        loopi(NUMARENAS) { arenaactive[i] = inarena[i] = false; lastarenamsg[i] = 0; }
        bossasked = bossdone = false;
        needlight = true;
    }
    ICOMMAND(pfreset, "", (), reset());

    // pffragment id "titre"
    ICOMMAND(pffragment, "ss", (char *id, char *title),
    {
        fragment *f = new fragment;
        copystring(f->id, id);
        f->title = newstring(title);
        fragments.add(f);
    });

    // pfzone id x1 y1 z1 x2 y2 z2 "titre" "texte" "type:valeur"
    //   type : frag (fragment donné), group (fragment donné quand tout le groupe est vu),
    //          arm / fail / end (parcours), arena (numéro d'arène)
    ICOMMAND(pfzone, "sffffffsss", (char *id, float *x1, float *y1, float *z1, float *x2, float *y2, float *z2, char *title, char *text, char *spec),
    {
        zone *z = new zone;
        copystring(z->id, id);
        z->lo = vec(min(*x1, *x2), min(*y1, *y2), min(*z1, *z2));
        z->hi = vec(max(*x1, *x2), max(*y1, *y2), max(*z1, *z2));
        z->title = newstring(title);
        z->text = newstring(text);
        const char *colon = strchr(spec, ':');
        string kind;
        kind[0] = '\0';
        if(colon) { copystring(kind, spec, min(size_t(colon - spec + 1), sizeof(kind))); copystring(z->tag, colon + 1); }
        z->kind = !strcmp(kind, "arm") ? 1 : !strcmp(kind, "fail") ? 2 : !strcmp(kind, "end") ? 3 : !strcmp(kind, "arena") ? 4 : 0;
        if(!strcmp(kind, "group")) concatstring(z->tag, "*");
        zones.add(z);
    });

    // pfcourse id x y z yaw "titre" : départ d'un parcours de parkour
    ICOMMAND(pfcourse, "sffffs", (char *id, float *x, float *y, float *z, float *yaw, char *title),
    {
        course *c = new course;
        copystring(c->id, id);
        c->start = vec(*x, *y, *z);
        c->yaw = *yaw;
        c->title = newstring(title);
        courses.add(c);
    });

    ICOMMAND(pffound, "", (), intret(numfound()));
    ICOMMAND(pftotal, "", (), intret(fragments.length()));
    ICOMMAND(pfcurrent, "", (), result(zones.inrange(current) ? zones[current]->id : ""));
    ICOMMAND(pfrestart, "", (), { loopv(fragments) fragments[i]->found = false; loopv(zones) zones[i]->found = false; loopv(courses) courses[i]->done = courses[i]->armed = false; current = -1; bossasked = false; });
    // pfgrant id : donne un fragment (tests automatisés, hors ligne uniquement)
    ICOMMAND(pfgrant, "s", (char *id), { if(!multiplayer(false)) grant(id); });

    static void teleportto(fpsent *d, const vec &o, float yaw)
    {
        d->o = o;
        d->yaw = yaw;
        d->pitch = 0;
        d->vel = vec(0, 0, 0);
        d->falling = vec(0, 0, 0);
        entinmap(d);
        updatedynentcache(d);
    }

    // pfgoto x y z [yaw] [pitch] : téléporte le joueur (tests, hors ligne uniquement)
    ICOMMAND(pfgoto, "fffff", (float *x, float *y, float *z, float *yaw, float *pitch),
    {
        fpsent *d = game::player1;
        if(!d || multiplayer(false)) return;
        teleportto(d, vec(*x, *y, *z), *yaw);
        d->pitch = *pitch;
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
    // pfmonsterinfo : liste les monstres connus de ce client (tests)
    ICOMMAND(pfmonsterinfo, "", (),
    {
        loopv(game::players)
        {
            fpsent *e = game::players[i];
            if(e->aitype == AI_NONE) continue;
            conoutf("monstre %s %s %.0f %.0f %.0f vie %d proprio %d moi %d ia %d etat %d wp %d", e->name, e->state == CS_ALIVE ? "vivant" : "mort", e->o.x, e->o.y, e->o.z, e->health,
                    e->ownernum, game::player1->clientnum, e->ai ? 1 : 0, e->ai ? e->ai->getstate().type : -1, ai::waypoints.length());
        }
    });
    // pfplayers : joueurs humains vus par ce client, avec leur apparence (tests)
    ICOMMAND(pfplayers, "", (),
    {
        loopv(game::players)
        {
            fpsent *e = game::players[i];
            if(e->aitype != AI_NONE || e == game::player1) continue;
            conoutf("joueur %d %s apparence %d etat %d vie %d", e->clientnum, e->name, e->playermodel, e->state, e->health);
        }
    });
    // pfrawname : envoie N_SWITCHNAME sans passer par `name` (simule un client modifié,
    // pour vérifier que le serveur ignore tout changement de pseudo)
    ICOMMAND(pfrawname, "s", (char *s), game::addmsg(N_SWITCHNAME, "rs", s));
    // pflookat x y z : oriente la vue vers un point (tests automatisés)
    ICOMMAND(pflookat, "fff", (float *x, float *y, float *z),
    {
        fpsent *d = game::player1;
        if(!d) return;
        vec dir = vec(*x, *y, *z).sub(d->o);
        if(dir.iszero()) return;
        d->yaw = -atan2(dir.x, dir.y)/RAD;
        d->pitch = asin(dir.z/dir.magnitude())/RAD;
    });
    ICOMMAND(pfpos, "", (), { fpsent *d = game::player1; if(d) conoutf("pos %.1f %.1f %.1f yaw %.2f pitch %.2f", d->o.x, d->o.y, d->o.z, d->yaw, d->pitch); });

    void servermsg(const char *msg)
    {
        int a = -1, on = 0;
        if(sscanf(msg, "arena %d %d", &a, &on) == 2 && a >= 0 && a < NUMARENAS)
        {
            arenaactive[a] = on != 0;
            arenastart[a] = lastmillis;
            zone *z = arenazone(a);
            fpsent *d = game::player1;
            inarena[a] = arenaactive[a] && z && d && d->state == CS_ALIVE && z->inside(d->o);
            if(inarena[a]) { lastinside[a] = d->o; arenalife[a] = d->lifesequence; }
        }
        else if(sscanf(msg, "arenaopen %d", &a) == 1 && a >= 0 && a < NUMARENAS)
        {
            arenaactive[a] = false;
            inarena[a] = false;
        }
        else if(sscanf(msg, "arenadone %d", &a) == 1 && a >= 0 && a < NUMARENAS)
        {
            arenaactive[a] = false;
            zone *z = arenazone(a);
            fpsent *d = game::player1;
            if(z && d && (inarena[a] || z->inside(d->o))) grant(z->id, fr("vague nettoyée"));
            inarena[a] = false;
        }
        else if(!strcmp(msg, "boss 1")) bossasked = true;
        else if(!strcmp(msg, "bossdown"))
        {
            if(bossdone) return;
            bossdone = true;
            if(pfend[0]) conoutf("\f0%s", pfend);
        }
    }

    static void barrier(const zone &z)
    {
        // « mur » d'énergie (particules d'origine) autour de l'arène fermée
        const float step = 64;
        for(float x = z.lo.x; x <= z.hi.x; x += step)
        {
            particle_splash(PART_SPARK, 1, 400, vec(x, z.lo.y, z.lo.z + 24), 0xFF4020, 1.2f, 20, 2);
            particle_splash(PART_SPARK, 1, 400, vec(x, z.hi.y, z.lo.z + 24), 0xFF4020, 1.2f, 20, 2);
        }
        for(float y = z.lo.y; y <= z.hi.y; y += step)
        {
            particle_splash(PART_SPARK, 1, 400, vec(z.lo.x, y, z.lo.z + 24), 0xFF4020, 1.2f, 20, 2);
            particle_splash(PART_SPARK, 1, 400, vec(z.hi.x, y, z.lo.z + 24), 0xFF4020, 1.2f, 20, 2);
        }
    }

    static void updatecourses(fpsent *d)
    {
        loopv(courses)
        {
            course &c = *courses[i];
            loopvj(zones)
            {
                zone &z = *zones[j];
                if(z.kind < 1 || z.kind > 3 || strcmp(z.tag, c.id) || !z.inside(d->o)) continue;
                if(z.kind == 1 && !c.armed && !c.done)
                {
                    c.armed = true;
                    conoutf(fr("\f6%s : va jusqu'au bout ! (une chute te ramène au départ)"), c.title);
                }
                else if(z.kind == 2 && c.armed)
                {
                    c.armed = false;
                    teleportto(d, c.start, c.yaw);
                    conoutf(fr("\f3Chute ! Retour au départ : %s"), c.title);
                    playsound(S_TELEPORT);
                }
                else if(z.kind == 3 && !c.done)
                {
                    c.done = true;
                    c.armed = false;
                    grant(c.id, fr("parcours réussi"));
                }
            }
        }
    }

    // Protection d'apparition : bulle bleue (sphère d'explosion bleue d'origine du moteur)
    // autour des visiteurs protégés, vue par soi et par les autres.
    static void spawnbubbles()
    {
        static int lastbubble = 0;
        if(lastmillis - lastbubble < 40) return;
        lastbubble = lastmillis;
        loopv(game::players)
        {
            fpsent *e = game::players[i];
            if(e->aitype != AI_NONE || e->state != CS_ALIVE || lastmillis >= e->pfprotectmillis) continue;
            float left = (e->pfprotectmillis - lastmillis) / float(PFPROTECT);
            vec c = vec(e->o).subz(e->eyeheight * 0.45f);
            float r = 13.0f + 1.5f * sinf(lastmillis * 0.012f);
            bool firstperson = e == game::player1 && !isthirdperson();
            // vue de l'intérieur, la sphère voilerait tout l'écran : seulement pour les autres
            if(!firstperson) particle_fireball(c, r, PART_EXPLOSION_BLUE, 60, left > 0.25f ? 0x3C78FF : 0x2850B0, r);
            else
            {
                // vue à la 1re personne : étincelles bleues autour du champ de vision
                loopk(3)
                {
                    vec p = vec(e->o).add(vec(rndscale(2) - 1, rndscale(2) - 1, rndscale(2) - 1).normalize().mul(9));
                    particle_splash(PART_SPARK, 1, 120, p, 0x5090FF, 0.6f, 40, 0);
                }
            }
        }
    }

    void update()
    {
        spawnbubbles();
        fpsent *d = game::player1;
        if(!d || d->state == CS_SPECTATOR || d->state == CS_EDITING) return;

        // La carte générée n'embarque pas de lightmaps (fichier plus léger) : on les
        // calcule une fois chargée (soleil + lumières colorées des salles).
        if(needlight)
        {
            needlight = false;
            if(pfautolight) execute("calclight -1");
            // Les monstres peuvent être initialisés avant la fin du chargement de la carte
            // (qui efface les points de passage) : on recharge le graphe de navigation.
            // Rechargement forcé : en multijoueur, le client a souvent déjà commencé à
            // poser des points de passage « à la trace » (quelques dizaines, non reliés),
            // ce qui bloquait le chargement du vrai graphe et figeait les monstres.
            ai::loadwaypoints(true);
        }
        if(d->state != CS_ALIVE)
        {
            // Mort : on n'est plus retenu dans l'arène. Sans cela, la réapparition sur la
            // place était aussitôt annulée (retour au dernier point dans l'arène, donc à
            // l'endroit de la mort, au milieu des monstres : morts en boucle).
            loopi(NUMARENAS) inarena[i] = false;
            return;
        }

        // Arènes fermées pendant une vague : on ne peut pas en sortir
        bool drawbarrier = lastmillis - lastbarrier > 250;
        if(drawbarrier) lastbarrier = lastmillis;
        loopi(NUMARENAS)
        {
            zone *z = arenazone(i);
            if(!z) continue;
            bool in = z->inside(d->o);
            if(inarena[i] && arenalife[i] != d->lifesequence) inarena[i] = false;   // mort / réapparition depuis
            if(arenaactive[i] && lastmillis - arenastart[i] > ARENALOCK)
            {
                if(inarena[i]) conoutf(fr("\f2Le mur d'énergie s'efface : tu peux quitter l'arène (la vague continue)."));
                inarena[i] = false;
            }
            else if(arenaactive[i])
            {
                if(drawbarrier) barrier(*z);
                if(inarena[i] && !in) { d->o = lastinside[i]; d->vel = vec(0, 0, 0); d->falling = vec(0, 0, 0); in = true; }
                if(in) { if(!inarena[i]) arenalife[i] = d->lifesequence; inarena[i] = true; lastinside[i] = d->o; }
            }
            else if(in && totalmillis - lastarenamsg[i] > 3000)
            {
                fragment *f = getfragment(z->id);
                if(f && f->found) continue;
                lastarenamsg[i] = totalmillis;
                game::addmsg(N_SERVCMD, "rs", i ? "pfarena 1" : "pfarena 0");
            }
        }

        updatecourses(d);

        // Boss : demandé au serveur tant qu'il ne l'a pas confirmé (« #pf boss 1 »)
        static int lastbossreq = 0;
        if(!bossasked && !bossdone && fragments.length() && numfound() >= fragments.length() && totalmillis - lastbossreq > 4000)
        {
            lastbossreq = totalmillis;
            game::addmsg(N_SERVCMD, "rs", "pfboss");
        }

        // Zones d'exploration : messages à l'entrée, fragments
        int inside = -1;
        loopv(zones) if(zones[i]->kind == 0 && zones[i]->inside(d->o)) { inside = i; break; }
        if(inside == current) return;
        current = inside;
        if(inside < 0) return;
        zone &z = *zones[inside];
        bool first = !z.found;
        z.found = true;
        int taglen = strlen(z.tag);
        if(first && taglen && z.tag[taglen-1] == '*')
        {
            conoutf("\f7%s \f4- %s", z.title, z.text);
            bool all = true;
            loopv(zones) if(zones[i]->kind == 0 && !strcmp(zones[i]->tag, z.tag) && !zones[i]->found) all = false;
            string fid;
            copystring(fid, z.tag, taglen);
            if(all) grant(fid, fr("tous les stands visités"));
        }
        else if(first && taglen && getfragment(z.tag) && !getfragment(z.tag)->found) grant(z.tag, z.text);
        else conoutf("\f7%s", z.title);
    }
}
