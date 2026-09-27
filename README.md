# Filou Macro System V1

Moteur généraliste de macros personnel pour Linux.

- Interface `index.html`
- Agent Python très léger
- ID + code appareil
- Macros en JSON
- Synchronisation d'un `macros.json` hébergé sur GitHub
- Actions V1 : lancer une application/commande, ouvrir un fichier, URL, commande sensible avec validation, texte, attente.

## Installation
Python 3 doit être installé.

```bash
python3 agent.py
```

Puis ouvre `index.html`.

Pour GitHub, place un `macros.json` dans ton dépôt et renseigne son URL RAW dans `config.json`.

**Sécurité :** les commandes shell sont marquées sensibles et doivent être validées dans la macro. Ne synchronise pas depuis une source que tu ne contrôles pas.
