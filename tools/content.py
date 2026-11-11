# -*- coding: utf-8 -*-
"""Contenu de la visite : textes des zones, panneaux muraux et histoire.

Les informations proviennent du portfolio de Jules ROGUE (applications CV,
Compétences, Certificats, Tux World, RPG « hameau des projets »).
Ce fichier est la seule source de vérité : gen_assets.py en tire les
panneaux (textures) et gen_map.py les zones/textes HUD (cubescript).
"""

# --- Histoire --------------------------------------------------------------
# Affichée uniquement via la console d'origine du jeu (messages courts).
STORY = {
    "intro": ("Le serveur du portfolio de Jules a planté : 10 fragments se sont éparpillés dans les "
              "salles, et des bugs rôdent ! Ramasse des armes, explore et restaure les fragments."),
    "end": ("Les 10 fragments sont restaurés : le portfolio de Jules est réparé. Merci de ta visite ! "
            "Écris-lui depuis la salle Contact ou sur julesrogue.fr."),
}

# --- Zones -----------------------------------------------------------------
# id -> (titre, message court affiché à l'entrée, compte dans l'histoire ?)
# Le détail de chaque sujet est écrit sur les panneaux muraux de la salle.
ZONES = {
    "accueil": ("Hall d'accueil", "", False),
    "galerie": ("Galerie des projets", "", False),
    "profil": ("Profil - la bibliothèque de Jules",
               "étudiant BTS SIO SLAM en alternance chez Action Logement Services", True),
    "competences": ("Compétences - la salle serveur",
                    "les 3 blocs du BTS SIO SLAM : support, développement, cybersécurité", True),
    "leboncoin": ("Projet Leboncoin - le garage",
                  "petites annonces auto en PHP 8 / MySQL / MVC, avec Roman Corobca", True),
    "magic": ("Projet Magic Shape Generator - la salle rythmique",
              "des magic shapes pour A Dance of Fire and Ice, sur magic.julesrogue.fr", True),
    "mineport": ("Projet Mineport - le monde en voxels",
                 "Minecraft Java porté en C# / MonoGame, OpenGL et Vulkan, multijoueur", True),
    "cube2": ("Projet Cube 2 Portfolio - l'arène",
              "ce jeu : Cube 2 compilé en WebAssembly, multijoueur via WebSocket", True),
    "portfolioos": ("Projet Portfolio OS - le bureau géant",
                    "julesrogue.fr : un bureau dans le navigateur (Aurelia, Express, MariaDB)", True),
    "certificats": ("Certificats - la salle des trophées",
                    "Cisco - Introduction to Cybersecurity", True),
    "tux": ("Tux World - la banquise",
            "la veille de Jules sur Tux, la mascotte de Linux", True),
    "contact": ("Contact - le bureau de poste",
                "jules.rogue@ploud.fr - julesrogue.fr", True),
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
