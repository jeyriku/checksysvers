# Check Sysvers

Ce script vérifie la version du système d'exploitation pour des systèmes locaux et distants, y compris Linux, Windows, macOS, Cisco, Juniper et Ubiquiti.

## Fonctionnalités

- **Vérification locale** : Détecte et affiche la version OS du système hôte.
- **Vérification distante** : Se connecte via SSH à des appareils distants pour récupérer leur version OS.
- **Récupération d'inventaire** : Utilise l'API GraphQL d'Infrahub ou le SDK Python pour obtenir la liste des appareils.

## Prérequis

- Python 3.x
- Modules : `platform`, `subprocess`, `logging`, `os`, `httpx`, `infrahub`
- Pour les vérifications distantes : SSH configuré, variables d'environnement pour les credentials.

## Variables d'environnement

- `SSH_USERNAME` : Nom d'utilisateur SSH
- `SSH_PASSWORD` : Mot de passe SSH
- `SSH_PORT` : Port SSH (défaut 22)
- `INFRAHUB_API_TOKEN` : Token pour l'API Infrahub
- `INFRAHUB_URL` : URL de l'API Infrahub (défaut https://infrahub.example.com/graphql)

## Utilisation

Exécutez le script :

```bash
python check_sysvers.py
```

Le script effectuera une vérification locale et tentera de récupérer la liste des appareils distants si configuré.

## Structure du code

- `LocalSysVersChecker` : Classe pour les vérifications locales.
- `RemoteSysVersChecker` : Classe pour les vérifications distantes, incluant la récupération d'inventaire via Infrahub.

## Licence

Copyright (c) 2026 Jeyriku.net
