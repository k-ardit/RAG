# Kestra — Orchestration des flows

Kestra Community Edition orchestre les deux flows principaux du POC Avantages Sportifs.

## Accès

- Interface web : **http://localhost:8080**
- Namespace : `avantages_sportifs`

## Flows

### flow_getdata.yaml
Synchronise les activités Strava toutes les 2 minutes.

| Paramètre | Valeur |
|-----------|--------|
| Déclencheur | `*/2 * * * *` (toutes les 2 min) |
| Concurrence | `CANCEL` — 1 seule exécution simultanée |
| Retry | 3 tentatives, 15s d'intervalle |
| Notifications | Email [OK] et [ECHEC] via `afterExecution` |

Séquence : `start getdata` → `exec 1.00_getData.py` → `stop getdata`

### flow_powerbi.yaml
Pipeline ETL complet, exécuté chaque lundi à 6h.

| Paramètre | Valeur |
|-----------|--------|
| Déclencheur | `0 6 * * 1` (lundi 6h00) |
| Retry | 3 tentatives, 30s d'intervalle |
| Notifications | Email [OK] en fin, [ECHEC] en cas d'erreur |

Séquence :
1. `strava_export` : ExportsDonnees → NettoyageDonnees
2. `strava_testexport` : TestExport
3. `strava_calcul_primes` : GenerateTestData → ValidateDeclarations → PrimeTrajet → PrimeBienEtre

## Secrets (Community Edition)

Les secrets sont définis via des variables préfixées `SECRET_` dans le fichier `.env` :

```
SECRET_GMX_PASSWORD=<mot_de_passe>
SECRET_GMX_USER=<email>
```

Accessibles dans les flows via : `{{ secret('GMX_PASSWORD') }}`

## Rechargement automatique des flows

Les fichiers YAML dans `flows/` sont montés dans le conteneur Kestra. Toute modification locale est **automatiquement appliquée** sans redémarrage grâce à la configuration :

```yaml
flows:
  local-files:
    enabled: true
    watch-directory: /app/flows
```

## Démarrage

```bash
# Pré-requis Windows : activer Docker TCP sur le port 2375
# (Paramètres Docker Desktop → General → "Expose daemon on tcp://localhost:2375")

docker-compose up -d
```

## Structure

```
dockerCompose_Kestra/
├── docker-compose.yml
├── Dockerfile
├── .env                    # Secrets Kestra (exclu du git)
└── flows/
    ├── flow_getdata.yaml
    └── flow_powerbi.yaml
```
