import numpy as np
import matplotlib.pyplot as plt


class Riemman1d:
    def __init__(self, case, gamma = 1.4):
        self.p1, self.v1, self.rho1, self.t1, self.p6, self.v6, self.rho6, self.t6 = case
        self.gamma = 1.4
        self.a1 =  np.sqrt(gamma * self.p1 / self.rho1)
        self.a6 =  np.sqrt(gamma * self.p6 / self.rho6)

        self.A6 = 2 / (self.rho6 * (gamma + 1))
        self.B6 =  self.p6 * (gamma - 1) / (gamma + 1)
        self.C6 = 2 * self.a1 / (gamma - 1)
        self.D6 = (gamma - 1) / (2 * gamma)

    def pstar_func(self, pstar):
        return (pstar - self.p6) * np.sqrt(self.A6 / (pstar + self.B6)) + self.C6 * ((pstar / self.p1) ** self.D6 - 1)

    def _solve_pstar(self):
        pstar_0 = 0
        pstar_1 = 100
        lhs = self.pstar_func(pstar_0)
        rhs = self.pstar_func(pstar_1)
        while(True):
            p_current = (pstar_0 + pstar_1) / 2
            v1 = self.pstar_func(p_current)
            if lhs * v1 < 0:
                rhs = v1
                pstar_1 = p_current
            else:
                lhs = v1
                pstar_0 = p_current
            if(abs(v1) < 1e-12):
                return p_current

    def _computeValues(self):
        self.pstar = self._solve_pstar()
        self.p3 = self.pstar
        self.p4 = self.pstar
        self.v3 = self.v1 - self.C6 * ((self.p3 / self.p1) ** self.D6 - 1)
        self.v4 = self.v6 + (self.p4 - self.p6) * np.sqrt(self.A6 / (self.p4 + self.B6))
        self.rho3 = self.rho1 * (self.p3 / self.p1) ** (1 / self.gamma)
        self.rho4 = self.rho6 * (self.p6 * (self.gamma - 1) + self.p4 * (self.gamma + 1)) / (self.p4 * (self.gamma - 1) + self.p6 * (self.gamma + 1))

        self.a3 = np.sqrt(self.gamma * self.p3 / self.rho3)
        self.a4 = np.sqrt(self.gamma * self.p4 / self.rho4)

        self.V_head = self.v1 - self.a1
        self.V_tail = self.v3 - self.a3
        self.V_contact = self.v4
        self.V_shock = self.v6 + self.a6 * np.sqrt((self.gamma + 1) * self.p4 / (2 * self.gamma * self.p6) + (self.gamma - 1) / (2 * self.gamma))

    def getSolution(self, x0, T, begin, end, step = 0.001):
        self._computeValues()
        x = np.arange(begin, end, step)
        p = np.zeros_like(x)
        rho = np.zeros_like(x)
        temp = np.zeros_like(x)
        for i in range(len(x)):
            x_local = x[i] - x0
            if x_local < T * self.V_head:
                p[i] = self.p1
                rho[i] = self.rho1
                temp[i] = p[i] / rho[i]
            if x_local > T * self.V_head and x_local < T * self.V_tail:
                p[i] = self.p1 * ( 2 / (self.gamma + 1) + (self.gamma - 1) / (self.a1 * (self.gamma + 1)) * (self.v1 - (x_local / T))) ** (2 * self.gamma / (self.gamma - 1))
                rho[i] = self.rho1 * ( 2 / (self.gamma + 1) + (self.gamma - 1) / (self.a1 * (self.gamma + 1)) * (self.v1 - (x_local / T))) ** (2 / (self.gamma - 1))
                temp[i] = p[i] / rho[i]
            if x_local > T * self.V_tail and x_local < T * self.V_contact:
                p[i] = self.p3
                rho[i] = self.rho3
                temp[i] = p[i] / rho[i]
            if x_local > T * self.V_contact and x_local < T * self.V_shock:
                p[i] = self.p4
                rho[i] = self.rho4
                temp[i] = p[i] / rho[i]
            if x_local > T * self.V_shock:
                p[i] = self.p6
                rho[i] = self.rho6
                temp[i] = p[i] / rho[i]
        return x, p, rho, temp


def get_analytical_solution(time = 400.8534e-6, cs = 347 /1.4, char = 0.02, x0 = -50, analytical = True):
    T_nondim = time * cs / char
    r_analytic = Riemman1d((4, 0, 4, 1, 1, 0, 1, 1))
    return r_analytic.getSolution(x0, T_nondim, -75, 75)