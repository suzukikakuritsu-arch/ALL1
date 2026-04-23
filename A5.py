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

p_list = primes(300)
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
# ■ 4. スペクトル関数
# =========================================================

def get_spec(V):
    H = Lap + diags(V, 0)
    vals = eigsh(H, k=k, which='SM', return_eigenvectors=False)
    vals = np.sort(vals)
    return vals - vals[0]

# =========================================================
# ■ 5. 各ポテンシャル
# =========================================================

# (1) Lap only
V0 = np.zeros_like(x)

# (2) log only
V1 = 0.8 * np.log(1 + x**2)

# (3) log + quadratic
V2 = 0.8 * np.log(1 + x**2) + 0.05 * x**2

# (4) + prime oscillation
osc = np.zeros_like(x)
for lp in logp:
    osc += np.cos(lp * x) / np.sqrt(np.exp(lp))

V3 = V2 + 0.5 * osc

# =========================================================
# ■ 6. スペクトル
# =========================================================

S0 = get_spec(V0)
S1 = get_spec(V1)
S2 = get_spec(V2)
S3 = get_spec(V3)

# =========================================================
# ■ 7. 誤差
# =========================================================

def err(s):
    return np.linalg.norm(s - target)

print("Lap only:", err(S0))
print("log:", err(S1))
print("log + x^2:", err(S2))
print("+ primes:", err(S3))

# =========================================================
# ■ 8. 可視化
# =========================================================

plt.figure()
plt.plot(target, 'o-', label="target")

plt.plot(S0, '--', label="Lap")
plt.plot(S1, '--', label="log")
plt.plot(S2, '--', label="log+x^2")
plt.plot(S3, '--', label="+primes")

plt.legend()
plt.title("Contribution breakdown")

plt.figure()
plt.plot(x, V0, label="Lap")
plt.plot(x, V1, label="log")
plt.plot(x, V2, label="log+x^2")
plt.plot(x, V3, label="+primes")
plt.legend()
plt.title("Potentials")

plt.show()
