# Flow 01 PowerBI — ETL et calcul des primes

Ce flow extrait, nettoie et transforme les données pour alimenter PowerBI, puis calcule les avantages salariaux.

## Conteneurs

| Conteneur | Nom Docker | Rôle |
|-----------|-----------|------|
| `export` | `strava_export` | Export DuckDB + nettoyage des données |
| `testexport` | `strava_testexport` | Tests qualité + rapport email |
| `calcul_primes` | `strava_calcul_primes` | Génération des données de test + calcul des primes |

## Scripts par conteneur

### strava_export
| Script | Description |
|--------|-------------|
| `1.00_ExportsDonnees.py` | Charge les tables SQL Server dans DuckDB, ajoute `rowHash` et `idExport`, réinsère |
| `2.00_NettoyageDonnees.py` | Nettoyage des 5 tables (suppression doublons, valeurs nulles, normalisation) |

### strava_testexport
| Script | Description |
|--------|-------------|
| `1.00_TestExport.py` | Tests structure, qualité et métier — envoie un rapport HTML par email |

### strava_calcul_primes
| Script | Description |
|--------|-------------|
| `1.00_GenerateTestData.py` | Génère des activités de test (15-25/an) dans `StravaActivities_TestData` |
| `2.00_ValidateDeclarations.py` | Valide les déclarations via Google Maps Distance Matrix API |
| `3.00_PrimeTrajet.py` | Calcule la prime de trajet (5% salaire brut) — export SQL + Excel |
| `4.00_PrimeBienEtre.py` | Calcule les 5 jours bien-être (≥15 activités) — export SQL + Excel |

## Règles métier

**Prime de trajet**
- Modes éligibles : marche/running, vélo/trottinette
- Calcul : `Montant_prime = Salaire_brut × 0.05`
- Export : table `Prime_Trajet` + fichier `/data/Prime_Trajet_YYYYMMDD.xlsx`

**5 Jours bien-être**
- Seuil : ≥ 15 activités sur les 12 derniers mois glissants
- Export : table `Prime_BienEtre` + fichier `/data/Prime_BienEtre_YYYYMMDD.xlsx`

## Réseau

Ce flow utilise le réseau externe `flow_01_strava_strava_network` créé par `flow_01_Strava`.

## Variables d'environnement

### .envFolder (partagé par les 3 conteneurs)
```
PATHDATA=/data/
```

### .env (conteneurs testexport et calcul_primes)
```
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=587
EMAIL_RECIPIENT=
GOOGLE_MAPS_API_KEY=    # Requis pour ValidateDeclarations.py
```

## Démarrage

```bash
docker-compose up -d
# Les conteneurs restent en attente (tail -f /dev/null)
# Kestra exécute les scripts via docker exec
```
