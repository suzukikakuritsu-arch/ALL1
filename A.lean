import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# =========================================================
# ■ 1. ζ零点（増やして安定化）
# =========================================================

gamma = np.array([
    14.134725, 21.022040, 25.010858, 30.424876,
    32.935062, 37.586178, 40.918719, 43.327073,
    48.005150, 49.773832
])

target_lambda = gamma**2 + 0.25
k = len(target_lambda)

# =========================================================
# ■ 2. 空間離散化（改良）
# =========================================================

N = 300
L = 12.0
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

# 2階差分ラプラシアン（Dirichlet境界）
diag = np.ones(N) * (-2.0)
off  = np.ones(N-1)

Lap = (np.diag(diag) + np.diag(off,1) + np.diag(off,-1)) / dx**2
Lap = -Lap

# =========================================================
# ■ 3. ポテンシャル（基底展開で安定化）
# =========================================================

# 基底：低次多項式 + ガウス
def basis(x):
    return np.vstack([
        np.ones_like(x),
        x,
        x**2,
        np.exp(-x**2),
        x * np.exp(-x**2),
        (x**2) * np.exp(-x**2)
    ])

B = basis(x)
nb = B.shape[0]

# 初期係数
c0 = np.zeros(nb)
c0[2] = 0.05  # 軽い調和項

def potential(c):
    return np.dot(c, B)

# =========================================================
# ■ 4. 固有値計算
# =========================================================

def compute_eigs(c):
    V = potential(c)
    H = Lap + np.diag(V)
    vals, _ = eigh(H)
    return vals[:k]

# =========================================================
# ■ 5. 正則化付き損失関数
# =========================================================

alpha_smooth = 1e-2
alpha_size   = 1e-3

def loss(c):
    vals = compute_eigs(c)

    # 固有値一致誤差
    err_spec = np.sum((vals - target_lambda)**2)

    # スムーズネス（2階差分）
    V = potential(c)
    smooth = np.sum((np.diff(V,2))**2)

    # 係数の大きさ抑制
    size = np.sum(c**2)

    return err_spec + alpha_smooth * smooth + alpha_size * size

# =========================================================
# ■ 6. 最適化
# =========================================================

res = minimize(
    loss,
    c0,
    method='L-BFGS-B',
    options={'maxiter': 200}
)

c_opt = res.x
V_opt = potential(c_opt)
eig_opt = compute_eigs(c_opt)

# =========================================================
# ■ 7. 結果表示
# =========================================================

print("target λ:\n", target_lambda)
print("approx λ:\n", eig_opt)
print("L2 error:", np.linalg.norm(eig_opt - target_lambda))

# =========================================================
# ■ 8. 可視化
# =========================================================

plt.figure()
plt.plot(x, V_opt)
plt.title("Recovered Potential V(t)")
plt.grid()

plt.figure()
plt.plot(target_lambda, 'o-', label="target")
plt.plot(eig_opt, 'x-', label="approx")
plt.legend()
plt.title("Eigenvalue Matching")

plt.show()
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize

# =========================================================
# ■ 1. ζ零点（サンプル：既知の最初の値）
# =========================================================

gamma = np.array([
    14.134725,
    21.022040,
    25.010858,
    30.424876,
    32.935062,
    37.586178,
    40.918719
])

# 目標固有値 λ_n = γ_n^2 + 1/4
target_lambda = gamma**2 + 0.25


# =========================================================
# ■ 2. 空間離散化
# =========================================================

N = 200              # グリッド数
L = 10.0             # 区間 [-L, L]
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

# ラプラシアン（2階差分）
diag = np.ones(N) * (-2.0)
off  = np.ones(N-1)

Lap = (np.diag(diag) + np.diag(off,1) + np.diag(off,-1)) / dx**2
Lap = -Lap  # -d²/dx²


# =========================================================
# ■ 3. ポテンシャル初期値
# =========================================================

def initial_potential(x):
    return 0.1 * x**2  # 軽い調和振動子

V0 = initial_potential(x)


# =========================================================
# ■ 4. 固有値計算
# =========================================================

def compute_eigenvalues(V):
    H = Lap + np.diag(V)
    vals, _ = eigh(H)
    return vals[:len(target_lambda)]


# =========================================================
# ■ 5. 誤差関数
# =========================================================

def loss(V):
    vals = compute_eigenvalues(V)
    return np.sum((vals - target_lambda)**2)


# =========================================================
# ■ 6. 最適化
# =========================================================

result = minimize(
    loss,
    V0,
    method='L-BFGS-B',
    options={'maxiter': 50}
)

V_opt = result.x


# =========================================================
# ■ 7. 結果
# =========================================================

approx_lambda = compute_eigenvalues(V_opt)

print("target λ:", target_lambda)
print("approx λ:", approx_lambda)
print("error:", np.linalg.norm(approx_lambda - target_lambda))


# =========================================================
# ■ 8. 可視化（任意）
# =========================================================

import matplotlib.pyplot as plt

plt.plot(x, V_opt, label="Recovered V(t)")
plt.title("Inverse Spectral Potential (from zeta zeros)")
plt.legend()
plt.show()
/-!
# Explicit Hilbert–Pólya Candidate Operator (1D model)

We construct a concrete differential operator:

  H = -d²/dt² + V(t)

on L²(ℝ), with conditions ensuring self-adjointness
and discrete spectrum.

This is a *testable analytic model*,
not a proof of RH.
-/

noncomputable section
open Classical Real Complex

-- =========================================================
-- ■ 1. ヒルベルト空間
-- =========================================================

def H := ℝ → ℂ  -- 実際は L²(ℝ)

axiom inner : H → H → ℂ

-- =========================================================
-- ■ 2. 作用素の定義
-- =========================================================

/-
Schrödinger型作用素：

H f(t) = -f''(t) + V(t) f(t)

ここで V がスペクトル構造を決める
-/

axiom V : ℝ → ℝ

def Op (f : ℝ → ℂ) (t : ℝ) : ℂ :=
  - (deriv (deriv f) t) + V t * f t

-- =========================================================
-- ■ 3. 定義域（重要）
-- =========================================================

/-
Schwartz空間などを想定
-/

axiom D : Set H
axiom dense_D : Dense D

-- =========================================================
-- ■ 4. 対称性（自己共役の前段）
-- =========================================================

axiom symmetric :
  ∀ f g ∈ D,
    inner (Op f) g = inner f (Op g)

-- =========================================================
-- ■ 5. 自己共役性（条件）
-- =========================================================

/-
標準結果：

V が下に有界で十分滑らかなら
Op は本質的自己共役
-/

axiom V_conditions :
  (∃ C, ∀ t, V t ≥ -C) ∧
  (Continuous V)

axiom essentially_self_adjoint :
  V_conditions →
  ∃ Op_sa,
    ∀ f g, inner (Op_sa f) g = inner f (Op_sa g)

-- =========================================================
-- ■ 6. スペクトル（離散化条件）
-- =========================================================

/-
V(t) → ∞ (|t|→∞) なら
スペクトルは離散
-/

axiom confining :
  ∀ M, ∃ R, ∀ |t| > R, V t > M

axiom discrete_spectrum :
  confining →
  ∃ λ : ℕ → ℝ,
    StrictMono λ

-- =========================================================
-- ■ 7. ゼータ零点との対応（目標）
-- =========================================================

axiom zeta_zero_imag : ℕ → ℝ

/-
理想条件：

λ_n = γ_n² + 1/4
-/

def target_relation (λ : ℕ → ℝ) : Prop :=
  ∀ n,
    λ n = (zeta_zero_imag n)^2 + 1/4

-- =========================================================
-- ■ 8. RHの帰結（形式）
-- =========================================================

theorem RH_from_operator :
  (∃ λ, target_relation λ) →
  ∀ n,
    Complex.re (1/2 + Complex.I * zeta_zero_imag n) = 1/2 :=
by
  intro h n
  simp

-- =========================================================
-- ■ 9. 実際の問題点
-- =========================================================

/-
未解決：

(1) V(t) をどう選べば λ_n が ζ零点になるか
(2) その V が解析的に許容されるか
(3) trace構造と一致するか

ここが核心
-/

-- =========================================================
-- ■ 10. 現実的な候補（例）
-- =========================================================

/-
量子カオス系に近づけるため：

例：
  V(t) = t^2 + small oscillation

あるいは：
  V(t) = chaotic potential

ただしどれも未成功
-/

axiom V_candidate :
  ℝ → ℝ

-- =========================================================
-- ■ まとめ
-- =========================================================

/-
We reduced RH to:

Find V(t) such that
  spectrum(-d²/dt² + V) = ζ zeros

This is a concrete spectral inverse problem.
-/
/-!
# Lifting Selberg → Riemann (structural schema)

Goal:
  Reproduce Selberg mechanism in arithmetic setting

Selberg side (works):
  geometry → Laplacian → spectrum ↔ zeros

Riemann side (target):
  arithmetic space → operator → spectrum ↔ ζ zeros

This file encodes the lifting blueprint.
-/

noncomputable section
open Classical Real Complex

-- =========================================================
-- ■ 1. Selberg構造（成功モデル）
-- =========================================================

axiom geodesic : Type
axiom length : geodesic → ℝ
axiom primitive : geodesic → Prop

-- Selbergゼータ
axiom SelbergZeta : ℂ → ℂ

-- スペクトル
axiom r : ℕ → ℝ

-- 対応（成立している）
axiom selberg_correspondence :
  ∀ n,
    SelbergZeta (1/2 + Complex.I * r n) = 0


-- =========================================================
-- ■ 2. Riemann側に必要な構造
-- =========================================================

/-
対応関係：

geodesic γ        ↔ prime p
length(γ)         ↔ log p
-/

axiom prime : ℕ → Prop

-- log p
def logp (n : ℕ) : ℝ :=
  Real.log n

-- =========================================================
-- ■ 3. リーマンゼータ（Euler積）
-- =========================================================

noncomputable def RiemannZeta (s : ℂ) : ℂ :=
  ∏' p : ℕ,
    if prime p then (1 - p^(-s))⁻¹ else 1

-- =========================================================
-- ■ 4. 「幾何の代替」が必要
-- =========================================================

/-
Selbergでは：
  空間 X = Γ\ℍ が存在

Riemannでは：
  対応する空間が未確定
-/

axiom ArithmeticSpace : Type

axiom measure : Measure ArithmeticSpace

def H := Lp ℂ 2 measure

-- =========================================================
-- ■ 5. 作用素（これが未構成）
-- =========================================================

/-
欲しいもの：

自己共役作用素 L で
  spectrum(L) = {γ_n}
-/

axiom L : H → H

axiom self_adjoint :
  ∀ f g, inner (L f) g = inner f (L g)

-- =========================================================
-- ■ 6. トレース公式（最重要）
-- =========================================================

/-
Selberg:
  spectrum = geodesic sum

Riemannで欲しい形：
-/

axiom trace_formula_R :
  ∀ h,
    (∑ n, h (γ n))
    =
    (integral h)
    +
    (∑ p, log p * h (log p))

-- γ_n = ζ零点の虚部
axiom γ : ℕ → ℝ

-- =========================================================
-- ■ 7. 核心仮定（Hilbert–Pólya）
-- =========================================================

axiom HP_operator :
  spectrum L = {x | ∃ n, x = γ n}

-- =========================================================
-- ■ 8. RH（帰結）
-- =========================================================

theorem RH_from_lifting :
  HP_operator →
  ∀ n,
    Complex.re (1/2 + Complex.I * γ n) = 1/2 :=
by
  intro h n
  simp

-- =========================================================
-- ■ 9. どこで詰まっているか
-- =========================================================

/-
未解決ポイント：

(1) ArithmeticSpace の具体構成
(2) L の明示定義
(3) trace_formula_R の証明
(4) spectrum = ζ零点 の一致

Selbergでは全部成立
Riemannでは全部未成立
-/

-- =========================================================
-- ■ 10. 本質
-- =========================================================

/-
RH ≡ “Selberg構造を数論空間に移植できるか”
-/
/-!
# Selberg Zeta Function → Spectrum Correspondence

This is the cleanest known analogue of the Riemann zeta structure.

Key facts:
- Defined from closed geodesics (prime analogue)
- Has Euler product
- Zeros correspond to Laplacian eigenvalues

This is mathematically established (Selberg theory),
unlike the Riemann case.
-/

noncomputable section
open Classical Real Complex

-- =========================================================
-- ■ 1. 幾何：閉測地線（素数の類似）
-- =========================================================

axiom geodesic : Type

-- primitive closed geodesics（素数に対応）
axiom primitive : geodesic → Prop

-- 長さ
axiom length : geodesic → ℝ

-- =========================================================
-- ■ 2. Selbergゼータ関数（定義）
-- =========================================================

/-
Z(s) = ∏_{γ primitive} ∏_{k=0}^∞ (1 - exp(-(s+k)ℓ(γ)))

完全に素数積のアナロジー
-/

noncomputable def SelbergZeta (s : ℂ) : ℂ :=
  ∏' γ : geodesic,
    if primitive γ then
      ∏' k : ℕ,
        (1 - Complex.exp (-(s + k) * length γ))
    else 1

-- =========================================================
-- ■ 3. 対数微分（trace公式の形）
-- =========================================================

/-
Z'(s)/Z(s) = Σ_{γ} Σ_{m≥1} ℓ(γ) e^{-m s ℓ(γ)}

→ 素数和の完全対応
-/

axiom log_derivative :
  ∀ s,
    deriv SelbergZeta s / SelbergZeta s
    =
    ∑ γ, ∑ m : ℕ,
      length γ * Complex.exp (-m * s * length γ)

-- =========================================================
-- ■ 4. スペクトル（ラプラシアン）
-- =========================================================

axiom eigenvalue : ℕ → ℝ

/-
λ_n = 1/4 + r_n^2
-/

def spectral_param (n : ℕ) : ℝ :=
  Real.sqrt (eigenvalue n - 1/4)

-- =========================================================
-- ■ 5. 零点との完全対応（Selbergの定理）
-- =========================================================

/-
Selbergの結果：

Z(s) = 0 ⇔ s = 1/2 ± i r_n
-/

axiom selberg_zero_correspondence :
  ∀ n,
    SelbergZeta (1/2 + Complex.I * spectral_param n) = 0

-- =========================================================
-- ■ 6. スペクトル対称性
-- =========================================================

/-
自動的に臨界線 Re(s)=1/2 上に乗る
-/

lemma critical_line_selberg :
  ∀ n,
    Complex.re (1/2 + Complex.I * spectral_param n) = 1/2 :=
by
  intro n
  simp

-- =========================================================
-- ■ 7. トレース公式（スペクトル＝幾何）
-- =========================================================

/-
Selberg trace formula:

Σ h(r_n)
=
幾何側（閉測地線和）
-/

axiom trace_formula :
  ∀ h,
    (∑ n, h (spectral_param n))
    =
    (integral h)
    +
    (∑ γ, length γ * h (length γ))

-- =========================================================
-- ■ 8. リーマンゼータとの比較
-- =========================================================

/-
Riemann ζ:

ζ(s) = ∏ (1 - p^{-s})^{-1}

Selberg Z:

Z(s) = ∏ (1 - e^{-sℓ(γ)})

完全な構造対応：
  prime p ↔ geodesic γ
  log p ↔ length γ
-/

axiom prime : ℕ → Prop

def analogy_map : geodesic → ℕ := fun γ => 2 -- placeholder

-- =========================================================
-- ■ 9. 決定的な違い
-- =========================================================

/-
Selberg:
  ✔ 零点 = スペクトル（証明済）

Riemann:
  ✘ 零点 = スペクトル（未証明）

ここがRHそのもの
-/

axiom riemann_zero_imag : ℕ → ℝ

def RH_goal : Prop :=
  ∃ L,
    spectrum L = {x | ∃ n, x = riemann_zero_imag n}

-- =========================================================
-- ■ まとめ
-- =========================================================

/-
Selberg world:
  完全成功モデル

Riemann world:
  同じ構造を持つはずだが未証明

Therefore:

RH = “Selberg現象を数論側で実現できるか”
-/
