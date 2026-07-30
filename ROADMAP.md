# Roadmap

## AoE Explorer — Comparateur : filtre de renforcement des unités

**Statut :** à faire plus tard (idée notée, pas encore implémentée)

**Contexte :** ce repo (`aos-catalogue`) ne contient que les données du catalogue
(`catalogue.json`). Le frontend "AoE Explorer" (comparateur d'unités) vit dans un
autre repo, non accessible depuis cette session. Cette entrée sert de mémo pour
reprendre le travail une fois ce repo frontend identifié/attaché.

**Demande :**

Quand les filtres `damage`, `résistance`, `health` "au contrôle" sont
sélectionnés dans le comparateur, ajouter un moyen de filtrer/mettre en avant
les unités **renforçables** (champ `renforcable` déjà présent dans
`catalogue.json` sur chaque unité) parmi la liste affichée en dessous.

Le contrôle doit être un bouton sélection/désélection (toggle), positionné par
rapport à la ligne de filtre existante **"save adverse"**.

**Deux designs à proposer avant implémentation** (l'utilisateur n'est pas sûr
du design final) :

1. **Ligne dédiée** : nouvelle ligne de filtres juste en dessous de la ligne
   "save adverse", avec le bouton toggle "Renforçable" seul (ou avec un futur
   groupe de filtres additionnels).
2. **Intégré dans la ligne du dessus** : le toggle "Renforçable" ajouté
   directement dans la ligne de filtres existante (celle au-dessus de "save
   adverse"), à condition que ça tienne en largeur sans casser le layout
   responsive.

**Prochaine étape :** une fois le repo frontend identifié, explorer le
composant de filtres du comparateur (ligne "save adverse", layout flex/grid,
composants de toggle existants), puis proposer les deux maquettes (capture ou
artifact) avant tout commit de code.
