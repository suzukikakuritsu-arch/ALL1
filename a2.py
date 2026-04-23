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
# ■ ポテンシャル
# =========================================================

def V_model(include_primes=True):

    V = 0.8*np.log(1 + x**2) + 0.05*x**2

    if include_primes:
        for p in p_list:
            V += np.cos(np.log(p)*x) / np.sqrt(p)

    return V

# =========================================================
# ■ 固有系
# =========================================================

def solve(V):

    H = Lap + diags(V, 0)
    vals, vecs = eigsh(H, k=k, which='SM')

    idx = np.argsort(vals)
    vals = vals[idx]
    vecs = vecs[:, idx]

    for i in range(k):
        vecs[:, i] /= np.sqrt(np.sum(vecs[:, i]**2)*dx)

    return vals, vecs

# =========================================================
# ■ ψ²スペクトル
# =========================================================

def psi2_spec(vecs):

    acc = np.zeros(N//2 + 1)

    for i in range(k):
        acc += np.abs(np.fft.rfft(vecs[:, i]**2))

    return acc / np.max(acc)

# =========================================================
# ■ Vスペクトル
# =========================================================

def V_spec(V):
    return np.abs(np.fft.rfft(V)) / np.max(np.abs(np.fft.rfft(V)))

# =========================================================
# ■ 計算
# =========================================================

V_full = V_model(True)
V_base = V_model(False)

vals_f, vecs_f = solve(V_full)
vals_b, vecs_b = solve(V_base)

spec_Vf = V_spec(V_full)
spec_Vb = V_spec(V_base)

spec_psi_f = psi2_spec(vecs_f)
spec_psi_b = psi2_spec(vecs_b)

# =========================================================
# ■ 周波数軸
# =========================================================

freqs = np.fft.rfftfreq(N, d=dx)

# =========================================================
# ■ 相関行列（全体俯瞰）
# =========================================================

def corr(a, b):
    return np.corrcoef(a, b)[0,1]

C = np.array([
    [1.0,            corr(spec_Vf, spec_psi_f), corr(spec_Vf, spec_Vb)],
    [corr(spec_Vf, spec_psi_f), 1.0,            corr(spec_psi_f, spec_psi_b)],
    [corr(spec_Vf, spec_Vb),     corr(spec_psi_f, spec_psi_b), 1.0]
])

print("=== correlation matrix ===")
print(C)

# =========================================================
# ■ 可視化（俯瞰）
# =========================================================

plt.figure()
plt.plot(freqs, spec_Vf, label="V full")
plt.plot(freqs, spec_Vb, label="V base")
plt.legend()
plt.title("Potential spectra")

plt.figure()
plt.plot(freqs, spec_psi_f, label="ψ² full")
plt.plot(freqs, spec_psi_b, label="ψ² base")
plt.legend()
plt.title("Wavefunction spectra")

plt.show()
