import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt

# =========================================================
# ■ 前提：既存の x, dx, logp, Lap を使う
# =========================================================

# --- ベースポテンシャル
V_base = 0.8 * np.log(1 + x**2) + 0.05 * x**2

# --- 固有値＆固有関数
H = Lap + diags(V_base, 0)

vals, vecs = eigsh(H, k=k, which='SM')
idx = np.argsort(vals)

vals = vals[idx]
vecs = vecs[:, idx]   # ψ_n

# 正規化（念のため）
for i in range(k):
    norm = np.sqrt(np.sum(vecs[:, i]**2) * dx)
    vecs[:, i] /= norm

# =========================================================
# ■ 理論感度
# =========================================================

def theoretical_shift(lp, n):
    psi = vecs[:, n]
    perturb = np.cos(lp * x) / np.sqrt(np.exp(lp))
    return np.sum(psi**2 * perturb) * dx

# =========================================================
# ■ 数値感度
# =========================================================

def numerical_shift(lp, n, eps=1e-3):
    perturb = np.cos(lp * x) / np.sqrt(np.exp(lp))

    Vp = V_base + eps * perturb
    H_p = Lap + diags(Vp, 0)

    vals_p = eigsh(H_p, k=k, which='SM', return_eigenvectors=False)
    vals_p = np.sort(vals_p)

    return (vals_p[n] - vals[n]) / eps

# =========================================================
# ■ 比較
# =========================================================

n_test = 4   # 見たい固有値

theory_vals = []
numeric_vals = []

for lp in logp[:50]:   # 小さい素数だけでOK
    t = theoretical_shift(lp, n_test)
    num = numerical_shift(lp, n_test)

    theory_vals.append(t)
    numeric_vals.append(num)

theory_vals = np.array(theory_vals)
numeric_vals = np.array(numeric_vals)

# =========================================================
# ■ 可視化
# =========================================================

plt.figure()
plt.plot(theory_vals, label="theory")
plt.plot(numeric_vals, '--', label="numeric")
plt.legend()
plt.title(f"Eigenvalue {n_test}: theory vs numeric")

plt.figure()
plt.scatter(theory_vals, numeric_vals)
plt.xlabel("theory")
plt.ylabel("numeric")
plt.title("Correlation check")

plt.show()

# 相関係数
corr = np.corrcoef(theory_vals, numeric_vals)[0,1]
print("correlation:", corr)
