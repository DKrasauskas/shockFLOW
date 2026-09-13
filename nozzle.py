import numpy as np
from scipy.spatial import cKDTree
from matplotlib.path import Path
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# Packing functions, DO NOT MODIFY. 29 bits are reserved for boundary cells
# meaning maximum boundary cell count => 536 million. Currently, for single GPU use only, this will never be exceeded.
# ---------------------------------------------------------------

def pack_uint16_to_uint32(high_16, low_16) -> int:
    # Shift the high 16 bits to the left, then OR with the low 16 bits
    return (high_16 << 29) | low_16


def unpack_uint32_to_uint16(packed_32):
    high_16 = (packed_32 >> 29) & 1
    low_16 = packed_32 & 0xFFFFFF
    return high_16, low_16


# ---------------------------------------------------------------
# Shared binary export helper
#   Layout of the grid .bin file:
#     int32  Ni
#     int32  Nj
#     int32  norm
#     uint32 array[Ni*Nj]   (row-major, i.e. array[i, j] in C order)
#   Layout of the normals .bin file:
#     float32 nx0, ny0, nx1, ny1, ...
# ---------------------------------------------------------------
def _write_grid_bin(path, Ni, Nj, norm, array):
    with open(path, "wb") as f:
        np.array([Ni, Nj, norm], dtype=np.int32).tofile(f)
        array.astype(np.uint32).tofile(f)


def _write_normals_bin(path, normal):
    if len(normal) > 0:
        np.array(normal, dtype=np.float32).tofile(path)
    else:
        # still create an (empty) file so downstream tooling doesn't choke
        open(path, "wb").close()


def create_nozzle_bc(Ni, Nj, destination, norm = 1):
    """
    Builds a boundary image for shockFLOW solver.

    Args:
        Ni: x grid length in voxels
        Nj: y grid length in voxels
        destination: directory path for output.
    """
    array = np.zeros((Ni, Nj), dtype=np.uint32)

    j0 = Nj // 2                # centerline (nozzle axis) row index in j

    # Hollow double-wall structure, measured outward from the bore surface r(x):
    #   [0, b1)  -> inner wall  (solid, thickness d_wall1)
    #   [b1, b2) -> hollow gap  (cavity, thickness d_gap)
    #   [b2, b3) -> outer wall  (solid, thickness d_wall2)
    #   >= b3    -> outside
    d_wall1 = 10
    d_gap = 0
    d_wall2 = 10

    b1 = d_wall1
    b2 = d_wall1 + d_gap
    b3 = d_wall1 + d_gap + d_wall2   # also used as the front-cap thickness

    # ---------------------------------------------------------------
    # The nozzle no longer spans the full texture: leave empty padding at
    # both ends, and seal the combustion-chamber (inlet) end with a solid
    # cap so the bore isn't open to the edge of the texture. The exit end
    # stays open (no cap) so exhaust can leave the nozzle, but the hollow
    # cavity between the inner and outer wall must be sealed off there --
    # otherwise the two walls are structurally disconnected and the cavity
    # vents straight into the exhaust flow. EXIT_CAP_THICKNESS controls how
    # many axial layers near i_end are used to fuse inner + outer wall into
    # a solid rim (this only closes the cavity band; the bore itself stays
    # open).
    # ---------------------------------------------------------------
    margin = 100                    # empty padding at each end of the texture
    i_cap_start = margin            # front cap begins here
    i_cap_end = margin + b3         # bore/contour geometry begins here
    EXIT_CAP_THICKNESS = d_wall1    # thickness of the rim that seals the exit gap

    # ---------------------------------------------------------------
    # Nozzle contour: r(x) = bore radius at axial position x, x measured
    # from i_cap_end (so x=0 is the back face of the sealing cap).
    # Three tunable sections, each with its own length:
    #   [0, x1)   -> combustion chamber (straight, rectangular, r = R_in)
    #   [x1, x2)  -> converging section, quadratic taper R_in -> R_t
    #   [x2, x3]  -> diverging / exit section, bell taper R_t -> R_e
    # ---------------------------------------------------------------
    R_in = 300.0 * norm * 0.25       # inlet radius (unchanged) -> 150
    R_t  = 60.0  * norm  * 0.25      # throat radius (unchanged) -> 30
    R_e  = 180.0 * norm  * 0.25      # exit radius (unchanged) -> 100

    chamber_length    = 100.0 * norm * 0.25    # unchanged -> 50
    converging_length = 380.0 * norm * 0.25    # 260 -> 380: eases the converging angle
    exit_length       = 800.0 * norm * 0.25    # unchanged -> 400

    x1 = chamber_length
    x2 = x1 + converging_length
    x3 = x2 + exit_length
    L = x3                          # total nozzle contour length

    i_end = i_cap_end + int(round(L))   # exit plane (left open, no cap)
    assert i_end <= Ni - margin, (
        "nozzle geometry doesn't fit in the texture -- increase Ni, or shrink "
        "margin / chamber_length / converging_length / exit_length"
    )
    assert EXIT_CAP_THICKNESS < (i_end - i_cap_end), (
        "EXIT_CAP_THICKNESS is too large for the nozzle contour length"
    )


    def r_of_x(x):
        if x <= x1:
            return R_in
        elif x <= x2:
            t = (x - x1) / converging_length
            return R_t + (R_in - R_t) * (1 - t) ** 2
        else:
            t = (x - x2) / exit_length
            return R_t + (R_e - R_t) * t ** 1.5


    def rprime_of_x(x):
        if x <= x1:
            return 0.0
        elif x <= x2:
            t = (x - x1) / converging_length
            return -2.0 * (R_in - R_t) * (1 - t) / converging_length
        else:
            t = (x - x2) / exit_length
            return 1.5 * (R_e - R_t) * (t ** 0.5) / exit_length


    # ---------------------------------------------------------------
    # Fill grid. Everything defaults to 0 (outside / bore fluid / hollow
    # gap all read as 0) except the solid wall pixels, which get an index
    # + outward normal:
    #   i < i_cap_start or i > i_end        -> outside padding (0)
    #   i_cap_start <= i < i_cap_end        -> sealing cap (solid disk)
    #   i_cap_end <= i <= i_end:
    #       diff < 0             -> bore fluid            (0)
    #       0 <= diff < b1        -> inner wall            (indexed)
    #       b1 <= diff < b2       -> hollow cavity         (0, EXCEPT within
    #                                EXIT_CAP_THICKNESS of i_end, where it's
    #                                sealed to connect inner + outer wall)
    #       b2 <= diff < b3       -> outer wall            (indexed)
    #       diff >= b3            -> outside               (0)
    # ---------------------------------------------------------------
    normal = []
    index = 0

    r0 = r_of_x(0.0)
    cap_radius = r0 + b3   # cap covers the bore plus both wall layers at the front face

    for i in range(Ni):
        if i < i_cap_start or i > i_end:
            continue  # stays 0: empty padding beyond the nozzle

        if i < i_cap_end:
            # sealing cap: solid disk across the whole chamber cross-section,
            # normal points outward along -x, away from the combustion chamber
            for j in range(Nj):
                rad = abs(j - j0)
                if rad <= cap_radius:
                    array[i, j] = pack_uint16_to_uint32(1, index)
                    normal.append(np.array([-1.0, 0.0]))
                    index += 1
            continue

        x = i - i_cap_end
        rw = r_of_x(x)
        rp = rprime_of_x(x)

        # Are we inside the exit rim region that seals the inner/outer walls
        # together? Only the cavity band gets treated differently here --
        # the bore stays open so exhaust can still exit.
        seal_exit_gap = i > (i_end - EXIT_CAP_THICKNESS)

        for j in range(Nj):
            rad = abs(j - j0)
            diff = rad - rw

            if diff < 0:
                array[i, j] = pack_uint16_to_uint32(2, index)  # bore fluid

            elif diff < b1 or (b2 <= diff < b3):
                array[i, j] = pack_uint16_to_uint32(1, index)
                sign = 1.0 if j >= j0 else -1.0
                if diff < b1:
                    # inner wall: normal points INTO the bore fluid
                    dir_x, dir_y = rp, -sign
                else:
                    # outer wall: normal points away from the body (unchanged)
                    dir_x, dir_y = -rp, sign
                length = np.sqrt(dir_x ** 2 + dir_y ** 2)
                dir_x /= length
                dir_y /= length
                normal.append(np.array([dir_x, dir_y]))
                index += 1
            elif diff < b2:
                if seal_exit_gap:
                    # fuse the cavity band into wall here so the inner and
                    # outer walls are structurally connected at the exit
                    array[i, j] = pack_uint16_to_uint32(1, index)
                    normal.append(np.array([1.0, 0.0]))  # rim faces outward, +x
                    index += 1
                else:
                    array[i, j] = 0#pack_uint16_to_uint32(1, 0xFFFF)  # hollow cavity
            else:
                array[i, j] = 0  # outside

    print(array.dtype)
    print("wall pixels:", len(normal))

    # ---------------------------------------------------------------
    # Decode for visualization: 1 = wall, 0 = everything else
    # ---------------------------------------------------------------
    high = (array >> 29) & 1
    target = np.where(high == 1, 1.0, 0.0)

    plt.imshow(target.T, origin="lower", aspect="auto")
    plt.title("Sealed, padded nozzle with chamber: wall (1) vs everything else (0)")
    plt.show()

    # ---------------------------------------------------------------
    # Export to binary for C++ ingestion
    # ---------------------------------------------------------------
    _write_grid_bin(destination + "nozzlez.bin", Ni, Nj, norm, array)
    _write_normals_bin(destination + "nozzlez_n.bin", normal)

def create_naca_bc(Ni, Nj, destination, naca_code="2412"):
    """
    Builds a boundary image for shockFLOW solver.

    Args:
        Ni: x grid length in voxels
        Nj: y grid length in voxels
        destination: directory path for output.
        naca_code (optional) : 4 digit naca code
    """
    array = np.empty((Ni, Nj), dtype=np.uint32)

    d = 5  # wall shell thickness (pixels)

    # ---------------------------------------------------------------
    # NACA 4-digit airfoil parameters
    # ---------------------------------------------------------------
    chord = 800.0            # chord length in pixels
    n_panel = 300             # points per surface (upper/lower) -> polygon resolution
    aoa_deg = 8.0             # angle of attack in degrees
    le_x, le_y = Ni / 2 - chord / 2, Nj / 2   # leading-edge position on the grid



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
    high = (array >> 29) & 1
    low = array & 0xFFFFFF
    target = np.where((high == 1) & (low == 0xFFFFFF), 0.5,
                      np.where(high == 1, 1.0, 0.0))

    plt.imshow(target.T, origin="lower", aspect="auto")
    plt.plot(airfoil_i, airfoil_j, "r-", linewidth=0.5)
    plt.title(f"NACA {naca_code} interior (0.5), wall shell (1), outside (0)")
    plt.show()

    # ---------------------------------------------------------------
    # Export to binary for C++ ingestion
    # ---------------------------------------------------------------
    _write_grid_bin(destination + "naca.bin", Ni, Nj, 1, array)
    _write_normals_bin(destination + "nacan.bin", normal)

def create_rectangle_bc(Ni, Nj, destination, hx = 100, hy = 100):
    """
    Builds a boundary image for shockFLOW solver.

    Args:
        Ni: x grid length in voxels
        Nj: y grid length in voxels
        destination: directory path for output.
    """
    array = np.empty((Ni, Nj), dtype=np.uint32)

    ci, cj = Ni // 2, Nj // 2   # rectangle center
    #hx, hy = 20.0, 20.0       # half-width, half-height
    d = 3                       # wall shell thickness (pixels)




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


    # ---------------------------------------------------------------
    # Decode for visualization: 0.5 = interior, 1 = wall, 0 = outside
    # ---------------------------------------------------------------
    high = (array >> 29) & 1
    low = array & 0xFFFFFF
    target = np.where((high == 1) & (low == 0xFFFFFF), 0.5,
                      np.where(high == 1, 1.0, 0.0))

    plt.imshow(target.T, origin="lower", aspect="auto")
    plt.title("Rectangle interior (0.5), wall shell (1), outside (0)")
    plt.show()

    # ---------------------------------------------------------------
    # Export to binary for C++ ingestion
    # ---------------------------------------------------------------
    _write_grid_bin(destination + "rect.bin", Ni, Nj, 1, array)
    _write_normals_bin(destination + "rectn.bin", normal)

def create_sphere_bc(Ni, Nj, destination, radius = 50):
    array = np.empty((Ni, Nj), dtype = np.uint32)

    R = radius
    d = 3


    normal = []
    index = 0
    for i in range(len(array)):
        for j in range(len(array[i])):
            dist = np.sqrt((i - Ni / 4) ** 2 + (j - Nj / 2) ** 2)
            dir_x = i - Ni / 4
            dir_y = j - Nj / 2

            if dist >= R and dist < R + 6:
                array[i, j] = pack_uint16_to_uint32(1, index)
                length = np.sqrt(dir_x **2 + dir_y ** 2)
                dir_x /= length
                dir_y /= length
                normal.append(np.array([dir_x, dir_y]))
                print(f"{dir_x} | {dir_y}")
                index += 1
            elif dist < R:
                array[i, j] =  pack_uint16_to_uint32(1, 0xFFFFFF)
            else:
                array[i, j] = 0


    high = (array >> 29) & 1
    low = array & 0xFFFFFF
    target = np.where((high == 1) & (low == 0xFFFFFF), 0.5,
                      np.where(high == 1, 1.0, 0.0))

    plt.imshow(target)
    plt.show()

    # ---------------------------------------------------------------
    # Export to binary for C++ ingestion
    # ---------------------------------------------------------------
    _write_grid_bin(destination + "sphere.bin", Ni, Nj, 1, array)
    _write_normals_bin(destination + "spheren.bin", normal)
    print("Saved 'spheren.bin'")
