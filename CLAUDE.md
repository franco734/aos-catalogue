# aos-catalogue — Contexte du projet

Dépôt de **publication des données** de l'app iOS familiale AOS Minilof
(Age of Sigmar 4e édition). L'app télécharge `catalogue.json` depuis ce
dépôt au premier lancement et via Réglages → Mettre à jour.

Utilisateur : Benoit, **non-codeur** — toujours donner des instructions
simples, pas à pas, en français.

## ⚠️ Ce dépôt est PUBLIC, et c'est voulu

L'app télécharge `catalogue.json` sans aucun identifiant — c'est ce qui
permet le fonctionnement offline-first sans serveur. Conséquences :

- **Ne jamais rien mettre de personnel ici** : pas de secret, pas de nom,
  pas de fichier de travail. Uniquement les données du jeu et les scripts
  de publication.
- Ne pas passer le dépôt en privé : l'app ne pourrait plus se mettre à jour.

## Consigne permanente de session

- **Toujours commencer la session par `git pull`** (le workflow Oracle
  committe directement sur ce dépôt depuis GitHub — le clone local est
  souvent en retard).
- **Toujours finir la session en proposant un commit + push vers GitHub.**

## Comment ce dépôt est alimenté (ne pas modifier à la main)

1. **Catalogue principal** (unités, armes, règles…) : généré sur la machine
   de Benoit par `ingest.py` (repo aos-explorer), puis publié par
   `publier_catalogue.sh` — jamais édité à la main ici.
2. **Fiches Oracle communautaires** : un 👍 dans l'app crée une Issue
   étiquetée `approuve-oracle` ; le workflow `publier-oracle.yml`
   (déclenchement **MANUEL uniquement**, bouton "Run workflow" sur
   github.com) les relit et les fusionne dans `catalogue.json`.

## Pièges connus

1. **Le déclenchement manuel du workflow Oracle est une décision de
   sécurité** (revue du 07/08/2026), pas une paresse : la clé embarquée
   dans l'app s'authentifie comme le propriétaire du repo, donc filtrer
   par auteur ne protège de rien. Seule la relecture humaine avant le
   clic garantit le contenu. **Ne jamais automatiser ce workflow.**
2. **Accès en écriture depuis le Mac** : le remote utilise l'alias SSH
   `github-aos-catalogue` (voir `~/.ssh/config`) avec une deploy key
   dédiée (`~/.ssh/id_ed25519_aos_catalogue`), limitée à ce seul repo.
   Sur une nouvelle machine, il faut soit recréer une deploy key, soit
   basculer le remote en HTTPS.
3. **Identité des commits** : ce dépôt committe avec
   `benoit.senchou@protonmail.com` (config locale du dépôt) — à refaire
   sur tout nouveau clone.
4. `publier_oracle.py` ne touche **jamais** au reste du catalogue : les
   fiches Oracle sont fusionnées, le reste vient exclusivement
   d'`ingest.py`. Garder cette séparation.
