import re

def _find_nested_block(content: str, path: list[str]):
    """
    Locates a nested YAML block by following `path` (e.g. ["runtime", "logging"]),
    assuming standard 2-space-per-level indentation.

    Returns (start, end, block_text) where start/end are absolute offsets into
    `content` covering the whole block (key line + everything indented under it).

    This generalizes the "before" section-scanning trick from the original
    set_logging_folder: instead of scanning backwards to check which top-level
    section a match belongs to, it narrows the search space one level at a time,
    so it naturally supports arbitrary nesting depth.
    """
    offset = 0
    search_space = content
    start_abs = end_abs = 0

    for depth, key in enumerate(path):
        indent = "  " * depth
        child_indent = "  " * (depth + 1)
        # Continuation lines are either properly-indented content, or blank
        # (blank/whitespace-only lines are common between YAML subsections
        # and shouldn't terminate the block).
        pattern = rf"(^{indent}{re.escape(key)}\s*:\s*$(?:\n(?:{child_indent}.*|[ \t]*))*)"

        m = re.search(pattern, search_space, re.MULTILINE)
        if not m:
            raise ValueError(f"Could not find '{'.'.join(path[:depth + 1])}' block.")

        start_abs = offset + m.start(1)
        end_abs = offset + m.end(1)
        search_space = m.group(1)
        offset = start_abs

    return start_abs, end_abs, search_space


def set_precision(config_path: str, precision: str):
    """
    Updates runtime.precision.DRAM, register, and compute.

    set_precision(path, "double") -> DRAM: double4_32a, register: double, compute: double
    set_precision(path, "float")  -> DRAM: float4,      register: float,  compute: float
    """
    precision = precision.lower()

    values_by_precision = {
        "double": {"DRAM": "double4_32a", "register": "double", "compute": "double"},
        "float": {"DRAM": "float4", "register": "float", "compute": "float"},
    }

    if precision not in values_by_precision:
        raise ValueError(
            f"Unsupported precision '{precision}'. Expected one of: {list(values_by_precision)}"
        )

    values = values_by_precision[precision]

    with open(config_path, "r") as f:
        content = f.read()

    start, end, block = _find_nested_block(content, ["runtime", "precision"])

    for field, value in values.items():
        block, n = re.subn(
            rf"(^    {field}\s*:\s*).*$",
            rf"\g<1>{value}",
            block,
            count=1,
            flags=re.MULTILINE,
        )
        if n != 1:
            raise ValueError(f"Could not find runtime.precision.{field}.")

    new_content = content[:start] + block + content[end:]

    with open(config_path, "w") as f:
        f.write(new_content)

    print(f"Updated precision to {precision}")


def set_video_resolution(config_path: str, x: int, y: int):
    """
    Updates x and y in every render_window block in the file, regardless of
    nesting (this config has both rendering.render_window and
    runtime.rendering.render_window).
    """
    with open(config_path, "r") as f:
        content = f.read()

    # \2 backreferences the captured indentation of the render_window line
    # itself, so this matches the block at whatever depth it's nested at.
    pattern = r"(^([ \t]*)render_window\s*:\s*$(?:\n^\2[ \t]+.*)*)"
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    if not matches:
        raise ValueError("Could not find any render_window blocks.")

    # Walk matches in reverse so earlier offsets stay valid as we splice.
    for match in reversed(matches):
        block = match.group(1)

        block, n1 = re.subn(
            r"(^\s*x\s*:\s*).*$", rf"\g<1>{x}", block, count=1, flags=re.MULTILINE
        )
        block, n2 = re.subn(
            r"(^\s*y\s*:\s*).*$", rf"\g<1>{y}", block, count=1, flags=re.MULTILINE
        )

        if n1 != 1 or n2 != 1:
            raise ValueError("Could not find x/y fields in a render_window block.")

        content = content[: match.start(1)] + block + content[match.end(1):]

    with open(config_path, "w") as f:
        f.write(content)

    print(f"Updated {len(matches)} render_window block(s) to {x}x{y}")


def select_renderer(config_path: str, renderer: str):
    """
    Updates runtime.rendering.renderer.

    select_renderer(path, "GLFW")
    select_renderer(path, "DIRECT")
    """
    valid_renderers = {"GLFW", "DIRECT"}
    if renderer not in valid_renderers:
        raise ValueError(f"Unsupported renderer '{renderer}'. Expected one of: {valid_renderers}")

    with open(config_path, "r") as f:
        content = f.read()

    start, end, block = _find_nested_block(content, ["runtime", "rendering"])

    block, n = re.subn(
        r"(^    renderer\s*:\s*).*$",
        rf"\g<1>{renderer}",
        block,
        count=1,
        flags=re.MULTILINE,
    )

    if n != 1:
        raise ValueError("Could not find runtime.rendering.renderer.")

    new_content = content[:start] + block + content[end:]

    with open(config_path, "w") as f:
        f.write(new_content)

    print(f"Updated renderer to {renderer}")

def set_ffmpeg_output_path(config_path: str, new_output_path: str):
    """
    Opens config_path as plain text, finds the ffmpeg command under
    encoding: args:, and replaces the trailing output path.
    """
    with open(config_path, 'r') as f:
        content = f.read()

    # Match a line like:  args: "ffmpeg ... -crf 18  /some/output/path"
    # Captures everything up to the last whitespace run, then the path itself.
    pattern = r'(args:\s*"ffmpeg.*?\s)(\S+)(")'

    match = re.search(pattern, content)
    if not match:
        raise ValueError("Could not find an active ffmpeg 'args' line to update.")

    new_content = content[:match.start(2)] + new_output_path + content[match.end(2):]

    with open(config_path, 'w') as f:
        f.write(new_content)

    print(f"Updated ffmpeg output path to: {new_output_path}")


def set_hdf5_output_path(config_path: str, output_path: str):
    """
    Sets the output.path value in the config file for hdf5 destination.
    """

    with open(config_path, "r") as f:
        content = f.read()

    pattern = r'(output:\s*\n\s*path\s*:\s*)(".*?"|\'.*?\'|[^\s#]+)'

    match = re.search(pattern, content)

    if not match:
        raise ValueError("Could not find output.path in config file.")

    new_content = (
            content[:match.start(2)]
            + f'"{output_path}"'
            + content[match.end(2):]
    )

    with open(config_path, "w") as f:
        f.write(new_content)

    print(f"Updated output path to: {output_path}")


def set_domain(config_path: str, mx: float, px: float):
    """
    Sets the physical domain extent (domain.mx and domain.px, in mm).
    Note: this file has two 'domain:' blocks (simulation.domain uses Nx/Ny/Nz,
    the other uses mx/px). This function specifically targets the mx/px block.
    """
    with open(config_path, 'r') as f:
        content = f.read()

    # Match the domain: block that contains mx/px (not the simulation Nx/Ny/Nz one)
    pattern = r'(domain:\s*\n\s*mx\s*:\s*)(-?[\d.eE+-]+)(.*\n\s*px\s*:\s*)(-?[\d.eE+-]+)'

    match = re.search(pattern, content)
    if not match:
        raise ValueError("Could not find the domain (mx/px) block to update.")

    new_content = (
            content[:match.start(2)] + str(mx) +
            content[match.end(2):match.start(4)] + str(px) +
            content[match.end(4):]
    )

    with open(config_path, 'w') as f:
        f.write(new_content)

    print(f"Updated domain to mx={mx}, px={px}")


def set_viscosity_and_vinf(config_path: str, viscosity: float, v_inf_x: float):
    """
    Sets physics.viscosity and v_inf_x in the config file.
    """
    with open(config_path, 'r') as f:
        content = f.read()

    visc_pattern = r'(viscosity\s*:\s*)([\d.eE+-]+)'
    vinf_pattern = r'(v_inf_x\s*:\s*)([\d.eE+-]+)'

    visc_match = re.search(visc_pattern, content)
    if not visc_match:
        raise ValueError("Could not find 'viscosity' field to update.")
    content = content[:visc_match.start(2)] + str(viscosity) + content[visc_match.end(2):]

    vinf_match = re.search(vinf_pattern, content)
    if not vinf_match:
        raise ValueError("Could not find 'v_inf_x' field to update.")
    content = content[:vinf_match.start(2)] + str(v_inf_x) + content[vinf_match.end(2):]

    with open(config_path, 'w') as f:
        f.write(content)

    print(f"Updated viscosity={viscosity}, v_inf_x={v_inf_x}")

def set_simulation_domain(config_path: str, Nx: int, Ny: int, Nz: int):
    """
    Sets Nx, Ny, and Nz under simulation.domain.

    Finds `domain:` as a (possibly non-first) child key of `simulation:`,
    based on indentation, not textual adjacency. Other `domain:` blocks
    elsewhere in the file are left untouched.
    """

    with open(config_path, "r") as f:
        lines = f.readlines()

    def indent_of(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def key_at(line: str):
        # returns the key name if this line is "key:" or "key: value", else None
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None
        m = re.match(r"([^\s:#][^:#]*):(?:\s|$)", stripped)
        return m.group(1).strip() if m else None

    # 1. find top-level `simulation:`
    sim_idx = None
    for i, line in enumerate(lines):
        if indent_of(line) == 0 and key_at(line) == "simulation":
            sim_idx = i
            break
    if sim_idx is None:
        raise ValueError("Could not find top-level 'simulation:' key.")

    # 2. find end of the simulation block (next line at indent 0, or EOF)
    sim_end = len(lines)
    for i in range(sim_idx + 1, len(lines)):
        if lines[i].strip() and indent_of(lines[i]) == 0:
            sim_end = i
            break

    # 3. within simulation block, find the indentation of its direct children
    child_indent = None
    for i in range(sim_idx + 1, sim_end):
        if lines[i].strip():
            child_indent = indent_of(lines[i])
            break
    if child_indent is None:
        raise ValueError("simulation: block has no children.")

    # 4. find `domain:` among direct children of simulation
    domain_idx = None
    for i in range(sim_idx + 1, sim_end):
        if not lines[i].strip():
            continue
        if indent_of(lines[i]) == child_indent and key_at(lines[i]) == "domain":
            domain_idx = i
            break
    if domain_idx is None:
        raise ValueError("Could not find 'domain:' under simulation.")

    # 5. find end of the domain block (next line at indent <= child_indent, or sim_end)
    domain_end = sim_end
    for i in range(domain_idx + 1, sim_end):
        if lines[i].strip() and indent_of(lines[i]) <= child_indent:
            domain_end = i
            break

    # 6. update Nx, Ny, Nz within domain block only
    counts = {"Nx": 0, "Ny": 0, "Nz": 0}
    for i in range(domain_idx + 1, domain_end):
        for name, val in (("Nx", Nx), ("Ny", Ny), ("Nz", Nz)):
            new_line, n = re.subn(
                rf"^(\s*{name}\s*:\s*)-?\d+(.*)$",
                rf"\g<1>{val}\2",
                lines[i],
            )
            if n:
                lines[i] = new_line
                counts[name] += n

    for name in ("Nx", "Ny", "Nz"):
        if counts[name] != 1:
            raise ValueError(f"Could not find exactly one '{name}' in simulation.domain "
                              f"(found {counts[name]}).")

    with open(config_path, "w") as f:
        f.writelines(lines)

    print(f"Updated simulation domain to Nx={Nx}, Ny={Ny}, Nz={Nz}")

import re


def set_logging_folder(config_path: str, logging_folder: str):
    """
    Updates runtime.logging.logging_folder, solver_log, and memory_log.
    """

    with open(config_path, "r") as f:
        content = f.read()

    if not logging_folder.endswith("/"):
        logging_folder += "/"

    # Locate the runtime.logging block directly.
    pattern = (
        r"(^  logging:\s*$"
        r"(?:\n^    .*)*)"
    )

    # Find all `logging:` blocks at indentation level 2 and check
    # that the one belongs to runtime.
    matches = list(re.finditer(pattern, content, re.MULTILINE))

    logging_match = None

    for match in matches:
        before = content[:match.start()]

        # The nearest top-level section before this logging block
        # must be `runtime:`.
        sections = re.findall(r"^(\S.*):\s*$", before, re.MULTILINE)

        if sections and sections[-1] == "runtime":
            logging_match = match
            break

    if logging_match is None:
        raise ValueError("Could not find runtime.logging block.")

    block = logging_match.group(1)

    block, n1 = re.subn(
        r'(^    logging_folder\s*:\s*).*$',
        rf'\g<1>"{logging_folder}"',
        block,
        count=1,
        flags=re.MULTILINE,
    )

    block, n2 = re.subn(
        r'(^    solver_log\s*:\s*).*$',
        rf'\g<1>"{logging_folder}solver_log.log"',
        block,
        count=1,
        flags=re.MULTILINE,
    )

    block, n3 = re.subn(
        r'(^    memory_log\s*:\s*).*$',
        rf'\g<1>"{logging_folder}memory_log.log"',
        block,
        count=1,
        flags=re.MULTILINE,
    )

    if n1 != 1:
        raise ValueError("Could not find runtime.logging.logging_folder.")

    if n2 != 1:
        raise ValueError("Could not find runtime.logging.solver_log.")

    if n3 != 1:
        raise ValueError("Could not find runtime.logging.memory_log.")

    new_content = (
            content[:logging_match.start(1)]
            + block
            + content[logging_match.end(1):]
    )

    with open(config_path, "w") as f:
        f.write(new_content)

    print(f"Updated logging folder to {logging_folder}")

def set_boundary_files(config_path: str, boundary_path: str, normals_path: str):
    """
    Sets the 'boundary' and 'normals' paths under the 'boundary_files' section
    in a YAML config file, preserving formatting/comments elsewhere.

    Works regardless of where 'boundary_files' appears in the file, but assumes
    it's a top-level key (i.e. not indented) with 'boundary' and 'normals'
    indented beneath it.
    """
    with open(config_path, 'r') as f:
        content = f.read()

    # Find the boundary_files block: from the "boundary_files:" line
    # up to (but not including) the next top-level (non-indented) key.
    block_pattern = r'^boundary_files\s*:\s*\n((?:[ \t]+.*\n?)*)'
    block_match = re.search(block_pattern, content, re.MULTILINE)
    if not block_match:
        raise ValueError("Could not find 'boundary_files' section in config.")

    block_start, block_end = block_match.start(1), block_match.end(1)
    block_content = block_match.group(1)

    def replace_field(block: str, field: str, new_path: str) -> str:
        # Matches: <indent>field : "anything"   (keeps indent, key spacing style)
        field_pattern = rf'([ \t]*{field}\s*:\s*)"[^"]*"'
        field_match = re.search(field_pattern, block)
        if not field_match:
            raise ValueError(f"Could not find '{field}' field inside 'boundary_files' section.")
        return block[:field_match.start()] + field_match.group(1) + f'"{new_path}"' + block[field_match.end():]

    new_block = replace_field(block_content, 'boundary', boundary_path)
    new_block = replace_field(new_block, 'normals', normals_path)

    new_content = content[:block_start] + new_block + content[block_end:]

    with open(config_path, 'w') as f:
        f.write(new_content)

    print(f"Set boundary -> {boundary_path}")
    print(f"Set normals  -> {normals_path}")
    
def set_debug_mode(config_path: str, enabled: bool):
    """
    Enables or disables DEBUG_MODE in settings.yaml.
    Writes TRUE or FALSE (matching the file's existing all-caps style).
    """
    with open(config_path, 'r') as f:
        content = f.read()

    pattern = r'(DEBUG_MODE\s*:\s*)(TRUE|FALSE|True|False|true|false)'

    match = re.search(pattern, content)
    if not match:
        raise ValueError("Could not find 'DEBUG_MODE' field to update.")

    new_value = "TRUE" if enabled else "FALSE"
    new_content = content[:match.start(2)] + new_value + content[match.end(2):]

    with open(config_path, 'w') as f:
        f.write(new_content)

    print(f"Set DEBUG_MODE to {new_value}")


def set_ext_event_times(config_path: str, new_time: float):
    """
    Sets both EXT event times to the same value:
      - events.EXT.time
      - capture_events.EXT.time
    Skips any commented-out 'time' lines (e.g. under #  event1: / #  event2:).
    """
    with open(config_path, 'r') as f:
        content = f.read()

    # Matches "EXT:" followed by (optionally other lines) "time : <number>",
    # only when the 'time' line isn't commented out.
    pattern = r'(EXT:\s*\n\s*time\s*:\s*)(-?[\d.eE+-]+)'

    matches = list(re.finditer(pattern, content))
    if not matches:
        raise ValueError("Could not find any 'EXT: time:' fields to update.")

    # Replace from last match to first, so earlier indices aren't invalidated
    for match in reversed(matches):
        content = content[:match.start(2)] + str(new_time) + content[match.end(2):]

    with open(config_path, 'w') as f:
        f.write(content)

    print(f"Updated {len(matches)} EXT event time(s) to {new_time}")

def set_wedge_dimensions(config_path: str, new_width: float = None, new_height: float = None):
    """
    Sets wedge dimensions in the config file:
      - wedge.width
      - wedge.height
    Only updates the values under the 'wedge:' section (not any other
    'width'/'height' keys elsewhere in the file).
    Pass None for a parameter to leave it unchanged.
    """
    with open(config_path, 'r') as f:
        content = f.read()

    # Isolate the wedge: block so we don't touch unrelated width/height keys
    wedge_block_pattern = r'(wedge:\s*\n(?:[ \t]+.*\n?)*)'
    block_match = re.search(wedge_block_pattern, content)
    if not block_match:
        raise ValueError("Could not find a 'wedge:' section in the config.")

    block = block_match.group(1)
    updated_block = block
    updated_fields = []

    if new_width is not None:
        width_pattern = r'(width\s*:\s*)(-?[\d.eE+-]+)'
        if not re.search(width_pattern, updated_block):
            raise ValueError("Could not find 'width' field under 'wedge:'.")
        updated_block = re.sub(width_pattern, lambda m: m.group(1) + str(new_width), updated_block, count=1)
        updated_fields.append(f"width={new_width}")

    if new_height is not None:
        height_pattern = r'(height\s*:\s*)(-?[\d.eE+-]+)'
        if not re.search(height_pattern, updated_block):
            raise ValueError("Could not find 'height' field under 'wedge:'.")
        updated_block = re.sub(height_pattern, lambda m: m.group(1) + str(new_height), updated_block, count=1)
        updated_fields.append(f"height={new_height}")

    if not updated_fields:
        print("No values provided; nothing updated.")
        return

    content = content[:block_match.start(1)] + updated_block + content[block_match.end(1):]

    with open(config_path, 'w') as f:
        f.write(content)

    print(f"Updated wedge section: {', '.join(updated_fields)}")

import h5py
import numpy as np

def hdf5_read_midline(path: str, axis: str = "x") -> dict[str, np.ndarray]:
    """
    Open a CFD HDF5 file written by exportAsHDF5 and extract all field
    values along the midpoint line.

    Parameters
    ----------
    path : str
        Path to the .h5 file.
    axis : str
        'x'  →  horizontal mid-line  (row  ny//2, all columns)
        'y'  →  vertical   mid-line  (column nx//2, all rows)

    Returns
    -------
    dict with keys:
        'coord'       – 1-D physical coordinate array (metres)
        'density'     – kg m⁻³  (or whatever your reference unit is)
        'vx'          – m s⁻¹
        'vy'          – m s⁻¹
        'temperature' – K
        'pressure'    – Pa  (raw, no conversion applied in C++)
        'Mach'        – dimensionless
    """
    fields = ("density", "vx", "vy", "temperature", "pressure", "density_gradient")

    with h5py.File(path, "r") as f:
        nx = int(f.attrs["nx"])
        ny = int(f.attrs["ny"])
        dx = float(f.attrs["dx"])
        dy = float(f.attrs["dy"])
        px = float(f.attrs["px"])
        mx = float(f.attrs["mx"])
        res = float(f.attrs["res"])
        rho = float(f.attrs["rho0"])
        p0 =   float(f.attrs["P0"])
        T0  = float(f.attrs["T0"])
        origin = int(f.attrs["origin"])
        rgas   = float(f.attrs["GasConstant"])

        if axis == "x":
            mid = ny // 2
            slicer = (mid, slice(None))
            coord = np.arange(nx) #* dx  # + float(f.attrs["origin_x"])
            coord = coord - origin * 1.0
            coord /= res
            print(res)
        elif axis == "y":
            mid = nx // 2
            slicer = (slice(None), mid)           # all rows, column mid
            coord = np.arange(ny) * dy + float(f.attrs["origin_y"])
        else:
            raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")

        result = {"coord": coord}
        result["res"] = res
        for name in fields:
            # datasets are stored (ny, nx) – float32
            result[name] = f[name][slicer].astype(np.float64)

        result["pressure"] = result["temperature"] * result["density"] * rgas / p0
        result["density"] /= rho
        result["temperature"] /= T0

    return result


import yaml

def set_field1_output(config_path, new_output_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    config['fields_to_rasterize']['field1']['output'] = new_output_path

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config