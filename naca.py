import numpy as np
from scipy.spatial import cKDTree
from matplotlib.path import Path
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# Grid setup
# ---------------------------------------------------------------
Ni, Nj = 4000, 2000
array = np.empty((Ni, Nj), dtype=int)

d = 5  # wall shell thickness (pixels)

# ---------------------------------------------------------------
# NACA 4-digit airfoil parameters
# ---------------------------------------------------------------
naca_code = "2412"      # e.g. "0012" (symmetric) or "2412" (cambered)
chord = 800.0            # chord length in pixels
n_panel = 300             # points per surface (upper/lower) -> polygon resolution
aoa_deg = 8.0             # angle of attack in degrees
le_x, le_y = Ni / 2 - chord / 2, Nj / 2   # leading-edge position on the grid


def pack_uint16_to_uint32(high_16, low_16) -> int:
    # Shift the high 16 bits to the left, then OR with the low 16 bits
    return (high_16 << 29) | low_16


def unpack_uint32_to_uint16(packed_32):
    high_16 = (packed_32 >> 29) & 1
    low_16 = packed_32 & 0xFFFFFF
    return high_16, low_16


# ---------------------------------------------------------------
# NACA 4-digit geometry generator
# ---------------------------------------------------------------
def naca4_polygon(code, n=200, closed_te=True):
    """Return closed polygon (x, y) in chord-fraction units, 0<=x<=1,
    ordered TE -> upper surface -> LE -> lower surface -> TE."""
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:]) / 100.0

    # cosine spacing: denser points near leading/trailing edge
    beta = np.linspace(0.0, np.pi, n)
    x = (1.0 - np.cos(beta)) / 2.0

    yt = 5.0 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2
                    + 0.2843 * x ** 3 - 0.1015 * x ** 4)
    if closed_te:
        yt = yt - yt[-1] * x  # force a sharp, closed trailing edge

    if m > 0 and p > 0:
        yc = np.where(
            x < p,
            m / p ** 2 * (2 * p * x - x ** 2),
            m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x ** 2),
        )
        dyc = np.where(
            x < p,
            2 * m / p ** 2 * (p - x),
            2 * m / (1 - p) ** 2 * (p - x),
        )
    else:
        yc = np.zeros_like(x)
        dyc = np.zeros_like(x)

    slope = np.arctan(dyc)
    xu = x - yt * np.sin(slope)
    yu = yc + yt * np.cos(slope)
    xl = x + yt * np.sin(slope)
    yl = yc - yt * np.cos(slope)

    x_poly = np.concatenate([xu[::-1], xl[1:]])
    y_poly = np.concatenate([yu[::-1], yl[1:]])
    return x_poly, y_poly


x_naca, y_naca = naca4_polygon(naca_code, n=n_panel)

# scale to chord length, rotate for angle of attack, place on the grid
rad = np.deg2rad(aoa_deg)
x_s, y_s = x_naca * chord, y_naca * chord
x_rot = x_s * np.cos(rad) + y_s * np.sin(rad)
y_rot = -x_s * np.sin(rad) + y_s * np.cos(rad)

airfoil_i = x_rot + le_x
airfoil_j = y_rot + le_y
airfoil_points = np.column_stack([airfoil_i, airfoil_j])

airfoil_path = Path(airfoil_points)
airfoil_tree = cKDTree(airfoil_points)

# ---------------------------------------------------------------
# Per-vertex outward normals, from the local surface tangent
# (NOT from raw pixel-to-nearest-point direction, which is noisy
# whenever vertex spacing isn't much smaller than the wall shell d)
# ---------------------------------------------------------------
# the polygon is (near-)closed (TE start ~= TE end), so a periodic
# central difference gives a clean tangent all the way around,
# including across the trailing edge seam
tangent_x = np.roll(airfoil_i, -1) - np.roll(airfoil_i, 1)
tangent_y = np.roll(airfoil_j, -1) - np.roll(airfoil_j, 1)

# polygon is traced counter-clockwise (TE -> upper, right-to-left
# -> LE -> lower, left-to-right -> TE), so rotating the tangent by
# -90 degrees, i.e. (Ty, -Tx), gives the outward-pointing normal
vertex_normal_x = tangent_y
vertex_normal_y = -tangent_x
vn_len = np.hypot(vertex_normal_x, vertex_normal_y)
vn_len[vn_len < 1e-12] = 1.0
vertex_normal_x /= vn_len
vertex_normal_y /= vn_len

# ---------------------------------------------------------------
# Fill grid using distance-to-surface as the SDF proxy:
#   sdf < 0  -> interior, 0 <= sdf < d -> wall shell, else -> outside
# ---------------------------------------------------------------
ii, jj = np.meshgrid(np.arange(Ni), np.arange(Nj), indexing="ij")
grid_points = np.column_stack([ii.ravel(), jj.ravel()])

dist, nearest_idx = airfoil_tree.query(grid_points, k=1)
inside = airfoil_path.contains_points(grid_points)

sdf = np.where(inside, -dist, dist).reshape(Ni, Nj)
nearest_idx = nearest_idx.reshape(Ni, Nj)

interior_mask = sdf < 0
wall_mask = (sdf >= 0) & (sdf < d)

array[:] = 0
array[interior_mask] = pack_uint16_to_uint32(1, 0xFFFFFF)

normal = []
index = 0
wall_i, wall_j = np.nonzero(wall_mask)
for i, j in zip(wall_i, wall_j):
    array[i, j] = pack_uint16_to_uint32(1, index)
    k = nearest_idx[i, j]
    normal.append(np.array([vertex_normal_x[k], vertex_normal_y[k]]))
    index += 1

print(array.dtype)
print("wall pixels:", len(normal))

# ---------------------------------------------------------------
# Decode for visualization: 0.5 = interior, 1 = wall, 0 = outside
# ---------------------------------------------------------------
target = np.zeros((Ni, Nj), dtype=float)
for i in range(Ni):
    for j in range(Nj):
        first, second = unpack_uint32_to_uint16(array[i, j])
        if first == 1 and second == 0xFFFFFF:
            target[i, j] = 0.5
        elif first == 1:
            target[i, j] = 1.0

plt.imshow(target.T, origin="lower", aspect="auto")
plt.plot(airfoil_i, airfoil_j, "r-", linewidth=0.5)
plt.title(f"NACA {naca_code} interior (0.5), wall shell (1), outside (0)")
plt.show()

# ---------------------------------------------------------------
# Export to plain text for C++ ingestion
# ---------------------------------------------------------------
with open("/home/dominykas/CLionProjects/CELBM/Cases/naca1.txt", "w") as f:
    f.write(f"{Ni} {Nj} {1}\n")
    np.savetxt(f, array, fmt="%u", delimiter=" ")

with open("/home/dominykas/CLionProjects/CELBM/Cases/naca1n.txt", "w") as f:
    for nx, ny in normal:
        f.write(f"{nx} {ny}\n")
print("Saved normals to naca1n.txt")