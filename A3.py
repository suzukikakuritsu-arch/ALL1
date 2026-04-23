import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import mpmath as mp

# =========================================================
# ■ 1. ζ零点
# =========================================================

mp.mp.dps = 40

def zeta_zeros(n):
    return np.array([float(mp.zetazero(k).imag) for k in range(1, n+1)])

k = 8
zeros = zeta_zeros(k)

target_lambda = zeros - zeros[0]
target_lambda = target_lambda / np.mean(np.diff(target_lambda))

# =========================================================
# ■ 2. 素数生成
# =========================================================

def primes(n):
    sieve = np.ones(n+1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(np.sqrt(n))+1):
        if sieve[i]:
            sieve[i*i:n+1:i] = False
    return np.where(sieve)[0]

prime_list = primes(200)
logp = np.log(prime_list)

# =========================================================
# ■ 3. 空間
# =========================================================

N = 220
L = 6.0
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

Lap = diags(
    [np.ones(N-1), -2*np.ones(N), np.ones(N-1)],
    [-1, 0, 1]
) / dx**2
Lap = -Lap

# =========================================================
# ■ 4. 基底
# =========================================================

def basis(x, K=24):
    B = [np.ones_like(x)]
    for k_ in range(1, K):
        B.append(np.sin(k_ * np.pi * x / L))
        B.append(np.cos(k_ * np.pi * x / L))
    return np.vstack(B)

B = basis(x)
nb = B.shape[0]

# =========================================================
# ■ 5. パラメータ
# =========================================================

def unpack(p):
    c = p[:-2]
    alpha = p[-2]
    beta = p[-1]
    return c, alpha, beta

# =========================================================
# ■ 6. ポテンシャル（核心）
# =========================================================

def potential(c, alpha, beta):

    base = np.dot(c, B)

    # --- 滑らかな成長（ζ用）
    smooth_part = 0.8 * np.log(1 + x**2) + 0.05 * x**2

    # --- 素数振動（explicit formula 的）
    osc = np.zeros_like(x)
    for p in logp:
        osc += np.cos(p * x) / np.sqrt(np.exp(p))

    osc_part = beta * osc

    return alpha * base + smooth_part + osc_part

# =========================================================
# ■ 7. 固有値
# =========================================================

def compute_eigs(p):
    c, alpha, beta = unpack(p)

    V = potential(c, alpha, beta)
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
# ■ 8. loss
# =========================================================

def loss(p):
    vals = compute_eigs(p)

    if not np.all(np.isfinite(vals)):
        return 1e6

    gap_v = np.diff(vals)
    gap_t = np.diff(target_lambda)
    err_gap = np.sum((gap_v - gap_t)**2)

    err_anchor = (vals[0] - target_lambda[0])**2

    slope_v = (vals[-1] - vals[0]) / (k - 1)
    slope_t = (target_lambda[-1] - target_lambda[0]) / (k - 1)
    err_slope = (slope_v - slope_t)**2

    scale_v = vals[-1] - vals[0]
    scale_t = target_lambda[-1] - target_lambda[0]
    err_scale = (scale_v - scale_t)**2

    gap_vn = gap_v / (np.mean(gap_v) + 1e-8)
    gap_tn = gap_t / (np.mean(gap_t) + 1e-8)
    err_stat = np.mean((np.sort(gap_vn) - np.sort(gap_tn))**2)

    c, alpha, beta = unpack(p)
    V = potential(c, alpha, beta)
    smooth = np.sum((np.diff(V, 2))**2)

    return (
        2.0 * err_gap +
        5.0 * err_anchor +
        8.0 * err_slope +
        6.0 * err_scale +
        1.0 * err_stat +
        1e-6 * smooth
    )

# =========================================================
# ■ 9. 最適化
# =========================================================

p0 = np.concatenate([
    0.01 * np.random.randn(nb),
    np.array([1.0, 0.1])   # alpha, beta
])

res = minimize(
    loss,
    p0,
    method='L-BFGS-B',
    options={'maxiter': 300}
)

p_opt = res.x

# =========================================================
# ■ 10. 結果
# =========================================================

vals = compute_eigs(p_opt)

print("zeta zeros:", target_lambda)
print("approx:", vals)
print("error:", np.linalg.norm(vals - target_lambda))

# =========================================================
# ■ 11. 可視化
# =========================================================

c_opt, alpha_opt, beta_opt = unpack(p_opt)
V_opt = potential(c_opt, alpha_opt, beta_opt)

plt.figure()
plt.plot(x, V_opt)
plt.title(f"Potential (alpha={alpha_opt:.3f}, beta={beta_opt:.3f})")
plt.grid()

plt.figure()
plt.plot(target_lambda, 'o-', label="target")
plt.plot(vals, 'x-', label="approx")
plt.legend()
plt.title("Spectrum")

# =========================================================
# ■ 12. FFT
# =========================================================

fft_V = np.abs(np.fft.rfft(V_opt))
freqs = np.fft.rfftfreq(len(V_opt), d=dx)

plt.figure()
plt.plot(freqs, fft_V)
plt.title("FFT (prime structure)")

plt.show()
