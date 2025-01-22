# GlassFinder - Détection et Segmentation des Fenêtres sur les Façades de Bâtiments

## Description du projet
**GlassFinder** est un projet qui combine intelligence artificielle et vision par ordinateur pour détecter et segmenter les fenêtres sur des images de façades de bâtiments. En utilisant un modèles avancés comme Mask R-CNN, ainsi qu'un pipeline d'application web basé sur FastAPI et Vue.js, ce projet vise à offrir une solution puissante, précise et intuitive pour l'analyse d'images architecturales.

## Fonctionnalités principales
- **Détection et segmentation des fenêtres** : Identification précise des contours des fenêtres avec des masques détaillés.
- **Détection des points de fuite** : Analyse géométrique des images pour extraire les points de perspective principaux.
- **Application web interactive** : 
  - **Backend** : FastAPI pour gérer les requêtes API et le traitement des modèles IA.
  - **Frontend** : Vue.js pour une interface utilisateur intuitive permettant l'affichage et la modification des annotations.

## Technologies utilisées
### Intelligence Artificielle
- **Frameworks** : PyTorch et TensorFlow
- **Modèles** :
  - Mask R-CNN (segmentation précise des fenêtres)
  - YOLO (détection rapide et légère)

### Backend
- **Framework** : FastAPI
- **Points de terminaison** :
  - Prédiction des fenêtres
  - Détection des points de fuite

### Frontend
- **Framework** : Vue.js
- **Fonctionnalités** :
  - Téléchargement et affichage d'images
  - Visualisation et édition des annotations
 
# Guide d'installation

## Prérequis
Assurez-vous que les outils suivants sont installés sur votre machine :
1. **Python** (version 3.8 ou ultérieure)
2. **Node.js** (version 14 ou ultérieure)
3. **npm** (généralement inclus avec Node.js)
4. **Git** (pour cloner le dépôt)
5. **pip** (gestionnaire de paquets Python)

---

## Étape 1 : Cloner le dépôt
Commencez par cloner ce dépôt GitHub :
```bash
git clone https://github.com/TRoutin/PFE_GlassFinder
cd PFE_GlassFinder
```

---

## Étape 2 : Configurer l'environnement backend

1. **Installer les dépendances Python** :
   ```bash
   cd web/backend
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Tester le backend** :
   Pour démarrer le backend avec FastAPI :
   ```bash
   python -m uvicorn app:app --reload
   ```
   Par défaut, l'application sera disponible à l'adresse : [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Étape 3 : Configurer l'environnement frontend

1. **Se déplacer dans le dossier `frontend/app`** :
   ```bash
   cd frontend/app
   ```

2. **Installer les dépendances npm** :
   ```bash
   npm install
   ```

3. **Démarrer le serveur de développement Vue.js** :
   ```bash
   npm run serve
   ```
   Par défaut, l'application sera disponible à l'adresse : [http://localhost:8080](http://localhost:8080)

---
