#!/usr/bin/env python3
"""publier_oracle.py — Publication des réponses Oracle approuvées
(voir ROADMAP.md du repo aos-explorer, section "Oracle des Règles",
double validation).

Lancé par le workflow GitHub Actions .github/workflows/publier-oracle.yml,
déclenché MANUELLEMENT depuis github.com uniquement (voir l'en-tête du
workflow pour le pourquoi — revue de sécurité du 07/08/2026) :
  1. Récupère les Issues ouvertes étiquetées "approuve-oracle".
  2. Décode le bloc JSON caché dans leur corps (<!-- ORACLE_DATA ... -->),
     créé par l'app (GitHubOracleService.swift, repo aos-explorer).
  3. Ajoute une entrée à oracleRegles dans catalogue.json.
  4. Commit + push catalogue.json.
  5. Ferme les Issues traitées.

Ne touche JAMAIS au reste du catalogue (unités/armes/règles de faction…) —
ça reste produit séparément par ingest.py sur la machine de Benoit,
volontairement laissé manuel (voir la discussion de risque du 01/08/2026 :
ce pipeline-ci ne publie que du contenu déjà validé par un humain avant
son passage ici, jamais de ré-extraction depuis BSData).
"""

import json
import os
import re
import subprocess
import unicodedata
import urllib.request

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]  # "owner/repo"
API_BASE = f"https://api.github.com/repos/{REPO}"
LABEL_APPROUVE = "approuve-oracle"
FICHIER_CATALOGUE = "catalogue.json"

# ── Garde-fous de publication (revue de sécurité du 07/08/2026) ──────────────
# À savoir : la clé embarquée dans l'app s'authentifie sous l'identité du
# propriétaire du repo. Filtrer les Issues par auteur ne servirait donc à
# RIEN — légitimes et fabriquées portent la même signature. La vraie
# protection est le déclenchement manuel du workflow (voir publier-oracle.yml).
#
# Ces limites ne sont qu'un filet de sécurité complémentaire : elles
# écartent le contenu manifestement aberrant (pavé de texte injecté, liste
# de sources à rallonge) et gardent l'aperçu de relecture lisible.
LIMITES_TAILLE = {
    "question_exemple": 300,
    "reponse": 2000,
    "extrait_regle": 4000,
}
MAX_SOURCES = 10
MAX_MOTS_CLES = 30
MAX_FICHES_PAR_RUN = 10


def requete(url, method="GET", body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        contenu = resp.read()
        return json.loads(contenu) if contenu else None


def lister_issues_approuvees():
    url = f"{API_BASE}/issues?state=open&labels={LABEL_APPROUVE}&per_page=50"
    return requete(url)


def fermer_issue(numero):
    requete(f"{API_BASE}/issues/{numero}", method="PATCH", body={"state": "closed"})


def decoder_issue(corps):
    """Extrait le bloc JSON caché dans <!-- ORACLE_DATA … --> (même format
    que GitHubOracleService.swift, côté app)."""
    m = re.search(r"<!-- ORACLE_DATA\s*(.*?)-->", corps, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def refus_eventuel(donnees):
    """Renvoie la raison du refus si la fiche dépasse les garde-fous, sinon
    None. Voir LIMITES_TAILLE pour le rôle exact de ces contrôles."""
    for champ, maximum in LIMITES_TAILLE.items():
        valeur = donnees.get(champ) or ""
        if not isinstance(valeur, str):
            return f"champ '{champ}' n'est pas du texte"
        if len(valeur) > maximum:
            return f"champ '{champ}' trop long ({len(valeur)} > {maximum} caractères)"

    for champ, maximum in (("sources", MAX_SOURCES), ("mots_cles", MAX_MOTS_CLES)):
        valeur = donnees.get(champ) or []
        if not isinstance(valeur, list):
            return f"champ '{champ}' n'est pas une liste"
        if len(valeur) > maximum:
            return f"champ '{champ}' trop fourni ({len(valeur)} > {maximum} entrées)"
        if any(not isinstance(x, str) for x in valeur):
            return f"champ '{champ}' contient autre chose que du texte"

    return None


def apercu(numero, donnees):
    """Aperçu lisible dans le journal de l'Action, pour vérifier après coup
    ce qui a été publié sans avoir à rouvrir chaque Issue."""
    reponse = (donnees.get("reponse") or "").replace("\n", " ")
    return (
        f"\n─── Issue #{numero} ───\n"
        f"  Question : {donnees['question_exemple']}\n"
        f"  Réponse  : {reponse[:200]}{'…' if len(reponse) > 200 else ''}\n"
        f"  Sources  : {', '.join(donnees.get('sources') or []) or '(aucune)'}"
    )


def slug(texte):
    normalise = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    normalise = re.sub(r"[^a-zA-Z0-9]+", "-", normalise).strip("-").lower()
    return normalise[:60] or "question"


def id_unique(base, ids_existants):
    if base not in ids_existants:
        return base
    i = 2
    while f"{base}-{i}" in ids_existants:
        i += 1
    return f"{base}-{i}"


def main():
    issues = lister_issues_approuvees()
    if not issues:
        print("Aucune Issue approuvée à publier.")
        return

    with open(FICHIER_CATALOGUE, encoding="utf-8") as f:
        catalogue = json.load(f)
    catalogue.setdefault("oracleRegles", [])
    ids_existants = {e["id"] for e in catalogue["oracleRegles"]}

    numeros_a_fermer = []
    for issue in issues:
        donnees = decoder_issue(issue.get("body") or "")
        if not donnees or not donnees.get("question_exemple"):
            print(f"Issue #{issue['number']} ignorée (format inattendu, "
                  f"pas créée par l'app).")
            continue

        refus = refus_eventuel(donnees)
        if refus:
            print(f"⚠️  Issue #{issue['number']} REFUSÉE : {refus}. "
                  f"Elle reste ouverte — à examiner à la main.")
            continue

        if len(numeros_a_fermer) >= MAX_FICHES_PAR_RUN:
            print(f"Limite de {MAX_FICHES_PAR_RUN} fiches par passage atteinte — "
                  f"le reste sera publié au prochain déclenchement.")
            break

        print(apercu(issue["number"], donnees))

        nouvel_id = id_unique(slug(donnees["question_exemple"]), ids_existants)
        ids_existants.add(nouvel_id)

        catalogue["oracleRegles"].append({
            "id": nouvel_id,
            "categorie": "communaute",
            "mots_cles": donnees.get("mots_cles", []),
            "question_exemple": donnees["question_exemple"],
            "reponse": donnees.get("reponse", ""),
            "extrait_regle": donnees.get("extrait_regle", ""),
            "sources": donnees.get("sources", []),
        })
        numeros_a_fermer.append(issue["number"])
        print(f"Issue #{issue['number']} → fiche '{nouvel_id}' ajoutée.")

    if not numeros_a_fermer:
        print("Rien à publier (Issues dans un format inattendu, ignorées).")
        return

    with open(FICHIER_CATALOGUE, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    subprocess.run(["git", "config", "user.name", "aos-catalogue-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", FICHIER_CATALOGUE], check=True)
    resultat = subprocess.run(
        ["git", "commit", "-m",
         f"Oracle : {len(numeros_a_fermer)} fiche(s) publiée(s) automatiquement"])
    if resultat.returncode == 0:
        subprocess.run(["git", "push"], check=True)
    else:
        print("Rien à committer (catalogue.json identique).")

    for numero in numeros_a_fermer:
        fermer_issue(numero)
        print(f"Issue #{numero} fermée.")


if __name__ == "__main__":
    main()
