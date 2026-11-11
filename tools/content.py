# -*- coding: utf-8 -*-
"""Contenu de la visite : textes des zones, panneaux muraux et histoire.

Les informations proviennent du portfolio de Jules ROGUE (applications CV,
Compétences, Certificats, Tux World, RPG « hameau des projets »).
Ce fichier est la seule source de vérité : gen_assets.py en tire les
panneaux (textures) et gen_map.py les zones/textes HUD (cubescript).
"""

# --- Histoire --------------------------------------------------------------
STORY = {
    "objective": "Restaure les fragments du portfolio",
    "intro_title": "Bienvenue dans le portfolio de Jules ROGUE",
    "intro_text": (
        "Le serveur du portfolio a planté : son contenu s'est éparpillé en 10 fragments, "
        "un par salle. Explore le Hall et les salles autour pour tous les restaurer. "
        "Chaque salle découverte rétablit un morceau du parcours de Jules (profil, compétences, "
        "projets, certificats...). Le compteur en haut à droite suit ta progression. "
        "Clique pour capturer la souris, ZQSD/WASD pour te déplacer, Échap pour le menu."
    ),
    "end_title": "Portfolio restauré à 100 % - merci de ta visite !",
    "end_text": (
        "Tu as retrouvé les 10 fragments : le parcours de Jules est de nouveau complet. "
        "Reviens au Hall pour discuter avec les autres visiteurs (touche T), "
        "ou passe par la salle Contact pour lui écrire. À bientôt sur julesrogue.fr !"
    ),
}

# --- Zones -----------------------------------------------------------------
# id -> (titre HUD, texte HUD, compte dans l'histoire ?)
ZONES = {
    "accueil": (
        "Hall d'accueil",
        "Le carrefour de la visite. Au nord : Profil et Compétences. Au sud : Certificats "
        "et Tux World. À l'est : la Galerie des projets. À l'ouest : la salle Contact.",
        False,
    ),
    "profil": (
        "Fragment 1 - Profil de Jules ROGUE",
        "Étudiant en BTS SIO option SLAM en alternance (CFA IEF2I, Vincennes, 2025-2027) et "
        "développeur web en alternance chez Action Logement Services. Avant : bac pro Systèmes "
        "numériques au lycée Clément Ader (Tournan-en-Brie), brevet au collège des Remparts "
        "(Rozay-en-Brie). Expériences : support IT et brassage réseau au CHI de Créteil, "
        "JavaScript, suite ELK et API Azure, support GLPI. Passionné, rigoureux, investi - "
        "et joueur de badminton.",
        True,
    ),
    "competences": (
        "Fragment 2 - Compétences BTS SIO SLAM",
        "Bloc 1 (U4) : support et mise à disposition de services informatiques. "
        "Bloc 2 (U5, spécifique SLAM) : conception et développement d'applications - concevoir, "
        "maintenir une solution applicative, gérer les données. Bloc 3 (U6) : cybersécurité des "
        "services informatiques. Langages : JavaScript, Java, Express JS, HTML/CSS. "
        "IA & outils : Claude Code, OpenClaw, agents IA, automatisation.",
        True,
    ),
    "leboncoin": (
        "Fragment 3 - Projet Leboncoin (véhicules)",
        "Clone de Leboncoin dédié aux véhicules : dépôt d'annonces (catalogue de 1802 modèles), "
        "recherche multicritère, favoris, messagerie entre membres et espace d'administration "
        "(modération des annonces, gestion des comptes). Mots de passe hachés en bcrypt. "
        "PHP 8, MySQL, Bootstrap 5, architecture MVC - projet de groupe avec Roman Corobca.",
        True,
    ),
    "magic": (
        "Fragment 4 - Magic Shape Generator",
        "Outil web pour créer des magic shapes pour A Dance of Fire and Ice : à partir d'un texte, "
        "d'un SVG, d'une image ou de formes générées (cercle, flocon de Koch, courbe du dragon...), "
        "il trace une piste jouable en rythme et exporte la map .adofai. HTML, JavaScript, "
        "Canvas 2D, 100 % côté client - en ligne sur magic.julesrogue.fr.",
        True,
    ),
    "mineport": (
        "Fragment 5 - Mineport",
        "Un portage de Minecraft Java Edition en C# avec MonoGame : rendu OpenGL et Vulkan, "
        "mode multijoueur, et un launcher séparé, MineportLauncher, pour installer et lancer le jeu.",
        True,
    ),
    "cube2": (
        "Fragment 6 - Cube 2 Portfolio (ce jeu !)",
        "Tu es dedans : le moteur de Cube 2: Sauerbraten (C++, licence zlib) allégé et compilé en "
        "WebAssembly avec Emscripten. Carte générée par un script Python, textes de visite en "
        "cubescript, multijoueur grâce à un pont WebSocket <-> UDP vers un serveur dédié, le tout "
        "lancé avec docker compose.",
        True,
    ),
    "portfolioos": (
        "Fragment 7 - Portfolio OS",
        "Le portfolio julesrogue.fr imite un système d'exploitation : bureau, fenêtres et "
        "applications (CV, Compétences, Certificats, Tux World, RPG, chat...). Front Aurelia, "
        "API Node.js/Express et base MariaDB, déployés en conteneurs Docker sur un VPS.",
        True,
    ),
    "certificats": (
        "Fragment 8 - Certificats",
        "Cisco - Introduction to Cybersecurity : menaces et vulnérabilités, protection des données, "
        "sécurité des réseaux et bonnes pratiques. Badge vérifiable sur Credly.",
        True,
    ),
    "tux": (
        "Fragment 9 - Tux World",
        "La veille de Jules sur Tux, la mascotte du noyau Linux : un manchot dessiné en 1996 par "
        "Larry Ewing avec GIMP. Son nom viendrait de (T)orvalds (U)ni(X). Au démarrage, le noyau "
        "affiche un Tux par coeur de processeur ! On le retrouve dans SuperTux, SuperTuxKart, "
        "Tux Paint... avec toute la bande des mascottes du libre.",
        True,
    ),
    "contact": (
        "Fragment 10 - Contact",
        "Envie d'échanger avec Jules ? Écris-lui à jules.rogue@ploud.fr, ou passe par "
        "l'application Contact du portfolio julesrogue.fr. Il est basé à Rozay-en-Brie (77).",
        True,
    ),
}

# --- Panneaux muraux (textures générées) -----------------------------------
# id -> (couleur d'accent RGB, titre, lignes)
PANELS = {
    "sign_accueil": ((255, 192, 64), "PORTFOLIO DE JULES ROGUE",
                     ["Étudiant BTS SIO - option SLAM", "Visite interactive en 3D",
                      "Nord : Profil - Compétences", "Sud : Certificats - Tux World",
                      "Est : Projets   Ouest : Contact"]),
    "sign_profil": ((64, 176, 255), "PROFIL",
                    ["Jules ROGUE - étudiant en BTS SIO",
                     "BTS SIO SLAM en alternance (2025-2027)",
                     "CFA IEF2I - Vincennes",
                     "Développeur web - Action Logement Services",
                     "Bac pro Systèmes numériques (2025)"]),
    "sign_experiences": ((64, 176, 255), "EXPÉRIENCES",
                         ["Action Logement Services",
                          "  dev web, JavaScript, ELK, API Azure, GLPI",
                          "CHI de Créteil",
                          "  support IT, brassage réseau, dépannage",
                          "Atouts : passionné, rigoureux, investi"]),
    "sign_bloc1": ((80, 140, 255), "BLOC 1 - U4",
                   ["Support et mise à disposition",
                    "de services informatiques",
                    "- patrimoine informatique", "- incidents et assistance",
                    "- travailler en mode projet"]),
    "sign_bloc2": ((80, 200, 120), "BLOC 2 - U5 (SLAM)",
                   ["Conception et développement",
                    "d'applications",
                    "- concevoir une solution applicative",
                    "- maintenance corrective / évolutive",
                    "- gérer les données"]),
    "sign_bloc3": ((230, 80, 80), "BLOC 3 - U6",
                   ["Cybersécurité des services",
                    "informatiques",
                    "- données personnelles, identité numérique",
                    "- sécuriser équipements et usages",
                    "- cybersécurité d'une application"]),
    "sign_projets": ((255, 140, 60), "GALERIE DES PROJETS",
                     ["Leboncoin - Magic Shape Generator", "Mineport - Cube 2 Portfolio",
                      "Portfolio OS", "", "Avance dans chaque stand !"]),
    "sign_leboncoin": ((255, 110, 20), "LEBONCOIN",
                       ["Petites annonces automobiles",
                        "annonces, recherche, favoris",
                        "messagerie, administration",
                        "PHP 8 - MySQL - Bootstrap 5 - MVC",
                        "avec Roman Corobca"]),
    "sign_magic": ((190, 110, 255), "MAGIC SHAPE GENERATOR",
                   ["Magic shapes pour ADOFAI",
                    "texte, SVG, image, fractales",
                    "export .adofai",
                    "HTML - JavaScript - Canvas 2D",
                    "magic.julesrogue.fr"]),
    "sign_mineport": ((90, 200, 90), "MINEPORT",
                      ["Minecraft Java porté en C#",
                       "MonoGame",
                       "rendu OpenGL et Vulkan",
                       "multijoueur",
                       "+ MineportLauncher"]),
    "sign_cube2": ((255, 220, 80), "CUBE 2 PORTFOLIO",
                   ["Ce jeu ! Cube 2: Sauerbraten",
                    "C++ compilé en WebAssembly",
                    "Emscripten + WebGL 2",
                    "carte générée en Python",
                    "multijoueur WebSocket <-> UDP"]),
    "sign_portfolioos": ((70, 200, 230), "PORTFOLIO OS",
                         ["julesrogue.fr",
                          "un bureau dans le navigateur",
                          "Aurelia - Node.js/Express",
                          "MariaDB - Docker",
                          "CV, Compétences, RPG, chat..."]),
    "sign_certificats": ((230, 190, 60), "CERTIFICATS",
                         ["Cisco", "Introduction to Cybersecurity",
                          "menaces, vulnérabilités",
                          "protection des données",
                          "badge vérifiable sur Credly"]),
    "sign_tux": ((120, 200, 255), "TUX WORLD",
                 ["Tux, mascotte du noyau Linux",
                  "dessiné en 1996 par Larry Ewing",
                  "(T)orvalds (U)ni(X)",
                  "un Tux par coeur au démarrage",
                  "SuperTux, SuperTuxKart, Tux Paint"]),
    "sign_contact": ((96, 255, 144), "CONTACT",
                     ["jules.rogue@ploud.fr",
                      "Rozay-en-Brie (77)",
                      "",
                      "Application Contact du portfolio",
                      "julesrogue.fr"]),
}

# Remplacements pour le jeu de caractères de Cube 2 (latin étendu, pas de « » ’ —).
_SUBST = {"—": "-", "–": "-", "’": "'", "«": '"', "»": '"', "…": "...", "↔": "<->", " ": " "}


def cube_safe(text):
    for a, b in _SUBST.items():
        text = text.replace(a, b)
    return text


def cubescript_string(text):
    """Chaîne cubescript entre guillemets (échappement ^ et ")."""
    text = cube_safe(text).replace("^", "^^").replace('"', '^"')
    return '"' + text + '"'
