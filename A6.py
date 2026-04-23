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

p_list = primes(200)
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
# ■ 4. ベースポテンシャル（骨格）
# =========================================================

V_base = 0.8 * np.log(1 + x**2) + 0.05 * x**2

def get_spec(V):
    H = Lap + diags(V, 0)
    vals = eigsh(H, k=k, which='SM', return_eigenvectors=False)
    vals = np.sort(vals)
    return vals

# ベース固有値
lambda_base = get_spec(V_base)

# =========================================================
# ■ 5. 素数ごとの感度
# =========================================================

eps = 0.01
shifts = []

for lp in logp:
    osc = np.cos(lp * x) / np.sqrt(np.exp(lp))
    V_pert = V_base + eps * osc

    lam = get_spec(V_pert)

    dlam = (lam - lambda_base) / eps  # 感度（線形近似）
    shifts.append(dlam)

shifts = np.array(shifts)   # shape: (num_primes, k)

# =========================================================
# ■ 6. 可視化①：ヒートマップ
# =========================================================

plt.figure(figsize=(8,5))
plt.imshow(shifts, aspect='auto', origin='lower')
plt.colorbar(label="dλ / dβ_p")
plt.xlabel("eigen index n")
plt.ylabel("prime index")
plt.title("Sensitivity: prime → eigenvalue")

# =========================================================
# ■ 7. 可視化②：特定固有値への寄与
# =========================================================

for n in range(k):
    plt.figure()
    plt.plot(p_list, shifts[:, n])
    plt.title(f"Contribution to eigenvalue {n}")
    plt.xlabel("prime p")
    plt.ylabel("sensitivity")

# =========================================================
# ■ 8. 可視化③：総寄与強度
# =========================================================

strength = np.linalg.norm(shifts, axis=1)

plt.figure()
plt.plot(p_list, strength)
plt.title("Total influence per prime")
plt.xlabel("prime p")

plt.show()
