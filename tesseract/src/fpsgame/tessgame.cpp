// tessgame.cpp : interface entre le jeu Sauerbraten de la visite et le moteur Tesseract
// (fonctions que Tesseract demande au module de jeu et que Sauerbraten n'avait pas).
#include "engine.h"
#include "game.h"

namespace game
{
    bool cancrouch() { return false; }                 // pas d'accroupissement dans Sauerbraten
    const char *gameconfig() { return "config/game.cfg"; }
    float clipconsole(float w, float h) { return 0; }
    int numanims() { return NUMANIMS; }

    void findanims(const char *pattern, vector<int> &anims)
    {
        loopi(sizeof(animnames)/sizeof(animnames[0])) if(matchanim(animnames[i], pattern)) anims.add(i);
    }

    extern void rendergame(bool mainpass);
    void rendergame() { rendergame(true); }

    extern void renderplayerpreview(int model, int team, int weap);
    void renderplayerpreview(int model, int color, int team, int weap) { renderplayerpreview(model, team, weap); }
}

// Rendu d'un joueur (moteur de Sauerbraten, rendermodel.cpp), adapté à Tesseract
VAR(animoverride, -1, 0, NUMANIMS-1);
VAR(testanims, 0, 0, 1);
VAR(testpitch, -90, 0, 90);

void renderclient(dynent *d, const char *mdlname, modelattach *attachments, int hold, int attack, int attackdelay, int lastaction, int lastpain, float scale, bool ragdoll, float trans)
{
    int anim = hold ? hold : ANIM_IDLE|ANIM_LOOP;
    float yaw = testanims && d==game::player1 ? 0 : d->yaw,
          pitch = testpitch && d==game::player1 ? testpitch : d->pitch;
    vec o = d->feetpos();
    int basetime = 0;
    if(animoverride) anim = (animoverride<0 ? ANIM_ALL : animoverride)|ANIM_LOOP;
    else if(d->state==CS_DEAD)
    {
        anim = ANIM_DYING|ANIM_NOPITCH;
        basetime = lastpain;
        // pas de ragdoll dans la visite : animation de mort du modèle
        if(lastmillis-basetime>1000) anim = ANIM_DEAD|ANIM_LOOP|ANIM_NOPITCH;
    }
    else if(d->state==CS_EDITING || d->state==CS_SPECTATOR) anim = ANIM_EDIT|ANIM_LOOP;
    else if(d->state==CS_LAGGED) anim = ANIM_LAG|ANIM_LOOP;
    else
    {
        if(lastmillis-lastpain < 300) { anim = ANIM_PAIN; basetime = lastpain; }
        else if(lastpain < lastaction && (attack < 0 || (d->type != ENT_AI && lastmillis-lastaction < attackdelay)))
        {
            anim = attack < 0 ? -attack : attack;
            basetime = lastaction;
        }
        if(d->inwater && d->physstate<=PHYS_FALL) anim |= (((game::allowmove(d) && (d->move || d->strafe)) || d->vel.z+d->falling.z>0 ? ANIM_SWIM : ANIM_SINK)|ANIM_LOOP)<<ANIM_SECONDARY;
        else if(d->timeinair>100) anim |= (ANIM_JUMP|ANIM_END)<<ANIM_SECONDARY;
        else if(game::allowmove(d) && (d->move || d->strafe))
        {
            if(d->move>0) anim |= (ANIM_FORWARD|ANIM_LOOP)<<ANIM_SECONDARY;
            else if(d->strafe)
            {
                if(d->move<0) anim |= ((d->strafe>0 ? ANIM_RIGHT : ANIM_LEFT)|ANIM_REVERSE|ANIM_LOOP)<<ANIM_SECONDARY;
                else anim |= ((d->strafe>0 ? ANIM_LEFT : ANIM_RIGHT)|ANIM_LOOP)<<ANIM_SECONDARY;
            }
            else if(d->move<0) anim |= (ANIM_BACKWARD|ANIM_LOOP)<<ANIM_SECONDARY;
        }
        if((anim&ANIM_INDEX)==ANIM_IDLE && (anim>>ANIM_SECONDARY)&ANIM_INDEX) anim >>= ANIM_SECONDARY;
    }
    if(d->ragdoll) cleanragdoll(d);
    if(!((anim>>ANIM_SECONDARY)&ANIM_INDEX)) anim |= (ANIM_IDLE|ANIM_LOOP)<<ANIM_SECONDARY;
    int flags = 0;
    if(d!=game::player1 && !(anim&ANIM_RAGDOLL)) flags |= MDL_CULL_VFC | MDL_CULL_OCCLUDED | MDL_CULL_QUERY;
    if(d->type!=ENT_PLAYER) flags |= MDL_CULL_DIST;
    if(d->state==CS_LAGGED) trans = min(trans, 0.3f);
    if(drawtex == DRAWTEX_MODELPREVIEW) flags &= ~(MDL_CULL_VFC | MDL_CULL_OCCLUDED | MDL_CULL_QUERY | MDL_CULL_DIST);
    rendermodel(mdlname, anim, o, yaw, pitch, 0, flags, d, attachments, basetime, 0, scale, vec4(1, 1, 1, trans));
}

namespace server
{
    int protocolversion() { return PROTOCOL_VERSION; }
    extern int serverport(int infoport);
    int serverport() { return serverport(-1); }
}
