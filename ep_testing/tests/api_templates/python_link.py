#!/usr/bin/env python3
import sys
sys.path.insert(0, '%s')
from pyenergyplus.api import EnergyPlusAPI  # noqa: E402
api = EnergyPlusAPI()
state = api.state_manager.new_state()
glycol = api.functional.glycol(state, u"water")
for t in [5.0, 15.0, 25.0]:
    cp = glycol.specific_heat(state, t)
    rho = glycol.density(state, t)
