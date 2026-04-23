import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt

# =========================================================
# ■ 1. パラメータ
# =========================================================

k = 8
N = 300
L = 6.0

x = np.linspace(-L, L, N)
dx = x[1] - x[0]

# =========================================================
# ■ 2. ラプラシアン
# =========================================================

Lap = diags(
    [np.ones(N-1), -2*np.ones(N), np.ones(N-1)],
    [-1, 0, 1]
) / dx**2
Lap = -Lap

# =========================================================
# ■ 3. 素数生成
# =========================================================

def primes(n):
    sieve = np.ones(n+1, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(np.sqrt(n))+1):
        if sieve[i]:
            sieve[i*i:n+1:i] = False
    return np.where(sieve)[0]

p_list = primes(300)

# =========================================================
# ■ 4. ポテンシャル構築
# =========================================================

# 骨格
V_base = 0.8 * np.log(1 + x**2) + 0.05 * x**2

# 素数振動（まとめて）
osc = np.zeros_like(x)
for p in p_list:
    osc += np.cos(np.log(p) * x) / np.sqrt(p)

V_full = V_base + osc

# =========================================================
# ■ 5. 固有関数取得
# =========================================================

def compute_psi(V):
    H = Lap + diags(V, 0)
    vals, vecs = eigsh(H, k=k, which='SM')

    idx = np.argsort(vals)
    vals = vals[idx]
    vecs = vecs[:, idx]

    # 正規化
    for i in range(k):
        vecs[:, i] /= np.sqrt(np.sum(vecs[:, i]**2) * dx)

    return vals, vecs

vals, vecs = compute_psi(V_full)

# =========================================================
# ■ 6. ψ²スペクトル
# =========================================================

def psi2_spectrum(vecs):
    freqs = np.fft.rfftfreq(len(x), d=dx)
    acc = np.zeros_like(freqs)

    for n in range(k):
        psi2 = vecs[:, n]**2
        fft = np.abs(np.fft.rfft(psi2))
        acc += fft

    acc /= np.max(acc)
    return freqs, acc

freqs, spec_base = psi2_spectrum(vecs)

# =========================================================
# ■ 7. Vを壊す
# =========================================================

noise_strength = 0.2  # ←ここ調整可能
noise = noise_strength * np.random.randn(len(x))

V_pert = V_full + noise

vals2, vecs2 = compute_psi(V_pert)
_, spec_pert = psi2_spectrum(vecs2)

# =========================================================
# ■ 8. 相関
# =========================================================

corr = np.corrcoef(spec_base, spec_pert)[0,1]
print("ψ² stability correlation:", corr)

# =========================================================
# ■ 9. 可視化
# =========================================================

plt.figure()
plt.plot(freqs, spec_base, label="original ψ² spectrum")
plt.plot(freqs, spec_pert, '--', label="perturbed ψ² spectrum")
plt.legend()
plt.title("Stability test of ψ² frequency structure")

plt.show()
