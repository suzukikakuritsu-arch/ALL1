import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# =========================================================
# ■ 1. ターゲット
# =========================================================

def generate_gue(N):
    A = np.random.randn(N, N)
    return (A + A.T) / 2

np.random.seed(0)

M = 30
eigvals = np.linalg.eigvalsh(generate_gue(M))
eigvals = np.sort(eigvals)

eigvals = eigvals - eigvals.min()
eigvals = eigvals / eigvals.max()
eigvals = eigvals * 1.2

k = 6
target_lambda = eigvals[:k]

# =========================================================
# ■ 2. 空間
# =========================================================

N = 160
L = 12.0
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

Lap = diags(
    [np.ones(N-1), -2*np.ones(N), np.ones(N-1)],
    [-1, 0, 1]
) / dx**2
Lap = -Lap

# =========================================================
# ■ 3. 基底
# =========================================================

def basis(x, K=10):
    B = [np.ones_like(x)]
    for k_ in range(1, K):
        B.append(np.sin(k_ * np.pi * x / L))
        B.append(np.cos(k_ * np.pi * x / L))
    return np.vstack(B)

B = basis(x)
nb = B.shape[0]

# =========================================================
# ■ 4. パラメータ
# =========================================================

def unpack(p):
    return p[:-1], p[-1]

def potential(c, alpha):
    return alpha * np.dot(c, B)

# =========================================================
# ■ 5. 固有値
# =========================================================

def compute_eigs(p):
    c, alpha = unpack(p)

    V = potential(c, alpha)
    H = Lap + diags(V, 0)

    try:
        vals = eigsh(H, k=k, which='SM', return_eigenvectors=False)
    except:
        return np.ones(k) * 1e6

    vals = np.sort(np.asarray(vals).reshape(-1))

    if len(vals) < k:
        vals = np.pad(vals, (0, k - len(vals)), mode='edge')

    return vals[:k]

# =========================================================
# ■ 6. loss（最終調整）
# =========================================================

def loss(p):
    vals = compute_eigs(p)

    if not np.all(np.isfinite(vals)):
        return 1e6

    # -------------------------
    # gap
    # -------------------------
    gap_v = np.diff(vals)
    gap_t = np.diff(target_lambda)
    err_gap = np.sum((gap_v - gap_t)**2)

    # -------------------------
    # anchor
    # -------------------------
    err_anchor = (vals[0] - target_lambda[0])**2

    # -------------------------
    # slope
    # -------------------------
    slope_v = (vals[-1] - vals[0]) / (k - 1)
    slope_t = (target_lambda[-1] - target_lambda[0]) / (k - 1)
    err_slope = (slope_v - slope_t)**2

    # -------------------------
    # scale（直接）
    # -------------------------
    scale_v = (vals[-1] - vals[0])
    scale_t = (target_lambda[-1] - target_lambda[0])
    err_scale = (scale_v - scale_t)**2

    # -------------------------
    # FFT
    # -------------------------
    fft_v = np.abs(np.fft.rfft(vals))
    fft_t = np.abs(np.fft.rfft(target_lambda))

    fft_v /= np.sum(fft_v) + 1e-8
    fft_t /= np.sum(fft_t) + 1e-8

    err_fft = np.sum((fft_v - fft_t)**2)

    # -------------------------
    # 正則化（最小）
    # -------------------------
    c, alpha = unpack(p)
    V = potential(c, alpha)

    smooth = np.sum((np.diff(V, 2))**2)

    return (
        2.0 * err_gap +
        5.0 * err_anchor +
        8.0 * err_slope +   # ★強化
        6.0 * err_scale +   # ★最重要
        1.0 * err_fft +
        2e-5 * smooth
    )

# =========================================================
# ■ 7. 最適化
# =========================================================

p0 = np.concatenate([
    0.01 * np.random.randn(nb),
    np.array([1.0])
])

res = minimize(
    loss,
    p0,
    method='L-BFGS-B',
    options={'maxiter': 200}
)

p_opt = res.x

# =========================================================
# ■ 8. 結果
# =========================================================

vals = compute_eigs(p_opt)

print("target:", target_lambda)
print("approx:", vals)
print("error:", np.linalg.norm(vals - target_lambda))

# =========================================================
# ■ 9. 可視化
# =========================================================

c_opt, alpha_opt = unpack(p_opt)
V_opt = potential(c_opt, alpha_opt)

plt.figure()
plt.plot(x, V_opt)
plt.title(f"Potential (alpha={alpha_opt:.3f})")
plt.grid()

plt.figure()
plt.plot(target_lambda, 'o-', label="target")
plt.plot(vals, 'x-', label="approx")
plt.legend()
plt.title("Final Spectrum Match")

plt.show()
target: [0.         0.0585243  0.09139321 0.15145093 0.18664156 0.22852727]
approx: [2.80636342e-06 5.85227610e-02 9.13842323e-02 1.51444878e-01
 1.86643506e-01 2.28530865e-01]
error: 1.2004973591394378e-05
