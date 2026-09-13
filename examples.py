import shockFLOW.solver as flow
import shockFLOW.utils as helpers
import shockFLOW.nozzle  as nc
import os
import shutil



def run_wedge_example(dimx=1000, dimy=1000, screen_x = 1000, screen_y = 1000, viscosity = 0.0005188, v_inf_x = 1.0, simulation_end = 40, precision = "float", Debug =True, wedge_height = 100, wedge_width = 100, gradient_name = "density_grad", config=None, settings = None, working_dir = None):
    """
    Run a 2D supersonic wedge simulation and render the resulting flow field.

    This function configures and executes a shockFLOW simulation of a
    supersonic freestream (Mach 1.8) impinging on a wedge, using the
    bundled "config_wedge.yaml" / "settings_wedge.yaml" example configs.

    **VRAM REQUIREMENT**: Default dimensions (dimx=1000, dimy=1000)
    require **~500 MB of VRAM**.

    Freestream Conditions
    ----------------------
    - Temperature   : 300.0 K
    - Pressure      : 100000 Pa
    - Density       : 1.0 kg/m^3
    - Gas constant  : 287.058 J/(kg*K)
    - Gamma (cp/cv) : 1.4
    - Viscosity     : 1.886109e-4 Pa*s
    - Mach number   : 1.8

    Geometry
    --------
    - Wedge width  : 400 (grid units)
    - Wedge height : 400 (grid units)


    Parameters
    ----------
    dimx : int, optional
        Number of grid cells in the x-direction, used to set the simulation
        domain resolution. Default is 1000.
    dimy : int, optional
        Number of grid cells in the y-direction, used to set the simulation
        domain resolution. Default is 1000.

    Returns
    -------
    None

    """
    initial_path = os.getcwd()
    if working_dir ==None:
        path_run = initial_path
    else:
        path_run = working_dir
    os.chdir(path_run)

    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)

    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(module_dir)
    if config == None :
        config = "example_configs/config_wedge.yaml"
    else:
        config = os.path.join(path_run,  config)
    if settings == None:
        settings = "example_configs/settings_wedge.yaml"
    else:
        settings = os.path.join(path_run, settings)

    helpers.set_video_resolution(settings, screen_x, screen_y)
    helpers.set_video_resolution(config, screen_x, screen_y)
    helpers.set_precision(settings, precision)

    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_field1_output(config, gradient_name)
    helpers.set_wedge_dimensions(config, wedge_width, wedge_height)
    helpers.set_viscosity_and_vinf(config, viscosity=viscosity, v_inf_x=v_inf_x)


    helpers.set_debug_mode(settings, Debug)
    helpers.set_ffmpeg_output_path(settings, output_dir)
    flow.custom(settings, config, path_run)
    os.chdir(initial_path)

def run_cylinder_example(dimx=1000, dimy=1000, screen_x = 1000, screen_y = 1000, simulation_end = 40, precision = "float", Debug = True, radius = 50):
    """
    Run a 2D supersonic wedge simulation and render the resulting flow field.

    This function configures and executes a shockFLOW simulation of a
    supersonic freestream (Mach 1.8) impinging on a wedge, using the
    bundled "config_wedge.yaml" / "settings_wedge.yaml" example configs.

    **VRAM REQUIREMENT**: Default dimensions (dimx=1000, dimy=1000)
    require **~500 MB of VRAM**.

    Freestream Conditions
    ----------------------
    - Temperature   : 300.0 K
    - Pressure      : 100000 Pa
    - Density       : 1.0 kg/m^3
    - Gas constant  : 287.058 J/(kg*K)
    - Gamma (cp/cv) : 1.4
    - Viscosity     : 1.886109e-4 Pa*s
    - Mach number   : 1.8

    Geometry
    --------
    - Wedge width  : 400 (grid units)
    - Wedge height : 400 (grid units)


    Parameters
    ----------
    dimx : int, optional
        Number of grid cells in the x-direction, used to set the simulation
        domain resolution. Default is 1000.
    dimy : int, optional
        Number of grid cells in the y-direction, used to set the simulation
        domain resolution. Default is 1000.

    Returns
    -------
    None

    """
    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    path_run = os.getcwd()
    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))

    config = "example_configs/config_sphereSF.yaml"
    settings = "example_configs/settings_sphereSF.yaml"

    # nc.create_rectangle_bc(dimx, dimy, os.getcwd() + "/")




    nc.create_sphere_bc(dimx, dimy, os.getcwd() + "/", radius)
    os.chdir(module_dir)





    #config = "example_configs/shock_impact_scenario/impact.yaml"
    #settings = "example_configs/shock_impact_scenario/settings.yaml"

    # helpers.set_boundary_files(config, path_run + "/rect.bin",  path_run + "/rectn.bin")
    # helpers.set_simulation_domain(config, dimx, dimy, 1)
    # helpers.set_logging_folder(settings, path_run + "/Logs")
    # helpers.set_ext_event_times(config, simulation_end)
    # helpers.set_debug_mode(settings, True)
    # helpers.set_ffmpeg_output_path(settings, output_dir)
    # flow.custom(settings, config, path_run)
    # os.chdir(path_run)

    helpers.set_video_resolution(settings, screen_x, screen_y)
    helpers.set_video_resolution(config, screen_x, screen_y)
    helpers.set_precision(settings, precision)
    helpers.set_boundary_files(config, path_run + "/sphere.bin",  path_run + "/spheren.bin")
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_debug_mode(settings, Debug)
    helpers.set_ffmpeg_output_path(settings, output_dir)
    flow.custom(settings, config, path_run)
    os.chdir(path_run)



def run_cylinder_example_monatomic(dimx=1000, dimy=1000, screen_x = 1000, screen_y = 1000, simulation_end = 40, precision = "float", Debug = True, radius = 50):
    """
    Run a 2D supersonic wedge simulation and render the resulting flow field.

    This function configures and executes a shockFLOW simulation of a
    supersonic freestream (Mach 1.8) impinging on a wedge, using the
    bundled "config_wedge.yaml" / "settings_wedge.yaml" example configs.

    **VRAM REQUIREMENT**: Default dimensions (dimx=1000, dimy=1000)
    require **~500 MB of VRAM**.

    Freestream Conditions
    ----------------------
    - Temperature   : 300.0 K
    - Pressure      : 100000 Pa
    - Density       : 1.0 kg/m^3
    - Gas constant  : 287.058 J/(kg*K)
    - Gamma (cp/cv) : 1.4
    - Viscosity     : 1.886109e-4 Pa*s
    - Mach number   : 1.8

    Geometry
    --------
    - Wedge width  : 400 (grid units)
    - Wedge height : 400 (grid units)


    Parameters
    ----------
    dimx : int, optional
        Number of grid cells in the x-direction, used to set the simulation
        domain resolution. Default is 1000.
    dimy : int, optional
        Number of grid cells in the y-direction, used to set the simulation
        domain resolution. Default is 1000.

    Returns
    -------
    None

    """
    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    path_run = os.getcwd()
    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))

    config = "example_configs/config_sphereSF.yaml"
    settings = "example_configs/settings_sphereSF.yaml"

    # nc.create_rectangle_bc(dimx, dimy, os.getcwd() + "/")




    nc.create_sphere_bc(dimx, dimy, os.getcwd() + "/", radius)
    os.chdir(module_dir)





    #config = "example_configs/shock_impact_scenario/impact.yaml"
    #settings = "example_configs/shock_impact_scenario/settings.yaml"

    # helpers.set_boundary_files(config, path_run + "/rect.bin",  path_run + "/rectn.bin")
    # helpers.set_simulation_domain(config, dimx, dimy, 1)
    # helpers.set_logging_folder(settings, path_run + "/Logs")
    # helpers.set_ext_event_times(config, simulation_end)
    # helpers.set_debug_mode(settings, True)
    # helpers.set_ffmpeg_output_path(settings, output_dir)
    # flow.custom(settings, config, path_run)
    # os.chdir(path_run)

    helpers.set_video_resolution(settings, screen_x, screen_y)
    helpers.set_video_resolution(config, screen_x, screen_y)
    helpers.set_precision(settings, precision)
    helpers.set_boundary_files(config, path_run + "/sphere.bin",  path_run + "/spheren.bin")
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_debug_mode(settings, Debug)
    helpers.set_ffmpeg_output_path(settings, output_dir)
    flow.customMonatomic(settings, config, path_run)
    os.chdir(path_run)


def run_naca_example(dimx=1000, dimy=1000, screen_x = 1000, screen_y = 1000, simulation_end = 40, precision = "float", Debug = True):
    """
    Run a 2D supersonic wedge simulation and render the resulting flow field.

    This function configures and executes a shockFLOW simulation of a
    supersonic freestream (Mach 1.8) impinging on a wedge, using the
    bundled "config_wedge.yaml" / "settings_wedge.yaml" example configs.

    **VRAM REQUIREMENT**: Default dimensions (dimx=1000, dimy=1000)
    require **~500 MB of VRAM**.

    Freestream Conditions
    ----------------------
    - Temperature   : 300.0 K
    - Pressure      : 100000 Pa
    - Density       : 1.0 kg/m^3
    - Gas constant  : 287.058 J/(kg*K)
    - Gamma (cp/cv) : 1.4
    - Viscosity     : 1.886109e-4 Pa*s
    - Mach number   : 1.8

    Geometry
    --------
    - Wedge width  : 400 (grid units)
    - Wedge height : 400 (grid units)


    Parameters
    ----------
    dimx : int, optional
        Number of grid cells in the x-direction, used to set the simulation
        domain resolution. Default is 1000.
    dimy : int, optional
        Number of grid cells in the y-direction, used to set the simulation
        domain resolution. Default is 1000.

    Returns
    -------
    None

    """
    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    path_run = os.getcwd()
    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))

    config = "example_configs/config_sphereSF.yaml"
    settings = "example_configs/settings_sphereSF.yaml"

    # nc.create_rectangle_bc(dimx, dimy, os.getcwd() + "/")




    nc.create_naca_bc(dimx, dimy, os.getcwd() + "/", invert=False)
    os.chdir(module_dir)





    #config = "example_configs/shock_impact_scenario/impact.yaml"
    #settings = "example_configs/shock_impact_scenario/settings.yaml"

    # helpers.set_boundary_files(config, path_run + "/rect.bin",  path_run + "/rectn.bin")
    # helpers.set_simulation_domain(config, dimx, dimy, 1)
    # helpers.set_logging_folder(settings, path_run + "/Logs")
    # helpers.set_ext_event_times(config, simulation_end)
    # helpers.set_debug_mode(settings, True)
    # helpers.set_ffmpeg_output_path(settings, output_dir)
    # flow.custom(settings, config, path_run)
    # os.chdir(path_run)

    helpers.set_video_resolution(settings, screen_x, screen_y)
    helpers.set_video_resolution(config, screen_x, screen_y)
    helpers.set_precision(settings, precision)
    helpers.set_boundary_files(config, path_run + "/naca.bin",  path_run + "/nacan.bin")
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_debug_mode(settings, Debug)
    helpers.set_ffmpeg_output_path(settings, output_dir)
    flow.custom(settings, config, path_run)
    os.chdir(path_run)


def run_nozzle_example(dimx=1000, dimy=1000, screen_x = 1000, screen_y = 1000, simulation_end = 40, precision = "float", Debug = True):
    """


    Returns
    -------
    None

    """
    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    path_run = os.getcwd()
    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))

    nc.create_nozzle_bc(dimx, dimy, os.getcwd() + "/", 4)
    os.chdir(module_dir)





    config = "example_configs/config_nozzle.yaml"
    settings = "example_configs/settings_nozzle.yaml"

    helpers.set_video_resolution(settings, screen_x, screen_y)
    helpers.set_video_resolution(config, screen_x, screen_y)
    helpers.set_precision(settings, precision)
    helpers.set_boundary_files(config, path_run + "/nozzlez.bin",  path_run + "/nozzlez_n.bin")
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_debug_mode(settings, Debug)
    helpers.set_ffmpeg_output_path(settings, output_dir)
    
    flow.custom(settings, config, path_run)
    os.chdir(path_run)



def run_rectangle_example2(dimx=1000, dimy=1000, screen_x = 1000, screen_y = 1000, simulation_end = 40, precision = "float", Debug =True, size = 400):
    """
    This function creates a rectangle and runs a simulation where a density discontinuity
    is propogated and eventually impacts the rectangle. 
    -------
    None

    """
    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    path_run = os.getcwd()
    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))

    nc.create_rectangle_bc(dimx, dimy, os.getcwd() + "/", size, size)
    os.chdir(module_dir)





    config = "example_configs/shock_impact_scenario/impact.yaml"
    settings = "example_configs/shock_impact_scenario/settings.yaml"
    helpers.set_video_resolution(settings, screen_x, screen_y)
    helpers.set_video_resolution(config, screen_x, screen_y)
    helpers.set_precision(settings, precision)
    helpers.set_boundary_files(config, path_run + "/rect.bin",  path_run + "/rectn.bin")
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_debug_mode(settings, Debug)
    helpers.set_ffmpeg_output_path(settings, output_dir)

    print("Parameters set. Starting simulation:", flush=True)
    flow.custom(settings, config, path_run)
    os.chdir(path_run)


def run_naca_example2(dimx=1000, dimy=1000, simulation_end = 40):
    """
    Run a 2D supersonic wedge simulation and render the resulting flow field.

    This function configures and executes a shockFLOW simulation of a
    supersonic freestream (Mach 1.8) impinging on a wedge, using the
    bundled "config_wedge.yaml" / "settings_wedge.yaml" example configs.

    **VRAM REQUIREMENT**: Default dimensions (dimx=1000, dimy=1000)
    require **~500 MB of VRAM**.

    Freestream Conditions
    ----------------------
    - Temperature   : 300.0 K
    - Pressure      : 100000 Pa
    - Density       : 1.0 kg/m^3
    - Gas constant  : 287.058 J/(kg*K)
    - Gamma (cp/cv) : 1.4
    - Viscosity     : 1.886109e-4 Pa*s
    - Mach number   : 1.8

    Geometry
    --------
    - Wedge width  : 400 (grid units)
    - Wedge height : 400 (grid units)


    Parameters
    ----------
    dimx : int, optional
        Number of grid cells in the x-direction, used to set the simulation
        domain resolution. Default is 1000.
    dimy : int, optional
        Number of grid cells in the y-direction, used to set the simulation
        domain resolution. Default is 1000.

    Returns
    -------
    None

    """
    os.makedirs("Videos", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    path_run = os.getcwd()
    output_dir = os.getcwd() + "/Videos/"
    module_dir = os.path.dirname(os.path.abspath(__file__))

    nc.create_naca_bc(dimx, dimy, os.getcwd() + "/")
    os.chdir(module_dir)





    config = "example_configs/shock_impact_scenario/impact.yaml"
    settings = "example_configs/shock_impact_scenario/settings.yaml"

    helpers.set_boundary_files(config, path_run + "/naca.bin",  path_run + "/nacan.bin")
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_logging_folder(settings, path_run + "/Logs")
    helpers.set_ext_event_times(config, simulation_end)
    helpers.set_debug_mode(settings, True)
    helpers.set_ffmpeg_output_path(settings, output_dir)
    flow.custom(settings, config, path_run)
    os.chdir(path_run)



def run_riemann_example(dimx=20000, dimy=300):
    """
    Run a 1D Riemann (shock-tube) simulation and visualize the results.

    This function configures and executes a shockFLOW simulation of a
    Riemann shock-tube problem, then reads the resulting midline flow-field
    data from the output HDF5 snapshot and compares it against the exact
    analytical solution at the same physical time. Results are plotted as
    a 2x2 grid of dimensionless profiles along the x-axis: density ratio,
    pressure ratio, temperature ratio, and x-velocity.

    Workflow
    --------
    1. Configure the simulation domain size and event timing in the
       "riemann.yaml" config file.
    2. Configure debug mode and output paths (FFmpeg, HDF5) in the
       "settings.yaml" settings file.
    3. Run the simulation via `flow.custom`, writing output to the current
       working directory.
    4. Read the midline data from the "200" snapshot and plot it against
       the analytical solution.

    Parameters
    ----------
    dimx : int, optional
        Number of grid cells in the x-direction, used to set the simulation
        domain resolution. Default is 10000.
    dimy : int, optional
        Number of grid cells in the y-direction, used to set the simulation
        domain resolution. Default is 300.

    Side Effects
    ------------
    - Creates a "Videos" directory in the current working directory if it
      does not already exist.
    - Modifies "riemann.yaml" (domain size, event times) and "settings.yaml"
      (debug mode, FFmpeg/HDF5 output paths) in place.
    - Runs a shockFLOW simulation, writing output files to the current
      working directory.
    - Reads "<cwd>/200" as an HDF5 midline dataset along the x-axis.
    - Saves a comparison figure to "Videos/riemann_comparison.png".
    - Displays the figure interactively via `plt.show()`.

    Returns
    -------
    None

    """
    import shockFLOW.utils as helpers
    import os
    import numpy as np
    from shockFLOW.utils import hdf5_read_midline
    os.makedirs("Videos", exist_ok=True)
    current_dir = os.getcwd()
    module_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(module_dir)

    config = "example_configs/riemann.yaml"
    settings = "example_configs/settings.yaml"
    helpers.set_simulation_domain(config, dimx, dimy, 1)
    helpers.set_ext_event_times(config, 300)  # simulate up to 300us
    helpers.set_debug_mode(settings, False)
    helpers.set_ffmpeg_output_path(settings, current_dir + "/")
    helpers.set_hdf5_output_path(config, current_dir + "/")
    flow.custom(settings, config, current_dir)
    os.chdir(current_dir)

    data = hdf5_read_midline(os.getcwd() + "/200", axis="x")

    import matplotlib.pyplot as plt
    import shockFLOW.analytical as anal

    # Analytical solution (no vx)
    x_a, p_a, rho_a, temp_a = anal.get_analytical_solution(x0=0, time=200e-6)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
    fig.suptitle("Riemann Problem — Simulation vs. Analytical Solution (t = 200 μs)",
                 fontsize=14, fontweight="bold")

    sim_style = dict(color="tab:blue", lw=1.5, label="Simulation")
    ana_style = dict(color="tab:red", lw=1.5, ls="--", label="Analytical")

    plot_specs = [
        (axes[0, 0], "density",     rho_a,  r"Density Ratio $\rho / \rho_0$"),
        (axes[0, 1], "pressure",    p_a,    r"Pressure Ratio $p / p_0$"),
        (axes[1, 0], "temperature", temp_a, r"Temperature Ratio $T / T_0$"),
        (axes[1, 1], "vx",          None,   r"Velocity $v_x$ [m/s]"),
    ]

    for ax, key, analytical, ylabel in plot_specs:
        ax.plot(data["coord"], data[key], **sim_style)
        if analytical is not None:
            ax.plot(x_a, analytical, **ana_style)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_xlim(-10, 10)
        ax.legend(fontsize=9, frameon=True)
        ax.tick_params(labelsize=9)

    axes[1, 0].set_xlabel("x [mm]", fontsize=10)
    axes[1, 1].set_xlabel("x [mm]", fontsize=10)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(os.getcwd(), "Videos", "riemann_comparison.png"), dpi=200)
    plt.show()
