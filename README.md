# Algorithme de Demoucron

Application GUI interactive pour le calcul des chemins minimaux/maximaux utilisant l'algorithme de Demoucron (variante du Floyd-Warshall).

## 🎯 Fonctionnalités

- **Tableau éditable** : Saisie intuitive de la matrice d'adjacence (graphe orienté)
- **Visualisation graphique** : Représentation visuelle du graphe
- **Calcul MIN/MAX** : Deux variantes de l'algorithme (distances minimales ou chemins maximaux)
- **Historique étape-par-étape** : Visualisation de la progression du calcul
- **Validation intelligente** : Vérification des entrées en temps réel (0-1000)

## 📋 Prérequis

- Python 3.7 ou supérieur
- Tkinter (inclus dans Python par défaut)
- **Pillow** (PIL) - pour charger l'icône PNG

## 🚀 Installation

```bash
git clone <repository-url>
cd "Projet R.O"

# Installer les dépendances
pip install Pillow

# Lancer l'application
python demoucron_app.py
```

## 💡 Utilisation

1. **Définir la matrice**
   - Saisir les poids dans le tableau (laisser vide pour absence d'arc)
   - Les valeurs doivent être entre 0 et 1000

2. **Ajouter/Modifier des arcs**
   - Cliquer sur le graphe pour ajouter des connexions
   - Le poids peut être modifié après création

3. **Calculer**
   - Sélectionner MIN ou MAX
   - Cliquer "Calculer"
   - Consulter le résultat et l'historique

## 📁 Structure du projet

```
Projet R.O/
├── demoucron_app.py      # Interface graphique (GUI Tkinter)
├── demoucron.py          # Implémentation de l'algorithme
├── .gitignore            # Fichiers à ignorer par Git
└── README.md             # Ce fichier
```

## 🔧 Détails techniques

### Algorithme
- **Demoucron MIN** : Recherche de plus courts chemins (absence d'arc = +∞)
- **Demoucron MAX** : Recherche de chemins maximaux (absence d'arc = 0)
- Complexité : O(n³) où n est le nombre de noeuds

### Interface
- **Framework** : Tkinter (GUI native Python)
- **Validation** : Entrées limitées à [0, 1000]
- **Design** : Palette de 11 couleurs professionnelles

## 📝 Licence

[À configurer]

## 👤 Auteur

Développé avec assistance IA (GitHub Copilot)
