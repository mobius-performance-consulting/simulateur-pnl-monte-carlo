# Changelog

Toutes les modifications notables de ce projet sont documentées ici.  
All notable changes to this project are documented here.

---

## [1.0.0] — 2026-06-20

### Français — Première version publique

#### Nouveautés
- Interface graphique complète (Tkinter + Matplotlib embarqué)
- Simulation Monte Carlo de 100 à 10 000 trajectoires
- Modélisation de la distribution des PnL journaliers via une loi **Johnson SU**
  - Prend en compte la moyenne, l'écart-type, l'asymétrie et le kurtosis
  - Adapté aux distributions non-normales typiques du trading (queues épaisses, asymétrie)
- Logique **compte prop firm** intégrée :
  - Drawdown maximum sur le compte financé
  - Coût de rachat (challenge + compte PA) déduit du capital personnel à chaque compte grillé
  - Conversion points → dollars via le prix du point et le nombre de contrats
- Graphique interactif avec :
  - Trajectoire médiane
  - Zone P5/P95 (les 5 % meilleurs et les 5 % pires)
  - Lignes P5 et P95 séparées
  - Ligne du capital initial
- Encadré de statistiques (bas droite) :
  - Probabilité de ruine
  - Capital médian, P5, P95 en fin de période
  - Nombre de comptes grillés (médiane et P95)
- Encadré des paramètres (haut droite) : rappel visuel des réglages en cours
- Mise à jour automatique du graphique lors du déplacement des curseurs (≤ 2 000 simulations)
- Saisie flexible des grandes valeurs : `50000`, `50 000`, `50,000` ou `50k` sont tous acceptés
- Curseurs + boutons +/− pour tous les paramètres
- Export en exécutable Windows autonome (`.exe`) — aucune installation Python requise

---

### English — First public release

#### New features
- Full graphical interface (Tkinter + embedded Matplotlib)
- Monte Carlo simulation from 100 to 10,000 trajectories
- Daily PnL distribution modeled via **Johnson SU** distribution
  - Takes into account mean, standard deviation, skewness and kurtosis
  - Suited for non-normal distributions typical in trading (fat tails, asymmetry)
- Integrated **prop firm account** logic:
  - Maximum drawdown on the funded account
  - Repurchase cost (challenge + PA account) deducted from personal capital on each blown account
  - Point-to-dollar conversion via point price and number of contracts
- Interactive chart with:
  - Median trajectory
  - P5/P95 band (best 5% and worst 5%)
  - Separate P5 and P95 lines
  - Initial capital reference line
- Statistics box (bottom right):
  - Probability of ruin
  - Median, P5, P95 capital at end of period
  - Number of blown accounts (median and P95)
- Parameters box (top right): visual reminder of current settings
- Automatic chart update when sliders move (≤ 2,000 simulations)
- Flexible input for large values: `50000`, `50 000`, `50,000` or `50k` all accepted
- Sliders + +/− buttons for all parameters
- Export as standalone Windows executable (`.exe`) — no Python installation required
