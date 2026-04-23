import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
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

target = zeros - zeros[0]
target = target / np.mean(np.diff(target))

# =========================================================
# ■ 2. 素数
# =========================================================

def primes(n):
    sieve = np.ones(n+1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(np.sqrt(n))+1):
        if sieve[i]:
            sieve[i*i:n+1:i] = False
    return np.where(sieve)[0]

p_list = primes(500)
logp = np.log(p_list)

# =========================================================
# ■ 3. 空間
# =========================================================

N = 300
L = 6.0
x = np.linspace(-L, L, N)
dx = x[1] - x[0]

Lap = diags(
    [np.ones(N-1), -2*np.ones(N), np.ones(N-1)],
    [-1, 0, 1]
) / dx**2
Lap = -Lap

# =========================================================
# ■ 4. ポテンシャル（最小構成）
# =========================================================

def potential(beta):

    # --- 成長（固定）
    smooth = 0.8 * np.log(1 + x**2) + 0.05 * x**2

    # --- 素数振動のみ
    osc = np.zeros_like(x)
    for lp in logp:
        osc += np.cos(lp * x) / np.sqrt(np.exp(lp))

    return smooth + beta * osc

# =========================================================
# ■ 5. 固有値
# =========================================================

def spectrum(beta):
    V = potential(beta)
    H = Lap + diags(V, 0)

    vals = eigsh(H, k=k, which='SM', return_eigenvectors=False)
    vals = np.sort(vals)

    return vals - vals[0]

# =========================================================
# ■ 6. βスキャン
# =========================================================

betas = np.linspace(0.0, 2.0, 40)
errors = []

for b in betas:
    vals = spectrum(b)
    err = np.linalg.norm(vals - target)
    errors.append(err)

best_idx = np.argmin(errors)
beta_best = betas[best_idx]

print("best beta:", beta_best)
print("best error:", errors[best_idx])

# =========================================================
# ■ 7. 最良結果
# =========================================================

vals = spectrum(beta_best)

print("target:", target)
print("approx:", vals)

# =========================================================
# ■ 8. 可視化
# =========================================================

plt.figure()
plt.plot(betas, errors)
plt.title("Error vs beta")
plt.grid()

plt.figure()
plt.plot(target, 'o-', label="target")
plt.plot(vals, 'x-', label="approx")
plt.legend()
plt.title("Spectrum (no optimization)")

plt.figure()
plt.plot(x, potential(beta_best))
plt.title("Potential (prime only)")

plt.show()
