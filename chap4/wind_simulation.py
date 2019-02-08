"""
Class to determine wind velocity at any given moment,
calculates a steady wind speed and uses a stochastic
process to represent wind gusts. (Follows section 4.4 in uav book)
"""
import sys
sys.path.append('..')
import numpy as np
from math import sqrt
import control.matlab as ctrl

class wind_simulation:
    def __init__(self, Ts,Va=17):
        # steady state wind defined in the inertial frame
        self._steady_state = np.array([[0., 0., 0.]]).T
        # self.steady_state = np.array([[3., 1., 0.]]).T

        self._Ts = Ts
        #   Dryden gust model parameters (pg 56 UAV book)
        # HACK:  Setting Va to a constant value is a hack.  We set a nominal airspeed for the gust model.
        # Could pass current Va into the gust function and recalculate A and B matrices.
        #Va = 17

        sigma_u = 1.06
        sigma_v = sigma_u
        sigma_w = 0.7
        Lu = 200.
        Lv = Lu
        Lw = 50.

        # transfer functions for gust model
        k1 = sgima_v*sqrt(3.*Va/Lv)
        TF_u = ctrl.tf([sgima_u*sqrt(2.*Va/Lu)],[1.,Va/Lu],Ts)
        k1 = sgima_v*sqrt(3.*Va/Lv)
        TF_v = ctrl.tf([k1,k1*Va/(sqrt(3)*Lu)],[1.,2.*Va/Lu,(Va/Lu)**2]],Ts)
        k2 = sgima_v*sqrt(3.*Va/Lw)
        TF_w = ctrl.tf([k2,k2*Va/(sqrt(3)*Lw)],[1.,2.*Va/Lw,(Va/Lw)**2]],Ts)

        # Conversion to state space and pull out matrices
        SS_u = ctrl.tf2ss(TF_u)
        self._A_u = SS_u.A
        self._B_u = SS_u.B
        self._C_u = SS_u.C

        SS_v = ctrl.tf2ss(TF_v)
        self._A_v = SS_v.A
        self._B_v = SS_v.B
        self._C_v = SS_v.C

        SS_w = ctrl.tf2ss(TF_w)
        self._A_w = SS_w.A
        self._B_w = SS_w.B
        self._C_w = SS_w.C


    def update(self):
        # returns a six vector.
        #   The first three elements are the steady state wind in the inertial frame
        #   The second three elements are the gust in the body frame
        return np.concatenate(( self._steady_state, self._gust() ))

    def _gust(self):
        # calculate wind gust using Dryden model.  Gust is defined in the body frame
        w = np.random.randn()  # zero mean unit variance Gaussian (white noise)
        # propagate Dryden model (Euler method): x[k+1] = x[k] + Ts*( A x[k] + B w[k] )
        #self._gust_state += self._Ts * (self._A @ self._gust_state + self._B * w)
        self._gust_u += self._Ts * (self._A_u @ self._gust_u + self._B_u * w)
        gust_u = self._C_u @ self._gust_u
        self._gust_v += self._Ts * (self._A_v @ self._gust_v + self._B_v * w)
        gust_v = self._C_v @ self._gust_v
        self._gust_w += self._Ts * (self._A_w @ self._gust_w + self._B_w * w)
        gust_w = self._C_w @ self._gust_w
        self._gust_state = np.concatenate((gust_u,gust_v,gust_w))

        # output the current gust: y[k] = C x[k]
        return self._gust_state