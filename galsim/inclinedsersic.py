# Copyright (c) 2012-2016 by the GalSim developers team on GitHub
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
"""@file inclinedsersic.py

InclinedSersic is a class representing a (possibly-truncated) Sersic profile inclined to the LOS.
"""

from galsim import GSObject
import galsim

from . import _galsim


class InclinedSersic(GSObject):
    """A class describing an inclined sersic profile. This class is general, and so for certain
    special cases, more specialized classes will be more efficient. For the case where n==1
    with no truncation, the InclinedExponential class will be much more efficient. For the case
    where the inclination angle is zero (face-on), the Sersic class will be slightly more efficient.

    The Inclined Sersic surface brightness profile is characterized by four properties: its
    Sersic index `n', its inclination angle (where 0 degrees = face-on and 90 degrees = edge-on),
    its scale radius, and its scale height. The 3D light distribution function is:

        I(R,z) = I_0 / (2h_s) * sech^2 (z/h_s) * exp[-b*(R/r_s)^{1/n}]

    where z is the distance along the minor axis, R is the radial distance from the minor axis,
    r_s is the scale radius of the disk, h_s is the scale height of the disk, and I_0 is the central
    surface brightness of the face-on disk. The 2D light distribution function is then determined
    from the scale height and radius here, along with the inclination angle.

    In this implementation, the profile is inclined along the y-axis. This means that it will likely
    need to be rotated in most circumstances.

    At present, this profile is not enabled for photon-shooting.

    The allowed range of values for the `n` parameter is 0.3 <= n <= 6.2.  An exception will be
    thrown if you provide a value outside that range, matching the range of the Sersic profile.

    This class shares the caching of Hankel transformations with the Sersic class; see that
    class for documentation on efficiency considerations with regards to caching.

    A profile can be initialized using one (and only one) of two possible size parameters:
    `scale_radius` or `half_light_radius`.  Exactly one of these two is required. Similarly,
    at most one of `scale_height' and `scale_h_over_r' is required; if neither is given, the
    default of scale_h_over_r = 0.1 will be used.

    Initialization
    --------------

    @param n                  The Sersic index, n.
    @param inclination        The inclination angle, which must be a galsim.Angle instance
    @param scale_radius       The scale radius of the disk.  Typically given in arcsec.
                              This can be compared to the 'scale_radius' parameter of the
                              galsim.Sersic class, and in the face-on case, the same same scale
                              radius will result in the same 2D light distribution as with that
                              class. Exactly one of this and half_light_radius must be provided.
    @param half_light_radius  The half-light radius of disk when seen face-on. Exactly one of this
                              and scale_radius must be provided.
    @param scale_height       The scale height of the exponential disk.  Typically given in arcsec.
                              [default: None]
    @param scale_h_over_r     In lieu of the scale height, you may specify the ratio of the
                              scale height to the scale radius. [default: 0.1]
    @param flux               The flux (in photons) of the profile. [default: 1]
    @param trunc              An optional truncation radius at which the profile is made to drop to
                              zero, in the same units as the size parameter.
                              [default: 0, indicating no truncation]
    @param flux_untruncated   Should the provided `flux` and `half_light_radius` refer to the
                              untruncated profile? See the documentation of the Sersic class for more
                              details. [default: False]
    @param gsparams           An optional GSParams argument.  See the docstring for GSParams for
                              details. [default: None]

    Methods
    -------

    In addition to the usual GSObject methods, InclinedSersic has the following access methods:

        >>> n = inclined_sersic_obj.getN()
        >>> inclination = inclined_sersic_obj.getInclination()
        >>> r0 = inclined_sersic_obj.getScaleRadius()
        >>> h0 = inclined_sersic_obj.getScaleHeight()
        >>> hlr = inclined_sersic_obj.getHalfLightRadius()
    """
    _req_params = { "inclination" : galsim.Angle, "n" : float }
    _opt_params = { "scale_height" : float, "scale_h_over_r" : float, "flux" : float }
    _single_params = [ { "scale_radius" : float , "half_light_radius" : float } ]
    _takes_rng = False

    def __init__(self, n, inclination, half_light_radius=None, scale_radius=None, scale_height=None,
                 scale_h_over_r=None, flux=1., trunc=0., flux_untruncated=False, gsparams=None):

        # Check that the scale/half-light radius is valid
        if scale_radius is not None:
            if not scale_radius > 0.:
                raise Exception("scale_radius must be > zero.")
        else:
            if not half_light_radius > 0.:
                raise Exception("half_light_radius must be > zero.")

        # Check if we need to use default scale_h_over_r
        if scale_height is None:
            if scale_h_over_r is None:
                scale_h_over_r = 0.1

            # Set the scale height here if we know the scale radius
            if scale_radius is not None:
                scale_height = scale_h_over_r * scale_radius
        else:
            # Check that scale_h_over_r wasn't also passed
            if scale_h_over_r is not None:
                raise Exception("At most one of scale_height and scale_h_over_r may be specified.")
            elif scale_radius is not None:
                scale_h_over_r = scale_height / scale_radius

        # Check that trunc is valid
        if trunc < 0.:
            raise Exception("trunc must be >= zero (zero implying no truncation).")

        # Explicitly check for angle type, so we can give more informative error if eg. a float is
        # passed
        if not isinstance(inclination, galsim.Angle):
            raise TypeError("Input inclination should be an Angle")

        GSObject.__init__(self, _galsim.SBInclinedSersic(n, inclination, scale_radius, half_light_radius,
                                                         scale_height, scale_h_over_r, flux, trunc, flux_untruncated,
                                                         gsparams))
        self._flux_untruncated = flux_untruncated
        self._gsparams = gsparams

    def getN(self):
        """Return the Sersic index `n` for this profile.
        """
        return self.SBProfile.getN()

    def getInclination(self):
        """Return the inclination angle for this profile as a galsim.Angle instance.
        """
        return self.SBProfile.getInclination()

    def getScaleRadius(self):
        """Return the scale radius for this profile.
        """
        return self.SBProfile.getScaleRadius()

    def getHalfLightRadius(self):
        """Return the half light radius for this profile (or rather, what it would be if the
           profile were face-on).
        """
        return self.SBProfile.getHalfLightRadius()

    def getScaleHeight(self):
        """Return the scale height for this profile.
        """
        return self.SBProfile.getScaleHeight()

    def getScaleHOverR(self):
        """Return the scale height over scale radius for this profile.
        """
        return self.SBProfile.getScaleHeight() / self.SBProfile.getScaleRadius()

    def getTrunc(self):
        """Return the truncation radius for this profile.
        """
        return self.SBProfile.getTrunc()

    @property
    def n(self): return self.getN()
    @property
    def inclination(self): return self.getInclination()
    @property
    def scale_radius(self): return self.getScaleRadius()
    @property
    def half_light_radius(self): return self.getHalfLightRadius()
    @property
    def scale_height(self): return self.getScaleHeight()
    @property
    def scale_h_over_r(self): return self.getScaleHOverR()
    @property
    def trunc(self): return self.getTrunc()

    def __eq__(self, other):
        return ((isinstance(other, galsim.InclinedSersic) and
                 (self.n == other.n) and
                 (self.inclination == other.inclination) and
                 (self.scale_radius == other.scale_radius) and
                 (self.scale_height == other.scale_height) and
                 (self.flux == other.flux) and
                 (self.trunc == other.trunc) and
                 (self._gsparams == other._gsparams)))

    def __hash__(self):
        return hash(("galsim.InclinedSersic", self.n, self.inclination, self.scale_radius,
                    self.scale_height, self.flux, self.trunc, self._gsparams))
    def __repr__(self):
        return ('galsim.InclinedSersic(n=%r, inclination=%r, scale_radius=%r, scale_height=%r, ' +
               'flux=%r, trunc=%r, gsparams=%r)') % (self.n,
            self.inclination, self.scale_radius, self.scale_height, self.flux, self.trunc,
            self._gsparams)

    def __str__(self):
        s = 'galsim.InclinedSersic(n=%s, inclination=%s, scale_radius=%s, scale_height=%s' % (
                self.n, self.inclination, self.scale_radius, self.scale_height)
        if self.flux != 1.0:
            s += ', flux=%s' % self.flux
        if self.trunc != 0.:
            s += ', trunc=%s' % self.trunc
        s += ')'
        return s

_galsim.SBInclinedSersic.__getinitargs__ = lambda self: (self.getN(),
        self.getInclination(), self.getScaleRadius(), None, self.getScaleHeight(), None,
        self.getFlux(), self.getTrunc(), False, self.getGSParams())
_galsim.SBInclinedSersic.__getstate__ = lambda self: None
_galsim.SBInclinedSersic.__repr__ = lambda self: \
        'galsim._galsim.SBInclinedSersic(%r, %r, %r, %r, %r, %r, %r, %r, %r, %r)' % self.__getinitargs__()
