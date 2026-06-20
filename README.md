# Simulateur PnL — Monte Carlo

> **Simulez les trajectoires de votre capital de trader en quelques clics.**  
> *Simulate your trading capital trajectories with a few clicks.*

---

## Français

### C'est quoi ce programme ?

Ce simulateur vous permet de **voir dans le futur** — pas vraiment, mais presque.

En entrant quelques chiffres qui décrivent votre façon de trader, le programme va générer **1 000 scénarios possibles** de ce qui pourrait arriver à votre capital sur une période donnée. Certains scénarios seront bons, d'autres mauvais — la réalité sera quelque part entre les deux.

### À quoi ça sert concrètement ?

- Savoir si votre stratégie est **viable à long terme**
- Comprendre le risque de **perdre votre capital** (probabilité de ruine)
- Voir ce qui se passe si vous tradez avec un **compte prop firm** et que vous vous faites griller
- Tester l'impact de changer vos paramètres de trading **avant de prendre de l'argent réel**

### Comment utiliser le programme ?

#### 1. Lancer l'application

Double-cliquez sur `SimulateurPnL.exe`. Une fenêtre s'ouvre avec deux zones :
- **À gauche** : vos paramètres
- **À droite** : le graphique qui se met à jour automatiquement

#### 2. Remplir les paramètres

**Compte Prop Firm**

| Paramètre | Explication simple |
|---|---|
| Capital personnel ($) | L'argent que VOUS avez mis de côté pour les challenges |
| Taille du compte ($) | La taille du compte financé que vous obtenez après le challenge |
| Drawdown max ($) | La perte maximale tolérée sur le compte avant qu'il soit fermé |
| Coût challenge + PA ($) | Ce que vous payez pour obtenir un nouveau compte (challenge + compte réel) |

**Trading (en points)**

| Paramètre | Explication simple |
|---|---|
| Prix d'un point ($) | La valeur d'un point de mouvement pour votre instrument |
| Nb micro-contrats | Le nombre de contrats que vous tradez |

> **Exemple** : Sur le MES (micro S&P500), 1 point = 5 $. Si vous tradez 2 micro-contrats, chaque point de mouvement vous rapporte ou vous coûte 10 $.

**Distribution journalière (en points)**

C'est la partie la plus importante — elle décrit votre style de trading :

| Paramètre | Explication simple |
|---|---|
| Moyenne / jour (pts) | Votre gain moyen par jour de trading (en points) |
| Écart-type (pts) | Combien vos résultats varient d'un jour à l'autre |
| Asymétrie | Si vos grosses journées sont plutôt positives ou négatives (-1 à +1) |
| Kurtosis excès | Si vous avez souvent des journées "extrêmes" (0 = normal, >3 = beaucoup d'extrêmes) |

> **Comment trouver ces chiffres ?** Exportez votre historique de trades, calculez le PnL par jour de trading, puis utilisez Excel (fonctions MOYENNE, ECARTYPE, KUURT, ASYMETRIE).

#### 3. Lire le graphique

- **Ligne bleue** : la trajectoire médiane — la moitié des simulations finissent au-dessus, l'autre moitié en-dessous
- **Zone bleue claire** : la zone entre les 5 % les pires et les 5 % les meilleurs
- **Ligne rouge pointillée** : les 5 % les pires scénarios
- **Ligne verte pointillée** : les 5 % les meilleurs scénarios

#### 4. Lire le résumé (cadre en bas à droite)

| Statistique | Ce que ça veut dire |
|---|---|
| Prob. de ruine | Chance de perdre tout votre capital personnel |
| Capital médian final | Dans 50 % des cas, vous terminez avec au moins ce montant |
| Capital P95 final | Dans 5 % des meilleurs cas, vous terminez avec ce montant |
| Capital P5 final | Dans 5 % des pires cas, vous terminez avec ce montant |
| Comptes grillés (méd.) | Nombre de comptes perdus en cours de route (médiane) |

### Exemple de paramètres réalistes

Pour un trader MES scalper débutant :

```
Capital personnel   : 2 000 $
Taille du compte    : 50 000 $
Drawdown max        : 2 000 $
Coût challenge + PA : 500 $
Prix d'un point     : 5 $ (MES)
Nb micro-contrats   : 1
Moyenne / jour      : 1 point
Écart-type          : 8 points
Asymétrie           : -0.2
Kurtosis excès      : 3.0
Jours simulés       : 252 (1 an)
```

---

## English

### What is this program?

This simulator lets you **see into the future** — not really, but close enough.

By entering a few numbers that describe how you trade, the program generates **1,000 possible scenarios** of what could happen to your capital over a given period. Some scenarios will be good, others bad — reality will be somewhere in between.

### What is it useful for?

- Checking whether your strategy is **viable long-term**
- Understanding your risk of **blowing your capital** (probability of ruin)
- Seeing what happens when trading a **prop firm account** and getting stopped out
- Testing the impact of changing your trading parameters **before risking real money**

### How to use the program?

#### 1. Launch the application

Double-click `SimulateurPnL.exe`. A window opens with two areas:
- **Left panel**: your parameters
- **Right panel**: the chart, which updates automatically

#### 2. Fill in the parameters

**Prop Firm Account**

| Parameter | Simple explanation |
|---|---|
| Personal capital ($) | The money YOU have set aside for challenges |
| Account size ($) | The funded account size you receive after passing the challenge |
| Max drawdown ($) | The maximum loss tolerated before the account is closed |
| Challenge + PA cost ($) | What you pay to get a new account (challenge + funded account) |

**Trading (in points)**

| Parameter | Simple explanation |
|---|---|
| Price per point ($) | The dollar value of one point move for your instrument |
| Nb of micro-contracts | The number of contracts you trade |

> **Example**: On MES (micro S&P500), 1 point = $5. If you trade 2 micro-contracts, each point of movement earns or costs you $10.

**Daily Distribution (in points)**

This is the most important part — it describes your trading style:

| Parameter | Simple explanation |
|---|---|
| Average / day (pts) | Your average daily gain in points |
| Standard deviation (pts) | How much your results vary from day to day |
| Skewness | Whether your big days are more often positive or negative (-1 to +1) |
| Excess kurtosis | How often you have "extreme" days (0 = normal, >3 = many extremes) |

> **How to find these numbers?** Export your trade history, calculate the PnL per trading day, then use Excel (AVERAGE, STDEV, KURT, SKEW functions).

#### 3. Reading the chart

- **Blue line**: the median trajectory — half the simulations end above, half below
- **Light blue zone**: the range between the worst 5% and best 5%
- **Red dashed line**: the worst 5% of scenarios
- **Green dashed line**: the best 5% of scenarios

#### 4. Reading the summary (bottom-right box)

| Statistic | What it means |
|---|---|
| Probability of ruin | Chance of losing all your personal capital |
| Median final capital | In 50% of cases, you end with at least this amount |
| P95 final capital | In the best 5% of cases, you end with this amount |
| P5 final capital | In the worst 5% of cases, you end with this amount |
| Blown accounts (med.) | Number of accounts lost along the way (median) |

### Example of realistic parameters

For a beginner MES scalper:

```
Personal capital      : $2,000
Account size          : $50,000
Max drawdown          : $2,000
Challenge + PA cost   : $500
Price per point       : $5 (MES)
Nb micro-contracts    : 1
Average / day         : 1 point
Standard deviation    : 8 points
Skewness              : -0.2
Excess kurtosis       : 3.0
Days simulated        : 252 (1 year)
```

---

## Installation

### Option 1 — Executable (recommended, no Python required)

1. Download `SimulateurPnL.exe` from the `dist/` folder
2. Double-click to run — no installation needed

### Option 2 — Python source

Requirements:
```
Python 3.9+
numpy
matplotlib
scipy
tkinter (included with Python)
```

Install dependencies:
```bash
pip install numpy matplotlib scipy
```

Run:
```bash
python simulateur_pnl_gui.py
```

---

## Disclaimer / Avertissement

**FR** : Ce simulateur est un outil pédagogique. Les résultats sont basés sur des hypothèses statistiques et ne constituent en aucun cas une garantie de performance future. Le trading comporte des risques de pertes.

**EN**: This simulator is an educational tool. Results are based on statistical assumptions and do not constitute any guarantee of future performance. Trading involves risk of loss.

---

*Développé par / Developed by [Mobius Performance Consulting](https://github.com/mobius-performance-consulting)*
