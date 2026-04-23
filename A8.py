import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt

# =========================================================
# ■ 前提：x, dx, Lap, k はそのまま使う
# =========================================================

# --- ベースポテンシャル（骨格）
V_base = 0.8 * np.log(1 + x**2) + 0.05 * x**2

# --- 素数ポテンシャル（まとめて）
osc = np.zeros_like(x)
for p in p_list:
    osc += np.cos(np.log(p) * x) / np.sqrt(p)

V_full = V_base + osc

# =========================================================
# ■ 固有値・固有関数
# =========================================================

H = Lap + diags(V_full, 0)
vals, vecs = eigsh(H, k=k, which='SM')

# ソート
idx = np.argsort(vals)
vals = vals[idx]
vecs = vecs[:, idx]

# 正規化
for i in range(k):
    vecs[:, i] /= np.sqrt(np.sum(vecs[:, i]**2) * dx)

# =========================================================
# ■ FFT解析
# =========================================================

freqs = np.fft.rfftfreq(len(x), d=dx)

# --- ポテンシャルの周波数
fft_V = np.abs(np.fft.rfft(V_full))

# --- ψ²の周波数（複数まとめて）
fft_psi2_sum = np.zeros_like(freqs)

for n in range(k):
    psi2 = vecs[:, n]**2
    fft_psi2 = np.abs(np.fft.rfft(psi2))
    fft_psi2_sum += fft_psi2

# 正規化
fft_V /= np.max(fft_V)
fft_psi2_sum /= np.max(fft_psi2_sum)

# =========================================================
# ■ 可視化
# =========================================================

plt.figure()
plt.plot(freqs, fft_V, label="V(x) spectrum")
plt.plot(freqs, fft_psi2_sum, label="sum ψ_n^2 spectrum")
plt.legend()
plt.title("Frequency alignment: V vs ψ^2")

# =========================================================
# ■ 相関（重要）
# =========================================================

corr = np.corrcoef(fft_V, fft_psi2_sum)[0,1]
print("frequency correlation:", corr)

plt.show()
