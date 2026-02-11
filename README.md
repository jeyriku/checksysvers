# CheckSysVers

Un package Python pour vérifier les versions de systèmes d'exploitation sur différentes plateformes, incluant Linux, Windows, macOS, Cisco, Juniper et Ubiquiti.

## Fonctionnalités

- **Vérification locale** : Détecte et affiche la version OS du système hôte
- **Vérification distante** : Se connecte via SSH à des appareils distants pour récupérer leur version OS
- **Récupération d'inventaire** : Utilise l'API GraphQL d'Infrahub ou le SDK Python pour obtenir la liste des appareils
- **Interface en ligne de commande** : CLI simple et intuitive
- **Utilisable comme bibliothèque** : Importez les classes dans vos propres scripts

## Installation

### Installation depuis le répertoire local

```bash
cd /home/jeyriku/Dev/python_scripts/check_sysvers
pip install -e .
```

### Installation avec les dépendances pour vérifications distantes

```bash
pip install -e ".[remote]"
```

### Installation pour le développement

```bash
pip install -e ".[dev]"
```

### Installation complète (remote + dev)

```bash
pip install -e ".[full]"
```

## Utilisation

### En ligne de commande

**Vérification locale** (par défaut) :
```bash
checksysvers
# ou
checksysvers --local
```

**Vérification distante** :
```bash
checksysvers --remote 192.168.1.1 --device-type cisco
```

**Demander les identifiants de manière interactive** :
```bash
# Pour les connexions distantes
checksysvers --remote 192.168.1.1 --device-type cisco --prompt-credentials

# Pour lister les appareils depuis Infrahub
checksysvers --list-devices --prompt-credentials
```

**Lister les appareils depuis Infrahub** :
```bash
checksysvers --list-devices
```

**Mode verbose** :
```bash
checksysvers --local --verbose
```

### Comme bibliothèque Python

```python
from checksysvers import LocalSysVersChecker, RemoteSysVersChecker

# Vérification locale
local_checker = LocalSysVersChecker()
version = local_checker.local_check_version()
print(f"Version locale: {version}")

# Vérification distante
remote_checker = RemoteSysVersChecker()
version = remote_checker.remote_check_version('192.168.1.1', 'cisco')
print(f"Version distante: {version}")

# Récupérer la liste des appareils
devices = remote_checker.recover_device_list()
```

## Variables d'environnement

Pour les vérifications distantes :

- `SSH_USERNAME` : Nom d'utilisateur SSH
- `SSH_PASSWORD` : Mot de passe SSH
- `SSH_PORT` : Port SSH (défaut: 22)
- `INFRAHUB_API_TOKEN` : Token pour l'API Infrahub
- `INFRAHUB_URL` : URL de l'API Infrahub (défaut: https://infrahub.example.com, `/graphql` sera ajouté automatiquement)
- `INFRAHUB_TLS_INSECURE` : Désactiver la vérification TLS/SSL (défaut: false, utiliser "true" pour désactiver)
- `INFRAHUB_DEVICE_SCHEMA` : Nom du schéma pour les appareils dans Infrahub (défaut: JeylanDevice)

## Structure du package

```
check_sysvers/
├── checksysvers/
│   ├── __init__.py          # Exports principaux du package
│   ├── local_checker.py     # Classe LocalSysVersChecker
│   ├── remote_checker.py    # Classe RemoteSysVersChecker
│   └── cli.py               # Interface ligne de commande
├── pyproject.toml           # Configuration du package
├── requirements.txt         # Dépendances optionnelles
└── README.md               # Ce fichier
```

## Plateformes supportées

- **Linux** : Toutes distributions
- **Windows** : Windows 7 et supérieur
- **macOS** : Toutes versions
- **Cisco** : Routeurs et switches IOS
- **Juniper** : Equipements JunOS
- **Ubiquiti** : Equipements réseau Ubiquiti

## Licence

Copyright (c) 2026 Jeyriku.net
