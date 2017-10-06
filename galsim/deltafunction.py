# Copyright (c) 2012-2017 by the GalSim developers team on GitHub
# https://github.com/GalSim-developers
#
# This file is part of GalSim: The modular galaxy image simulation toolkit.
# https://github.com/GalSim-developers/GalSim
#
# GalSim is free software: redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions, and the disclaimer given in the accompanying LICENSE
#    file.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions, and the disclaimer given in the documentation
#    and/or other materials provided with the distribution.
#
"""@file deltafunction.py
This file implements the DeltaFunction surface brightness profile
"""

import numpy as np
import math

from . import _galsim
from .gsobject import GSObject
from .gsparams import GSParams
from .position import PositionD


class DeltaFunction(GSObject):
    """A class describing a DeltaFunction surface brightness profile.

    The DeltaFunction surface brightness profile is characterized by a single property,
    its `flux'.

    Initialization
    --------------

    A DeltaFunction can be initialized with a specified flux.

    @param flux             The flux (in photons/cm^2/s) of the profile. [default: 1]
    @param gsparams         An optional GSParams argument.  See the docstring for GSParams for
                            details. [default: None]

    Methods and Properties
    ----------------------

    DeltaFunction simply has the usual GSObject methods and properties.
    """
    # Initialization parameters of the object, with type information, to indicate
    # which attributes are allowed / required in a config file for this object.
    # _req_params are required
    # _opt_params are optional
    # _single_params are a list of sets for which exactly one in the list is required.
    # _takes_rng indicates whether the constructor should be given the current rng.
    _req_params = {}
    _opt_params = { "flux" : float }
    _single_params = []
    _takes_rng = False

    _mock_inf = 1.e300  # Some arbitrary very large number to use when we need infinity.

    def __init__(self, flux=1., gsparams=None):
        self._gsparams = GSParams.check(gsparams)
        self._flux = flux

    @property
    def _sbp(self):
        # NB. I only need this until compound and transform are reimplemented in Python...
        return _galsim.SBDeltaFunction(self._flux, self.gsparams._gsp)

    @property
    def flux(self):
        return self._flux

    def __eq__(self, other):
        return (isinstance(other, DeltaFunction) and
                self.flux == other.flux and
                self.gsparams == other.gsparams)

    def __hash__(self):
        return hash(("galsim.DeltaFunction", self.flux, self.gsparams))

    def __repr__(self):
        return 'galsim.DeltaFunction(flux=%r, gsparams=%r)'%(self.flux, self.gsparams)

    def __str__(self):
        s = 'galsim.DeltaFunction('
        if self.flux != 1.0:
            s += 'flux=%s'%self.flux
        s += ')'
        return s

    # These are the GSObject functions that need to be overridden
    def maxK(self):
        return self._mock_inf

    def stepK(self):
        return self._mock_inf

    def hasHardEdges(self):
        return False

    def isAxisymmetric(self):
        return True

    def isAnalyticX(self):
        return False

    def isAnalyticK(self):
        return True

    @property
    def centroid(self):
        return PositionD(0,0)

    def getPositiveFlux(self):
        return self._flux

    def getNegativeFlux(self):
        return 0.

    def maxSB(self):
        return self._mock_inf

    def _xValue(self, pos):
        if pos.x == 0. and pos.y == 0.:
            return self._mock_inf
        else:
            return 0.

    def _kValue(self, kpos):
        return self.flux

    def _drawReal(self, image):
        raise NotImplemented("Cannot draw a DeltaFunction in real space")

    def _shoot(self, photons, rng):
        flux_per_photon = self.flux / len(photons)
        photons.x = 0.
        photons.y = 0.
        photons.flux = flux_per_photon

    def _drawKImage(self, image):
        image.array[:,:] = self.flux
        return image