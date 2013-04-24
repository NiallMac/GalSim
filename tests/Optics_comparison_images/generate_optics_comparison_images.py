# Copyright 2012, 2013 The GalSim developers:
# https://github.com/GalSim-developers
#
# This file is part of GalSim: The modular galaxy image simulation toolkit.
#
# GalSim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GalSim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GalSim.  If not, see <http://www.gnu.org/licenses/>
#
"""This script generates images in tests/Optics_comparison_images/ used by a unit test
test_OpticalPSF_aberration() in tests/test_optics.py.
Images in the directory is generated by using commit bff868949a290cbb93940de1493f36c940713ab3.
"""
import os
import sys

try:
    import galsim
except ImportError:
    path, filename = os.path.split(__file__)
    sys.path.append(os.path.abspath(os.path.join(path, "..", "..")))
    import galsim

if __name__ == "__main__":
    lod = 0.04
    obscuration = 0.3
    imsize = 128

    # predefine image of fixed size for drawing into
    im = galsim.ImageD(imsize, imsize)

    # defocus
    optics = galsim.OpticalPSF(lod, defocus = .5, obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_defocus.fits"))

    # astig1
    optics = galsim.OpticalPSF(lod, defocus = .5, astig1 = 1., obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_astig1.fits"))

    # astig2
    optics = galsim.OpticalPSF(lod, defocus = .5, astig2 = 1., obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_astig2.fits"))

    # coma1
    optics = galsim.OpticalPSF(lod, coma1 = .5, obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_coma1.fits"))

    # coma2
    optics = galsim.OpticalPSF(lod, coma2 = .5, obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_coma2.fits"))

    # trefoil1
    optics = galsim.OpticalPSF(lod, trefoil1 = .5, obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_trefoil1.fits"))

    # trefoil2
    optics = galsim.OpticalPSF(lod, trefoil2 = .5, obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_trefoil2.fits"))

    # spherical
    optics = galsim.OpticalPSF(lod, spher = .5, obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_spher.fits"))

    # all aberrations
    optics = galsim.OpticalPSF(lod, defocus = .5, astig1 = 0.5, astig2 = 0.3, coma1 = 0.4,
                               coma2 = -0.3, trefoil1 = -0.2, trefoil2 = 0.1, spher = -0.8,
                               obscuration = obscuration)
    im = optics.draw(im, dx=0.2*lod)
    im.write(os.path.join(os.path.abspath(os.path.dirname(__file__)), "optics_all.fits"))
