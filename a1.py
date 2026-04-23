import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt

# =========================================================
# ■ 基本設定
# =========================================================

N = 300
L = 6.0
k = 8

x = np.linspace(-L, L, N)
dx = x[1] - x[0]

Lap = diags(
    [np.ones(N-1), -2*np.ones(N), np.ones(N-1)],
    [-1, 0, 1]
) / dx**2
Lap = -Lap

# =========================================================
# ■ 素数
# =========================================================

def primes(n):
    sieve = np.ones(n+1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(np.sqrt(n))+1):
        if sieve[i]:
            sieve[i*i:n+1:i] = False
    return np.where(sieve)[0]

p_list = primes(250)

# =========================================================
# ■ 固有値計算
# =========================================================

def spectrum(V):
    H = Lap + diags(V, 0)
    vals = eigsh(H, k=k, which='SM', return_eigenvectors=False)
    return np.sort(vals - vals[0])

# =========================================================
# ■ ψ²スペクトル
# =========================================================

def psi2_spectrum(V):
    H = Lap + diags(V, 0)
    vals, vecs = eigsh(H, k=k, which='SM')

    idx = np.argsort(vals)
    vecs = vecs[:, idx]

    acc = np.zeros(N//2 + 1)

    for n in range(k):
        psi2 = vecs[:, n]**2
        fft = np.abs(np.fft.rfft(psi2))
        acc += fft

    return acc / np.max(acc)

# =========================================================
# ■ モデル生成
# =========================================================

def build(mode):

    V = 0.8*np.log(1 + x**2) + 0.05*x**2

    for p in p_list:

        # 周波数
        if mode == "log":
            f = np.log(p)
        elif mode == "sqrt":
            f = np.sqrt(p)
        elif mode == "linear":
            f = p * 0.01
        elif mode == "random_freq":
            f = np.random.uniform(0, 5)
        else:
            f = np.log(p)

        # 位相
        if mode == "sin":
            w = np.sin(f * x)
        elif mode == "random_phase":
            w = np.cos(f*x + np.random.uniform(0,2*np.pi))
        else:
            w = np.cos(f * x)

        # 重み
        if mode == "flat":
            a = 1.0
        elif mode == "1/p":
            a = 1/p
        else:
            a = 1/np.sqrt(p)

        V += a * w

    return V

# =========================================================
# ■ 実験群
# =========================================================

modes = [
    "log",
    "sqrt",
    "linear",
    "random_freq",
    "sin",
    "random_phase",
    "flat",
    "1/p"
]

# =========================================================
# ■ ベース
# =========================================================

V0 = build("log")
base_spec = psi2_spectrum(V0)

# =========================================================
# ■ 比較
# =========================================================

results = {}

for m in modes:

    V = build(m)
    spec = psi2_spectrum(V)

    corr = np.corrcoef(base_spec, spec)[0,1]
    results[m] = corr

    print(m, corr)

# =========================================================
# ■ 可視化
# =========================================================

plt.figure()
plt.bar(results.keys(), results.values())
plt.xticks(rotation=30)
plt.ylabel("correlation with log-model")
plt.title("Structural stability test")

plt.show()
