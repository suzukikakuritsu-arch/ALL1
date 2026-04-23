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
# ■ ベースポテンシャル
# =========================================================

def V_base():
    return 0.8*np.log(1 + x**2) + 0.05*x**2

# =========================================================
# ■ モデル生成
# =========================================================

def V_model(mode):

    V = V_base()

    # --- 素数構造（通常）
    if mode in ["full", "no_phase", "random_freq", "random_phase"]:
        for p in p_list:
            V += np.cos(np.log(p)*x) / np.sqrt(p)

    # --- 位相破壊（正しく定義）
    if mode == "random_phase":

        Vp = np.zeros_like(x)

        for p in p_list:
            phase = np.random.uniform(0, 2*np.pi)
            Vp += np.cos(np.log(p)*x + phase) / np.sqrt(p)

        V += Vp

    # --- 周波数破壊
    if mode == "random_freq":
        V += np.cos(np.random.uniform(0,5)*x)

    # --- 素数なし
    if mode == "no_prime":
        pass

    # --- 骨格なし（重要）
    if mode == "no_base":
        V = np.zeros_like(x)
        for p in p_list:
            V += np.cos(np.log(p)*x) / np.sqrt(p)

    # --- 完全ランダム
    if mode == "random_all":
        V = np.random.randn(len(x))

    return V

# =========================================================
# ■ 固有値問題
# =========================================================

def solve(V):
    H = Lap + diags(V, 0)
    vals, vecs = eigsh(H, k=k, which='SM')

    idx = np.argsort(vals)
    vals = vals[idx]
    vecs = vecs[:, idx]

    for i in range(k):
        vecs[:, i] /= np.sqrt(np.sum(vecs[:, i]**2) * dx)

    return vals, vecs

# =========================================================
# ■ ψ²スペクトル
# =========================================================

def psi2_spectrum(vecs):

    acc = np.zeros(N//2 + 1)

    for i in range(k):
        acc += np.abs(np.fft.rfft(vecs[:, i]**2))

    return acc / np.max(acc)

# =========================================================
# ■ 実験モード
# =========================================================

modes = [
    "full",
    "no_prime",
    "random_freq",
    "random_phase",
    "no_base",
    "random_all"
]

# =========================================================
# ■ 基準
# =========================================================

V_ref = V_model("full")
_, vecs_ref = solve(V_ref)
ref_spec = psi2_spectrum(vecs_ref)

# =========================================================
# ■ 比較
# =========================================================

results = {}

for m in modes:

    V = V_model(m)
    _, vecs = solve(V)

    spec = psi2_spectrum(vecs)

    corr = np.corrcoef(ref_spec, spec)[0,1]
    results[m] = corr

    print(m, corr)

# =========================================================
# ■ 可視化
# =========================================================

plt.figure()
plt.bar(results.keys(), results.values())
plt.xticks(rotation=30)
plt.ylabel("ψ² spectral correlation vs full")
plt.title("Structural robustness map (clean version)")
plt.show()
