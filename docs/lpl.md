# Logistic plus linear (LPL) Model

This model proposes a latent true coverage curve, which is subject to observation error. A hierarchy accounts for the effects of categorical features.

## Terminology and notation

- $C_{sgm}$: reported, estimated coverage (proportion of people vaccinated) in season $s$, geography (i.e., state) $g$, and month $m$ (`estimate` in the data)
- $N_{sgm}$: number of people surveyed (`sample_size` in the data)
- $v_{sg}(t)$: latent true coverage at time $t$ (measured in years)

## Model equations

```math
\begin{align*}
X_{sgm} &= \mathrm{round}(C_{sgm} \cdot N_{sgm}) \\
v_{sg}(t) &= \frac{A_{sg}}{1 + \exp\{- K \cdot (t - \tau)\}} + B_{sg} t \\
A_{sg} &= \beta^{(A)} + \beta_s^{(AS)} + \beta_g^{(AG)} + \beta_{sg}^{(ASG)} \\
B_{sg} &= \beta^{(B)} + \beta_s^{(BS)} + \beta_g^{(BG)} + \beta_{sg}^{(BSG)} \\
\\
X_{sgm} &\sim \mathrm{BetaBinom}\big( N_{sgm}, v_{sg}(t_m) \cdot D, [1-v_{sg}(t_m)] \cdot D \big) \\
K &\sim \text{Gamma}(\text{shape} = 25.0, \text{rate} = 1.0) \\
\tau &\sim \text{Beta}(100.0, 225.0) \\
D &\sim \text{Gamma}(\text{shape} = 350.0, \text{rate} = 1.0) \\
\beta^{(A)} &\sim \text{Beta}(100.0, 180.0) \\
\beta_s^{(AS)} &\sim \mathcal{N}\left(0, \sigma^{(AS)}\right) \\
\beta_g^{(AG)} &\sim \mathcal{N}\left(0, \sigma^{(AG)}\right) \\
\beta_{sg}^{(ASG)} &\sim \mathcal{N}\left(0, \sigma^{(ASG)}\right) \\
\beta^{(B)} &\sim \text{Gamma}(\text{shape} = 1.0, \text{rate} = 10.0) \\
\beta_s^{(BS)} &\sim \mathcal{N}\left(0, \sigma^{(BS)}\right) \\
\beta_g^{(BG)} &\sim \mathcal{N}\left(0, \sigma^{(BG)}\right) \\
\beta_{sg}^{(BSG)} &\sim \mathcal{N}\left(0, \sigma^{(BSG)}\right) \\
\sigma^{(\bullet)} &\sim \text{Exp}(40.0) \\
\end{align*}
```

Notes:

- The latent coverage $v_{sg}(t)$ is assumed to be a sum of a logistic curve and a line with intercept at $t=0$
- The shape parameter $K$ and midpoint $\tau$ of the logistic curve are assumed to be common to all groups
- The height $A_{sg}$ of the logistic curve is a grand mean $\beta^{(A)}$ plus effects for the season, state, and season-state interaction. The slopes $M_g$ follow a similar pattern.

```math
\begin{align*}
\mathbb{E}[X_{sgk}] &= v_{sg}(t_k) \cdot N_{sgk} \\
\mathrm{Var}[X_{sgk}] &= v_{sg}(t_k) \cdot [1-v_{sg}(t_k)] \cdot \frac{N_{sgk} (N_{sgk} + D)}{D+1}
\end{align*}
```
