import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import mpmath as mp

# =========================================================
# ■ 1. ζ零点（虚部）
# =========================================================

mp.mp.dps = 30

def zeta_zeros(n):
    return np.array([float(mp.zetazero(k).imag) for k in range(1, n+1)])

k = 8
zeros = zeta_zeros(k)

# 正規化（スケール安定）
target_lambda = zeros - zeros[0]
target_lambda = target_lambda / np.mean(np.diff(target_lambda))

# =========================================================
# ■ 2. 空間
# =========================================================

N = 200
L = 15.0
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

def basis(x, K=12):
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
# ■ 6. loss（数論対応版）
# =========================================================

def loss(p):
    vals = compute_eigs(p)

    if not np.all(np.isfinite(vals)):
        return 1e6

    # --- gap
    gap_v = np.diff(vals)
    gap_t = np.diff(target_lambda)
    err_gap = np.sum((gap_v - gap_t)**2)

    # --- anchor
    err_anchor = (vals[0] - target_lambda[0])**2

    # --- slope
    slope_v = (vals[-1] - vals[0]) / (k - 1)
    slope_t = (target_lambda[-1] - target_lambda[0]) / (k - 1)
    err_slope = (slope_v - slope_t)**2

    # --- scale
    scale_v = vals[-1] - vals[0]
    scale_t = target_lambda[-1] - target_lambda[0]
    err_scale = (scale_v - scale_t)**2

    # --- 統計（GUE的）
    gap_vn = gap_v / (np.mean(gap_v) + 1e-8)
    gap_tn = gap_t / (np.mean(gap_t) + 1e-8)
    err_stat = np.mean((np.sort(gap_vn) - np.sort(gap_tn))**2)

    # --- 正則化
    c, alpha = unpack(p)
    V = potential(c, alpha)
    smooth = np.sum((np.diff(V, 2))**2)

    return (
        2.0 * err_gap +
        5.0 * err_anchor +
        8.0 * err_slope +
        6.0 * err_scale +
        1.0 * err_stat +
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
    options={'maxiter': 250}
)

p_opt = res.x

# =========================================================
# ■ 8. 結果
# =========================================================

vals = compute_eigs(p_opt)

print("zeta zeros (scaled):", target_lambda)
print("approx spectrum:", vals)
print("error:", np.linalg.norm(vals - target_lambda))

# =========================================================
# ■ 9. ポテンシャル
# =========================================================

c_opt, alpha_opt = unpack(p_opt)
V_opt = potential(c_opt, alpha_opt)

plt.figure()
plt.plot(x, V_opt)
plt.title("Recovered Potential (zeta-based)")
plt.grid()

# =========================================================
# ■ 10. 周波数解析（ここが数論ポイント）
# =========================================================

fft_V = np.abs(np.fft.rfft(V_opt))
freqs = np.fft.rfftfreq(len(V_opt), d=dx)

plt.figure()
plt.plot(freqs, fft_V)
plt.title("Potential Spectrum (FFT)")

# =========================================================
# ■ 11. 素数ログとの比較
# =========================================================

# 素数列
def primes(n):
    sieve = np.ones(n+1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(np.sqrt(n))+1):
        if sieve[i]:
            sieve[i*i:n+1:i] = False
    return np.where(sieve)[0]

p = primes(200)
logp = np.log(p)

plt.figure()
plt.hist(logp, bins=30)
plt.title("log primes distribution")

plt.show()
