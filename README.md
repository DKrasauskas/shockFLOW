# ShockFLOW - a GPU based 1D/2D Transonic CFD solver 
Shock flow is a purely GPU-based transonic 1D/2D CFD solver based on the Entropic Lattice Boltzman Methods.  This module implements the interface via python to the backend, build
entirely in CUDA/C++ with OpenGL support. It can be used to simulate complex transonic and supersonic 1D and 2D problems, remaining stable and well posed up until Mach 5.0. 
<img width="1802" height="941" alt="image" src="https://github.com/user-attachments/assets/62d2ce6d-934a-40e8-b6e4-2e1ec5a32c65" />


<table>
  <tr>
     <td>
      <img src="https://github.com/user-attachments/assets/82ecc0ce-4fa6-40a3-aaca-b98d241da657" width="100%" >
        <figcaption align="center"> Density Field </figcaption>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/077b73eb-55b2-4bdb-bcd9-73a287a5a580" width="100%">
       <figcaption align="center"> Density Gradient </figcaption>
    </td>
  </tr>
</table>
For examples, usage and documentation, see the official example repository https://github.com/DKrasauskas/shockFLOW-examples:


### GPU Architecture Support

As of the latest release, the currently supported compute modes and architectures are:
 
| Architecture | Compute Capability | FP32 | FP64 | Linux | Windows | shockFLOW  | shockFLOW-cu129 |
|--------------|--------------------|:----:|:----:|:-----:|:-------:|:----------------------:|:----------------:|
| Pascal       | 6.x                | Yes  | No   | Yes   | No      |                        | x                |
| Volta        | 7.0                | Yes  | No   | Yes   | No      |                        | x                |
| Turing       | 7.5                | Yes  | No   | Yes   | Yes     | x                      | x                |
| Ampere       | 8.x                | Yes  | No   | Yes   | Yes     | x                      |                  |
| Ada Lovelace | 8.9                | Yes  | No   | Yes   | Yes     | x                      |                  |
| Hopper       | 9.0                | Yes  | No   | Yes   | Yes     | x                      |                  |
 

Note that FP64 is currently unavailable on all architectures. This is due to the large file size required for the pip repository. This will be fixed in the near future. 

## Requirements

For the module to function correctly, make sure you have:

- An NVIDIA GPU
- NVIDIA driver version ≥ 580
- [ffmpeg](https://ffmpeg.org/)

## Installation

The package is available via pip:

For CUDA 13.3 Versions (supporting GPUs with compute capability of >=7.5
```bash
pip install shockFLOW
```
For older GPUs, use a build with CUDA 12.9:


```bash
pip install shockFLOW-cu129
```

after installation, run a simple test program:
```python
import shockFLOW.solver as solver
solver.getDeviceProperties()
```


## Validation



While still being an experimental solver, we have performed a few validation runs and comparisons with existing software. 
For more details on the problems and detailed results, please see https://arc.aiaa.org/doi/abs/10.2514/6.2026-5123
### Gaussian Pulse Advection


### Riemann Problem
A classical Riemann problem, defined initially as a density discontinuity, splits into three waves. See https://en.wikipedia.org/wiki/Riemann_problem. 
This validation problem can be run by a builtin function of the solver.

The initial discontinuity is defined as:

$$
\frac{\rho}{\rho_0} = 4, \qquad \frac{T}{T_0} = 1, \qquad \frac{p}{p_0} = 4
$$

And the freestream conditions:

$$
\begin{aligned}
T_\infty &= 300.0 \ \text{K} \\
R &= 287.058 \ \text{J/(kg·K)} \\
p_\infty &= 100000 \ \text{Pa} \\
\rho_\infty &= 1.118 \ \text{kg/m}^3 \\
\gamma &= 1.4 \\
\mu &= 1.886109\times10^{-4} \ \text{Pa·s}
\end{aligned}
$$

Running the simulation for 200us (in physical time) produces the result:

<table>
  <tr>
     <td>
      <img src="https://github.com/user-attachments/assets/49a6b7d1-8c35-4fa2-9d0d-7d0f0022df39" >
        <figcaption align="center"> Comparison with analytical results </figcaption>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/32b742da-58cf-4159-b2ed-8d0ab7cf4dde" width="100%">
       <figcaption align="center"> Density gradient showing 1: rearwards moving expansion fan 2: contact discontinuity 3: shock </figcaption>
    </td>
  </tr>
</table>

### Schardin's problem: a shock - vortex interaction.

See more details: https://link.springer.com/article/10.1007/s001930000061

Similarly to the Riemann problem, the initial discontinuity is defined as:

$$
\frac{\rho}{\rho_0} = 4, \qquad \frac{T}{T_0} = 1, \qquad \frac{p}{p_0} = 4
$$

while the wedge is selected as an equilateral triangle, with:

$$
\begin{aligned}
L_c &= 20 \ \text{mm} \\
N_v &= 256 (voxels)
\end{aligned}
$$

Measuring time after the first shock impacts the wedge, density gradients are extracted and compared with both existing solvers and Schielern experimental photography. For detailed analysis and comparison, please see https://arc.aiaa.org/doi/abs/10.2514/6.2026-5123.
<img width="1903" height="956" alt="image" src="https://github.com/user-attachments/assets/5591b197-4d44-4bca-a5d4-45778ef3e79b" />

<table>
  <tr>
     <td>
      <img src="https://github.com/user-attachments/assets/79430210-f4c6-40db-a1e2-d09251681de8", width="100% >
        <figcaption align="center"> 92us after impact </figcaption>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/614734ed-1276-4d39-a740-48948254fdf3" width="100%">
       <figcaption align="center"> 105 us after impact </figcaption>
    </td>
  </tr>
</table>

## License

The Python interface in this repository is licensed under the [MIT License](./LICENSE).
The compiled CUDA/C++ backend distributed via PyPI is proprietary — free to use,
but reverse engineering, decompilation, or redistribution as a standalone product
is not permitted. See [LICENSE-BINARY.md](./LICENSE-BINARY.md) for full terms.
