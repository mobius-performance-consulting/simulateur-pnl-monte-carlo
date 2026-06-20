"""
simulateur_pnl_gui.py

Simulateur Monte Carlo PnL — interface graphique autonome.
Tkinter + Matplotlib embarqué.

Logique prop firm :
  - Le trader dispose d'un compte financé (taille_compte).
  - Si le PnL cumulé sur le compte descend sous -DD → compte grillé.
  - Le coût (challenge + PA) est déduit du capital personnel.
  - Les paramètres de distribution décrivent le PnL journalier en POINTS.
  - Conversion en $ : PnL_$ = PnL_pts × prix_point × nb_contrats.
  - La courbe equity = capital personnel au fil du temps.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import warnings
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats import johnsonsu
from scipy.optimize import least_squares


# ============================================================
# COULEURS UI
# ============================================================

BG        = "#0F1117"
BG_PANEL  = "#1A1E2B"
BG_FIELD  = "#252A3A"
FG        = "#D0D8F0"
FG_DIM    = "#7080A0"
ACCENT    = "#4C9BE8"
ACCENT2   = "#E8A84C"
ACCENT3   = "#7BE84C"
BTN_BG    = "#2A3050"
BTN_ACT   = "#3A4570"
BORDER    = "#3A4060"
RED       = "#E85C5C"
GREEN     = "#5CE87A"


# ============================================================
# CALIBRATION JOHNSON SU
# ============================================================

def calibrate_johnson_su(mean, std, skewness, kurtosis_excess):
    std = max(std, 1e-6)
    target = np.array([mean, std, skewness, kurtosis_excess], dtype=float)

    lo = np.array([-10.0, -2.0, mean - 10 * std, np.log(std * 0.01)])
    hi = np.array([ 10.0,  2.0, mean + 10 * std, np.log(std * 100)])

    def residuals(x):
        a, b = x[0], np.exp(np.clip(x[1], -2.0, 2.0))
        loc, sc = x[2], np.exp(x[3])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            m, v, sk, ku = johnsonsu.stats(a, b, loc=loc, scale=sc, moments="mvsk")
        cur = np.array([
            float(np.nan_to_num(m,  nan=0.0)),
            float(np.nan_to_num(np.sqrt(max(float(v), 1e-12)), nan=std)),
            float(np.nan_to_num(sk, nan=0.0)),
            float(np.nan_to_num(ku, nan=0.0)),
        ])
        w = np.array([std, std, 1.0, max(1.0, abs(kurtosis_excess))], dtype=float)
        return (cur - target) / w

    log_std = np.log(std)
    guesses = [
        np.array([0.0,  log_std, mean, log_std]),
        np.array([-0.5, log_std, mean, log_std]),
        np.array([-1.0, min(log_std + 0.4, 2.0), mean, log_std]),
        np.array([0.5,  min(log_std + 0.4, 2.0), mean, log_std]),
    ]

    best = None
    for g in guesses:
        g = np.clip(g, lo, hi)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                res = least_squares(residuals, g, bounds=(lo, hi), max_nfev=20_000)
            if best is None or res.cost < best.cost:
                best = res
        except Exception:
            continue

    if best is None or best.cost > 1.0:
        return 0.0, 1.0, mean, std

    return (float(best.x[0]),
            float(np.exp(np.clip(best.x[1], -2.0, 2.0))),
            float(best.x[2]),
            float(np.exp(best.x[3])))


# ============================================================
# SIMULATION MONTE CARLO — logique prop firm
# ============================================================

def run_simulation(
    mean_pts, std_pts, skewness, kurtosis_excess,
    capital, n_days, n_sim,
    prix_point, nb_contrats,
    dd, challenge_cost,
    seed=42,
):
    """
    Simule n_sim trajectoires sur n_days jours.

    Chaque jour :
      pnl_pts  ~ Johnson SU(mean_pts, std_pts, skew, kurt)
      pnl_$    = pnl_pts × prix_point × nb_contrats
      account_pnl += pnl_$
      Si account_pnl <= -dd :
          capital -= challenge_cost   (compte grillé → on rachète)
          account_pnl = 0.0          (nouveau compte)

    Retourne :
      curves  : (n_sim × n_days) capital personnel jour par jour
      ruined  : bool par simulation (capital <= 0)
      blown   : nb de comptes grillés par simulation
    """
    a, b, loc, sc = calibrate_johnson_su(mean_pts, std_pts, skewness, kurtosis_excess)

    rng = np.random.default_rng(seed)
    daily_pts = johnsonsu.rvs(a, b, loc=loc, scale=sc,
                              size=(n_sim, n_days), random_state=rng)
    daily_usd = daily_pts * prix_point * nb_contrats

    curves      = np.empty((n_sim, n_days), dtype=float)
    blown       = np.zeros(n_sim, dtype=int)
    cap         = np.full(n_sim, capital, dtype=float)   # capital personnel restant
    account_pnl = np.zeros(n_sim, dtype=float)           # PnL en cours sur compte financé

    for d in range(n_days):
        alive = cap > 0

        account_pnl[alive] += daily_usd[alive, d]

        # Comptes grillés ce jour : compte_pnl < -DD
        grille = alive & (account_pnl <= -dd)
        cap[grille]         -= challenge_cost
        blown[grille]       += 1
        account_pnl[grille]  = 0.0

        # Plafonner capital à 0 (ruine) et figer PnL compte
        cap = np.maximum(cap, 0.0)
        account_pnl[cap <= 0] = 0.0

        # Equity = capital restant + PnL non-réalisé du compte en cours
        curves[:, d] = cap + account_pnl

    ruined = cap <= 0
    return curves, ruined, blown


# ============================================================
# WIDGET PARAMÈTRE
# ============================================================

class ParamRow:
    """Label + [−] + Champ + [+] + Curseur

    - _dvar  (DoubleVar) : valeur numérique, liée au slider.
    - _svar  (StringVar) : texte affiché dans le champ de saisie.
    Les deux sont synchronisés : le slider met à jour le champ,
    et la saisie met à jour le slider.
    """

    def __init__(self, parent, label, default, lo, hi, step,
                 fmt=".1f", row=0, callback=None):
        self.lo, self.hi, self.step = lo, hi, step
        self.fmt      = fmt
        self.callback = callback
        self._updating = False          # garde contre les boucles de synchro

        self._dvar = tk.DoubleVar(value=default)
        self._svar = tk.StringVar(value=self._fmt(default))

        # Label
        tk.Label(parent, text=label, bg=BG_PANEL, fg=FG,
                 font=("Segoe UI", 9), anchor="w", width=22
                 ).grid(row=row, column=0, padx=(8, 2), pady=3, sticky="w")

        # Bouton −
        tk.Button(parent, text="−", command=self._decrement,
                  bg=BTN_BG, fg=FG, activebackground=BTN_ACT,
                  relief="flat", width=2, font=("Segoe UI", 10, "bold"),
                  cursor="hand2"
                  ).grid(row=row, column=1, padx=2)

        # Champ de saisie (StringVar, largeur généreuse)
        self.entry = tk.Entry(parent, textvariable=self._svar,
                              bg=BG_FIELD, fg=FG, insertbackground=FG,
                              relief="flat", width=12,
                              font=("Segoe UI", 9), justify="right")
        self.entry.grid(row=row, column=2, padx=4)
        self.entry.bind("<Return>",   self._on_entry)
        self.entry.bind("<FocusOut>", self._on_entry)

        # Bouton +
        tk.Button(parent, text="+", command=self._increment,
                  bg=BTN_BG, fg=FG, activebackground=BTN_ACT,
                  relief="flat", width=2, font=("Segoe UI", 10, "bold"),
                  cursor="hand2"
                  ).grid(row=row, column=3, padx=2)

        # Curseur (DoubleVar — pas de valeur affichée par le widget)
        self.slider = tk.Scale(parent, from_=lo, to=hi,
                               resolution=step, orient="horizontal",
                               variable=self._dvar, showvalue=False,
                               bg=BG_PANEL, fg=FG, troughcolor=BG_FIELD,
                               activebackground=ACCENT, highlightthickness=0,
                               length=150, bd=0, sliderrelief="flat",
                               command=self._on_slider)
        self.slider.grid(row=row, column=4, padx=(4, 8))

    # ── Formatage ────────────────────────────────────────────────────────────

    def _fmt(self, v: float) -> str:
        """Formate la valeur pour l'affichage dans le champ."""
        if self.fmt.endswith("f"):
            decimals = int(self.fmt[1:-1])      # ".0f" → 0, ".2f" → 2
            if decimals == 0:
                return f"{int(round(v)):,}".replace(",", " ")   # "50 000"
            else:
                return f"{v:,.{decimals}f}"
        return str(v)

    def _parse(self, text: str) -> float:
        """Accepte '50000', '50 000', '50,000', '50.0', '1.5k', etc."""
        t = text.strip().replace(" ", "").replace(",", "")
        if t.lower().endswith("k"):
            return float(t[:-1]) * 1_000
        return float(t)

    # ── Synchronisation ──────────────────────────────────────────────────────

    def _clamp(self, v: float) -> float:
        return max(self.lo, min(self.hi, v))

    def _set_value(self, v: float, from_slider=False):
        """Met à jour valeur numérique + affichage, déclenche le callback."""
        if self._updating:
            return
        self._updating = True
        v = round(self._clamp(v), 8)
        self._dvar.set(v)
        self._svar.set(self._fmt(v))
        self._updating = False
        if self.callback:
            self.callback()

    def _on_slider(self, _=None):
        """Le slider a bougé : lire _dvar et mettre à jour le champ texte."""
        if self._updating:
            return
        self._updating = True
        v = self._clamp(self._dvar.get())
        self._svar.set(self._fmt(v))
        self._updating = False
        if self.callback:
            self.callback()

    def _on_entry(self, _=None):
        """L'utilisateur a validé la saisie : parser et mettre à jour le slider."""
        try:
            v = self._parse(self._svar.get())
            self._set_value(v)
        except ValueError:
            # Restaurer la valeur courante si saisie invalide
            self._svar.set(self._fmt(self._dvar.get()))

    def _increment(self):
        self._set_value(self._dvar.get() + self.step)

    def _decrement(self):
        self._set_value(self._dvar.get() - self.step)

    def get(self) -> float:
        return self._dvar.get()


def _section_label(parent, text, row, color=ACCENT):
    """Titre de section dans le panneau gauche."""
    tk.Label(parent, text=text, bg=BG_PANEL, fg=color,
             font=("Segoe UI", 9, "bold"), anchor="w"
             ).grid(row=row, column=0, columnspan=5,
                    padx=8, pady=(10, 2), sticky="w")


def _separator(parent, row):
    ttk.Separator(parent, orient="horizontal").grid(
        row=row, column=0, columnspan=5, sticky="ew", padx=8, pady=4)


# ============================================================
# APPLICATION PRINCIPALE
# ============================================================

class SimulateurApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Simulateur PnL — Monte Carlo")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()
        self._run_and_plot()

    # ── Interface ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Panneau gauche ───────────────────────────────────────────────────
        left = tk.Frame(self, bg=BG_PANEL, bd=0)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)

        cb = self._on_param_change
        r  = 0

        # — Titre général —
        tk.Label(left, text="SIMULATEUR PnL", bg=BG_PANEL, fg=FG,
                 font=("Segoe UI", 12, "bold")
                 ).grid(row=r, column=0, columnspan=5, pady=(12, 4)); r += 1

        _separator(left, r); r += 1

        # ── Section Compte prop firm ─────────────────────────────────────────
        _section_label(left, "▸  COMPTE PROP FIRM", r, ACCENT2); r += 1

        self.p_capital    = ParamRow(left, "Capital personnel ($)", 5_000,   100, 100_000, 100,  ".0f", row=r, callback=cb); r += 1
        self.p_taille_cpt = ParamRow(left, "Taille du compte ($)", 50_000, 1_000, 500_000, 1_000, ".0f", row=r, callback=cb); r += 1
        self.p_dd         = ParamRow(left, "Drawdown max ($)",         600,   100,  50_000,  100, ".0f", row=r, callback=cb); r += 1
        self.p_chall_cost = ParamRow(left, "Coût challenge + PA ($)",  180,     0,  10_000,   10, ".0f", row=r, callback=cb); r += 1

        _separator(left, r); r += 1

        # ── Section Paramètres de trading ────────────────────────────────────
        _section_label(left, "▸  TRADING (en points)", r, ACCENT3); r += 1

        self.p_prix_pt  = ParamRow(left, "Prix d'un point ($)",    5.0,   0.25, 50.0,  0.25, ".2f", row=r, callback=cb); r += 1
        self.p_nb_ctr   = ParamRow(left, "Nb micro-contrats",        1,      1,   20,    1,  ".0f", row=r, callback=cb); r += 1

        _separator(left, r); r += 1

        # ── Section Distribution journalière ─────────────────────────────────
        _section_label(left, "▸  DISTRIBUTION JOURNALIÈRE (pts)", r, ACCENT); r += 1

        self.p_mean  = ParamRow(left, "Moyenne / jour (pts)",    2.0,  -50.0,  50.0,  0.5,  ".1f", row=r, callback=cb); r += 1
        self.p_std   = ParamRow(left, "Écart-type (pts)",       20.0,    0.1, 200.0,  0.5,  ".1f", row=r, callback=cb); r += 1
        self.p_skew  = ParamRow(left, "Asymétrie",              -0.2,   -5.0,   5.0,  0.05, ".3f", row=r, callback=cb); r += 1
        self.p_kurt  = ParamRow(left, "Kurtosis excès",          3.0,    0.0,  20.0,  0.5,  ".2f", row=r, callback=cb); r += 1

        _separator(left, r); r += 1

        # ── Section Simulation ───────────────────────────────────────────────
        _section_label(left, "▸  SIMULATION", r, FG_DIM); r += 1

        self.p_days = ParamRow(left, "Jours simulés",  252,  10, 1_000,  10, ".0f", row=r, callback=cb); r += 1
        self.p_nsim = ParamRow(left, "Simulations",  1_000, 100, 10_000, 100, ".0f", row=r, callback=cb); r += 1

        _separator(left, r); r += 1

        # ── Bouton lancer ────────────────────────────────────────────────────
        tk.Button(left, text="▶  Lancer la simulation",
                  command=self._run_and_plot,
                  bg=ACCENT, fg="white", activebackground="#3A8BCC",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  cursor="hand2", pady=7
                  ).grid(row=r, column=0, columnspan=5, padx=10, sticky="ew"); r += 1

        self.status_var = tk.StringVar(value="")
        tk.Label(left, textvariable=self.status_var,
                 bg=BG_PANEL, fg=FG_DIM,
                 font=("Segoe UI", 8), wraplength=320, justify="left"
                 ).grid(row=r, column=0, columnspan=5, padx=8, pady=(4, 8), sticky="w")

        # ── Panneau droit : graphique ────────────────────────────────────────
        right = tk.Frame(self, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        self.fig = Figure(figsize=(10, 6))
        self.fig.patch.set_facecolor(BG)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _on_param_change(self):
        if int(self.p_nsim.get()) <= 2_000:
            self._run_and_plot()

    def _run_and_plot(self):
        capital      = float(self.p_capital.get())
        taille_cpt   = float(self.p_taille_cpt.get())
        dd           = float(self.p_dd.get())
        chall_cost   = float(self.p_chall_cost.get())
        prix_pt      = float(self.p_prix_pt.get())
        nb_ctr       = int(self.p_nb_ctr.get())
        mean_pts     = float(self.p_mean.get())
        std_pts      = float(self.p_std.get())
        skew         = float(self.p_skew.get())
        kurt         = float(self.p_kurt.get())
        n_days       = int(self.p_days.get())
        n_sim        = int(self.p_nsim.get())

        self.status_var.set("Simulation en cours…")
        self.update_idletasks()

        try:
            curves, ruined, blown = run_simulation(
                mean_pts, std_pts, skew, kurt,
                capital, n_days, n_sim,
                prix_pt, nb_ctr,
                dd, chall_cost,
            )
            self._draw(curves, ruined, blown,
                       capital, taille_cpt, dd, chall_cost,
                       prix_pt, nb_ctr, mean_pts, std_pts, skew, kurt)

            prob      = ruined.mean() * 100
            pnl_med   = np.median(curves[:, -1]) - capital
            blown_med = int(np.median(blown))
            self.status_var.set(
                f"✓  {n_sim} simulations — ruine {prob:.1f} % — "
                f"capital médian final {np.median(curves[:,-1]):,.0f} $ — "
                f"comptes grillés (médiane) {blown_med}"
            )
        except Exception as exc:
            self.status_var.set(f"Erreur : {exc}")
            raise

    # ── Tracé ────────────────────────────────────────────────────────────────

    def _draw(self, curves, ruined, blown,
              capital, taille_cpt, dd, chall_cost,
              prix_pt, nb_ctr, mean_pts, std_pts, skew, kurt):

        ax = self.ax
        ax.clear()
        ax.set_facecolor(BG)
        ax.tick_params(colors="#A0B0D0", labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)
        ax.grid(True, color="#2A2E40", linewidth=0.4, alpha=0.6)

        n_sim, n_days = curves.shape
        days = np.arange(1, n_days + 1)

        p05 = np.percentile(curves, 5,  axis=0)
        p50 = np.percentile(curves, 50, axis=0)
        p95 = np.percentile(curves, 95, axis=0)

        final      = curves[:, -1]
        prob_ruin  = ruined.mean() * 100
        cap_med    = np.median(final)
        cap_p05    = np.percentile(final, 5)
        cap_p95    = np.percentile(final, 95)
        blown_med  = float(np.median(blown))
        blown_p95  = float(np.percentile(blown, 95))

        # Échelle
        mx = float(np.nanmax(np.abs(np.concatenate([p05, p95, [capital]]))))
        if mx >= 1_000_000:
            scale, unit = 1e6, "M$"
        elif mx >= 1_000:
            scale, unit = 1e3, "k$"
        else:
            scale, unit = 1.0, "$"

        # Zone P5/P95
        ax.fill_between(days, p05 / scale, p95 / scale,
                        alpha=0.18, color=ACCENT, label="Zone P5 – P95")

        # Médiane
        ax.plot(days, p50 / scale, color=ACCENT, linewidth=2.2, label="Médiane")

        # Lignes P5 / P95
        ax.plot(days, p05 / scale, color=RED,   linewidth=1.0,
                linestyle="--", alpha=0.75, label="P5")
        ax.plot(days, p95 / scale, color=GREEN, linewidth=1.0,
                linestyle="--", alpha=0.75, label="P95")

        # Capital initial
        ax.axhline(capital / scale, color="white",
                   linewidth=0.8, linestyle=":", alpha=0.5,
                   label=f"Capital initial ({capital:,.0f} $)")

        # Titre & axes
        ax.set_title(
            f"Simulation Monte Carlo — Capital personnel — {n_sim} trajectoires — {n_days} jours",
            color="white", fontsize=11, fontweight="bold", pad=10,
        )
        ax.set_xlabel("Jour de trading", color="#A0B0D0", fontsize=9)
        ax.set_ylabel(f"Capital + PnL compte ({unit})", color="#A0B0D0", fontsize=9)
        ax.legend(fontsize=8, facecolor=BG_PANEL, edgecolor=BORDER,
                  labelcolor=FG, loc="upper left")

        # ── Encadré statistiques (bas droite) ──────────────────────────────
        fmt_cap = lambda v: f"{v / scale:,.1f} {unit}"
        stats = (
            f"Prob. de ruine         : {prob_ruin:.1f} %\n"
            f"Capital médian final   : {fmt_cap(cap_med)}\n"
            f"Capital P95 final      : {fmt_cap(cap_p95)}\n"
            f"Capital P5 final       : {fmt_cap(cap_p05)}\n"
            f"Comptes grillés (méd.) : {blown_med:.0f}\n"
            f"Comptes grillés (P95)  : {blown_p95:.0f}"
        )
        ax.text(0.98, 0.04, stats,
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=9, color=FG, fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.5", facecolor=BG_PANEL,
                          edgecolor=BORDER, alpha=0.92))

        # ── Encadré paramètres (haut droite) ───────────────────────────────
        pnl_moy_j  = mean_pts * prix_pt * nb_ctr
        pnl_std_j  = std_pts  * prix_pt * nb_ctr
        params = (
            f"Compte : {taille_cpt:,.0f} $  |  DD : {dd:,.0f} $\n"
            f"Coût challenge+PA : {chall_cost:,.0f} $\n"
            f"Prix point : {prix_pt:.2f} $  |  Contrats : {nb_ctr}\n"
            f"PnL moy/jour : {pnl_moy_j:+.1f} $  "
            f"σ : {pnl_std_j:.1f} $\n"
            f"Asymétrie : {skew:.3f}  |  Kurtosis exc. : {kurt:.2f}"
        )
        ax.text(0.98, 0.97, params,
                transform=ax.transAxes, ha="right", va="top",
                fontsize=8, color="#A0B0D0", fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=BG_PANEL,
                          edgecolor=BORDER, alpha=0.85))

        self.fig.tight_layout()
        self.canvas.draw()


# ============================================================
# ENTRÉE
# ============================================================

if __name__ == "__main__":
    app = SimulateurApp()
    app.mainloop()
