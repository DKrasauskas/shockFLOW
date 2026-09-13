import shockFLOW.solver as flow
import shockFLOW.utils as helpers
import os

import h5py
import numpy as np

from shockFLOW.utils import hdf5_read_midline

data = hdf5_read_midline("/home/dominykas/Desktop/shockFLOW_tutorials/riemann_problem/Results/200", axis="x")
import matplotlib.pyplot as plt
import numpy as np

a = np.arange(0, 1, 1.0 / len(data["temperature"]))
print(a.shape)
plt.plot(data['coord'], data['density'])


import analytical as anal

x, p, rho, temp = anal.get_analytical_solution(x0=0, time=200e-6)
#plt.plot(x, temp)
plt.xlim(-10, 10)
plt.show()
# os.makedirs("Videos", exist_ok=True)

# config = "riemann_problem/riemann.yaml"
# settings = "riemann_problem/settings.yaml"
# helpers.set_simulation_domain(config, 20000, 300, 1)
# helpers.set_ext_event_times(config, 300) #simulate up to 40us
# helpers.set_debug_mode(settings, False)
# helpers.set_ffmpeg_output_path(settings, os.getcwd() + "/")
# flow.custom(settings, config, os.getcwd())
