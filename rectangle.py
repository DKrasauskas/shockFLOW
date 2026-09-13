mport numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# Grid setup
# ---------------------------------------------------------------
Ni, Nj = 4000, 2000
array = np.empty((Ni, Nj), dtype=int)

ci, cj = Ni // 2, Nj // 2   # rectangle center
hx, hy = 20.0, 20.0       # half-width, half-height
d = 3                       # wall shell thickness (pixels)


def pack_uint16_to_uint32(high_16, low_16) -> int:
    # Shift the high 16 bits to the left, then OR with the low 16 bits
    return (high_16 << 29) | low_16


def unpack_uint32_to_uint16(packed_32):
    high_16 = (packed_32 >> 29) & 1
    low_16 = packed_32 & 0xFFFFFF
    return high_16, low_16


# ---------------------------------------------------------------
# Fill grid using a box signed-distance function:
#   qx = |dx| - hx , qy = |dy| - hy
#   sdf = |max(qx,0), max(qy,0)| + min(max(qx,qy), 0)
# sdf < 0  -> interior, 0 <= sdf < d -> wall shell, else -> outside
# ---------------------------------------------------------------
normal = []
index = 0
for i in range(Ni):
    dx = i - ci
    qx = abs(dx) - hx
    for j in range(Nj):
        dy = j - cj
        qy = abs(dy) - hy
        sdf = np.sqrt(max(qx, 0.0) ** 2 + max(qy, 0.0) ** 2) + min(max(qx, qy), 0.0)

        if sdf < 0:
            array[i, j] = pack_uint16_to_uint32(1, 0xFFFFFF)
        elif sdf < d:
            array[i, j] = pack_uint16_to_uint32(1, index)
            if qx > 0 and qy > 0:
                # corner region: normal points toward the corner
                dir_x, dir_y = np.sign(dx) * qx, np.sign(dy) * qy
            elif qx > qy:
                # left/right edge dominates
                dir_x, dir_y = float(np.sign(dx)), 0.0
            else:
                # top/bottom edge dominates
                dir_x, dir_y = 0.0, float(np.sign(dy))
            length = np.sqrt(dir_x ** 2 + dir_y ** 2)
            dir_x /= length
            dir_y /= length
            normal.append(np.array([dir_x, dir_y]))
            index += 1
        else:
            array[i, j] = 0

print(array.dtype)
print(array[399, 500])
print("wall pixels:", len(normal))

# ---------------------------------------------------------------
# Decode for visualization: 0.5 = interior, 1 = wall, 0 = outside
# ---------------------------------------------------------------
target = np.empty((Ni, Nj), dtype=float)
for i in range(Ni):
    for j in range(Nj):
        first, second = unpack_uint32_to_uint16(array[i, j])
        if first == 1 and second == 0xFFFFFF:
            target[i, j] = 0.5
            continue
        elif first == 1:
            target[i, j] = 1
            continue
        target[i, j] = 0

plt.imshow(target.T, origin="lower", aspect="auto")
plt.title("Rectangle interior (0.5), wall shell (1), outside (0)")
plt.show()

# ---------------------------------------------------------------
# Export to plain text for C++ ingestion
# ---------------------------------------------------------------
with open("/home/dominykas/CLionProjects/CELBM/Cases/rect1.txt", "w") as f:
    f.write(f"{Ni} {Nj} {1}\n")
    np.savetxt(f, array, fmt="%u", delimiter=" ")

with open("/home/dominykas/CLionProjects/CELBM/Cases/rect1n.txt", "w") as f:
    for nx, ny in normal:
        f.write(f"{nx} {ny}\n")
print("Saved 'normals1.txt'")

