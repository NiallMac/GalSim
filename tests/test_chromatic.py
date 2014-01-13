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
import numpy as np

from galsim_test_helpers import *

path, filename = os.path.split(__file__)
datapath = os.path.abspath(os.path.join(path, "../examples/data/"))

try:
    import galsim
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(path, "..")))
    import galsim

# def plotme(image):
#     from pylab import *
#     imshow(image.array)
#     show()

# liberal use of globals here...
zenith_angle = 20 * galsim.degrees
R610 = galsim.dcr.get_refraction(610.0, zenith_angle) # normalize refraction to 610nm

# some profile parameters to test with
bulge_n = 4.0
bulge_hlr = 0.5
bulge_e1 = 0.2
bulge_e2 = 0.2

disk_n = 1.0
disk_hlr = 1.0
disk_e1 = 0.4
disk_e2 = 0.2

PSF_hlr = 0.3
PSF_beta = 3.0
PSF_e1 = 0.01
PSF_e2 = 0.06

shear_g1 = 0.01
shear_g2 = 0.02

# load some spectra and a filter
Egal_wave, Egal_flambda = np.genfromtxt(os.path.join(datapath, 'CWW_E_ext.sed')).T
Egal_wave /= 10 # Angstrom -> nm
bulge_SED = galsim.SED(wave=Egal_wave, flambda=Egal_flambda, base_wavelength=500.0, norm=0.3)

Sbcgal_wave, Sbcgal_flambda = np.genfromtxt(os.path.join(datapath, 'CWW_Sbc_ext.sed')).T
Sbcgal_wave /= 10 # Angstrom -> nm
disk_SED = galsim.SED(wave=Sbcgal_wave, flambda=Sbcgal_flambda, base_wavelength=500.0, norm=0.3)

bluelim = 500
redlim = 720
filter_wave, filter_throughput = np.genfromtxt(os.path.join(datapath, 'LSST_r.dat')).T
wgood = (filter_wave >= bluelim) & (filter_wave <= redlim) # truncate out-of-band wavelengths
filter_wave = filter_wave[wgood][0::40]  # sparsify from 1 Ang binning to 40 Ang binning
filter_throughput = filter_throughput[wgood][0::40]
filter_fn = galsim.LookupTable(filter_wave, filter_throughput)

def test_direct_sum_vs_chromatic():
    """Compare two chromatic images, one generated by integrating over wavelength directly,
    and another generated using the galsim.chromatic module (which internally integrates over
    wavelength).
    """
    import time
    t1 = time.time()

    stamp_size = 32
    pixel_scale = 0.2

    #-----------
    # direct sum
    #-----------

    # make galaxy
    GS_gal = galsim.Sersic(n=bulge_n, half_light_radius=bulge_hlr)
    GS_gal.applyShear(e1=bulge_e1, e2=bulge_e2)
    GS_gal.applyShear(g1=shear_g1, g2=shear_g2)

    # make effective PSF
    mPSFs = [] # list of flux-scaled monochromatic PSFs
    N = 200
    h = (redlim * 1.0 - bluelim) / N
    ws = [bluelim + h*(i+0.5) for i in range(N)]
    shift_fn = lambda w:(0, (galsim.dcr.get_refraction(w, zenith_angle) - R610) / galsim.arcsec)
    dilate_fn = lambda w:(w/500.0)**(-0.2)
    for w in ws:
        flux = bulge_SED(w) * filter_fn(w) * h
        mPSF = galsim.Moffat(flux=flux, beta=PSF_beta, half_light_radius=PSF_hlr*dilate_fn(w))
        mPSF.applyShear(e1=PSF_e1, e2=PSF_e2)
        mPSF.applyShift(shift_fn(w))
        mPSFs.append(mPSF)
    PSF = galsim.Add(mPSFs)

    # final profile
    pixel = galsim.Pixel(pixel_scale)
    final = galsim.Convolve([GS_gal, PSF, pixel])
    GS_image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    GS_image = final.draw(image=GS_image)
    # plotme(GS_image)

    #----------
    # chromatic
    #----------

    # make galaxy
    mono_gal = galsim.Sersic(n=bulge_n, half_light_radius=bulge_hlr)
    chromatic_gal = galsim.Chromatic(mono_gal, bulge_SED)
    chromatic_gal.applyShear(e1=bulge_e1, e2=bulge_e2)
    chromatic_gal.applyShear(g1=shear_g1, g2=shear_g2)

    # make chromatic PSF
    mono_PSF = galsim.Moffat(beta=PSF_beta, half_light_radius=PSF_hlr)
    chromatic_PSF = galsim.ChromaticShiftAndDilate(mono_PSF, shift_fn, dilate_fn)
    chromatic_PSF.applyShear(e1=PSF_e1, e2=PSF_e2)

    # final profile
    chromatic_final = galsim.Convolve([chromatic_gal, chromatic_PSF, pixel])
    chromatic_image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    # chromatic_final.draw(filter_wave, filter_throughput, image=chromatic_image)
    chromatic_image = chromatic_final.draw(filter_fn, bluelim, redlim, N, image=chromatic_image)
    # plotme(chromatic_image)

    #-----------
    # comparison
    #-----------

    analytic_flux = galsim.integ.int1d(lambda w: bulge_SED(w) * filter_fn(w), bluelim, redlim)
    peak1 = chromatic_image.array.max()

    printval(GS_image, chromatic_image)
    np.testing.assert_array_almost_equal(
        chromatic_image.array/peak1, GS_image.array/peak1, 3,
        err_msg="Directly computed chromatic image disagrees with image created using "
                +"galsim.chromatic")
    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_draw2():
    import time
    t1 = time.time()

    pixel_scale = 0.1
    stamp_size = 64

    # stars are fundamentally delta-fns with an SED
    star = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), bulge_SED)
    pix = galsim.Pixel(pixel_scale)
    mono_PSF = galsim.Gaussian(half_light_radius=PSF_hlr)
    PSF = galsim.ChromaticShiftAndDilate(mono_PSF,
                                         dilate_fn=lambda w:(w/500.0)**(-0.2))

    final = galsim.Convolve([star, PSF, pix])
    image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)

    image = galsim.ChromaticObject.draw(final, filter_fn, bluelim, redlim, 100, image=image)
    draw_flux = image.array.sum()

    image2 = image.copy()
    image2 = galsim.ChromaticObject.draw2(final, filter_fn, bluelim, redlim, 100, image=image2)
    draw2_flux = image2.array.sum()

    #compare
    np.testing.assert_array_almost_equal(
        image.array, image2.array, 5,
        err_msg="draw not equivalent to draw2")

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def compare_integrators():
    import galsim.integ
    import time

    pixel_scale = 0.1
    stamp_size = 64

    # stars are fundamentally delta-fns with an SED
    star = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), bulge_SED)
    pix = galsim.Pixel(pixel_scale)
    mono_PSF = galsim.Gaussian(half_light_radius=PSF_hlr)
    PSF = galsim.ChromaticShiftAndDilate(mono_PSF,
                                         dilate_fn=lambda w:(w/500.0)**(-0.2))

    final = galsim.Convolve([star, PSF, pix])
    image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)

    t1 = time.time()
    print 'midpoint'
    for N in [100, 200, 300, 400, 500, 998, 5000]:
        image = galsim.ChromaticObject.draw2(final, filter_fn, bluelim, redlim, N, image=image)
        print '{:04d} {:14.11f}'.format(N, image.array.sum())
    t2 = time.time()
    print 'time for midpoint = %.2f'%(t2-t1)

    print 'trapezoidal'
    for N in [100, 200, 300, 400, 500, 998, 5000]:
        image = galsim.ChromaticObject.draw2(final, filter_fn, bluelim, redlim, N, image=image,
                                             integrator = galsim.integ.trapezoidal_int_image)
        print '{:04d} {:14.11f}'.format(N, image.array.sum())
    t3 = time.time()
    print 'time for trapezoidal = %.2f'%(t3-t2)

    print 'Simpson\'s'
    for N in [100, 200, 300, 400, 500, 998, 5000]:
        image = galsim.ChromaticObject.draw2(final, filter_fn, bluelim, redlim, N, image=image,
                                             integrator = galsim.integ.simpsons_int_image)
        print '{:04d} {:14.11f}'.format(N, image.array.sum())
    t4 = time.time()
    print 'time for simpsons = %.2f'%(t4-t3)

def test_chromatic_add():
    """Test the `+` operator on ChromaticObjects"""
    import time
    t1 = time.time()

    stamp_size = 32
    pixel_scale = 0.2

    # create galaxy profiles
    mono_bulge = galsim.Sersic(n=bulge_n, half_light_radius=bulge_hlr)
    bulge = galsim.Chromatic(mono_bulge, bulge_SED)
    bulge.applyShear(e1=bulge_e1, e2=bulge_e2)

    mono_disk = galsim.Sersic(n=disk_n, half_light_radius=disk_hlr)
    disk = galsim.Chromatic(mono_disk, disk_SED)
    disk.applyShear(e1=disk_e1, e2=disk_e2)

    # test `+` operator
    bdgal = bulge + disk
    bdgal.applyShear(g1=shear_g1, g2=shear_g2)

    # create PSF
    shift_fn = lambda w:(0, (galsim.dcr.get_refraction(w, zenith_angle) - R610) / galsim.arcsec)
    dilate_fn = lambda w:(w/500.0)**(-0.2)
    mono_PSF = galsim.Moffat(beta=PSF_beta, half_light_radius=PSF_hlr)
    chromatic_PSF = galsim.ChromaticShiftAndDilate(mono_PSF, shift_fn, dilate_fn)
    chromatic_PSF.applyShear(e1=PSF_e1, e2=PSF_e2)

    # create final profile
    pixel = galsim.Pixel(pixel_scale)
    final = galsim.Convolve([bdgal, chromatic_PSF, pixel])
    image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    # final.draw(filter_wave, filter_throughput, image=image)
    image = final.draw(filter_fn, bluelim, redlim, 100, image=image)

    bulge_image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    bulge_part = galsim.Convolve([bulge, chromatic_PSF, pixel])
    # bulge_part.draw(filter_wave, filter_throughput, image=bulge_image)
    bulge_image = bulge_part.draw(filter_fn, bluelim, redlim, 100, image=bulge_image)
    disk_image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    disk_part = galsim.Convolve([disk, chromatic_PSF, pixel])
    # disk_part.draw(filter_wave, filter_throughput, image=disk_image)
    disk_image = disk_part.draw(filter_fn, bluelim, redlim, 100, image=disk_image)

    piecewise_image = bulge_image + disk_image
    printval(image, piecewise_image)
    np.testing.assert_array_almost_equal(
            image.array, piecewise_image.array, 6,
            err_msg="`+` operator doesn't match manual image addition")

    # also test the `+=` operator
    bdgal2 = bulge
    bdgal2 += disk
    final2 = galsim.Convolve([bdgal2, chromatic_PSF, pixel])
    image2 = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    # final2.draw(filter_wave, filter_throughput, image=image2)
    image2 = final2.draw(filter_fn, bluelim, redlim, 100, image=image2)

    printval(image2, piecewise_image)
    np.testing.assert_array_almost_equal(
            image2.array, piecewise_image.array, 6,
            err_msg="`+=` operator doesn't match manual image addition")
    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_dcr_moments():
    """Check that zenith-direction surface brightness distribution first and second moments obey
    expected behavior for differential chromatic refraction when comparing objects drawn with
    different SEDs."""

    import time
    t1 = time.time()

    stamp_size = 256
    pixel_scale = 0.025

    # stars are fundamentally delta-fns with an SED
    star1 = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), bulge_SED)
    star2 = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), disk_SED)

    shift_fn = lambda w:(0, ((galsim.dcr.get_refraction(w, zenith_angle) - R610)
                             / galsim.arcsec))
    mono_PSF = galsim.Moffat(beta=PSF_beta, half_light_radius=PSF_hlr)
    PSF = galsim.ChromaticShiftAndDilate(mono_PSF,shift_fn = shift_fn)

    pix = galsim.Pixel(pixel_scale)
    final1 = galsim.Convolve([star1, PSF, pix])
    final2 = galsim.Convolve([star2, PSF, pix])

    image1 = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
    image2 = galsim.ImageD(stamp_size, stamp_size, pixel_scale)

    # final1.draw(filter_wave, filter_throughput, image=image1)
    # final2.draw(filter_wave, filter_throughput, image=image2)
    image1 = final1.draw(filter_fn, bluelim, redlim, 100, image=image1)
    image2 = final2.draw(filter_fn, bluelim, redlim, 100, image=image2)
    # plotme(image1)

    mom1 = getmoments(image1)
    mom2 = getmoments(image2)
    dR_image = (mom1[1] - mom2[1]) * pixel_scale
    dV_image = (mom1[3] - mom2[3]) * (pixel_scale)**2

    # analytic first moment differences
    R = lambda w:(galsim.dcr.get_refraction(w, zenith_angle) - R610) / galsim.arcsec
    numR1 = galsim.integ.int1d(lambda w: R(w) * filter_fn(w) * bulge_SED(w), bluelim, redlim)
    numR2 = galsim.integ.int1d(lambda w: R(w) * filter_fn(w) * disk_SED(w), bluelim, redlim)
    den1 = galsim.integ.int1d((lambda w:filter_fn(w) * bulge_SED(w)), bluelim, redlim)
    den2 = galsim.integ.int1d((lambda w:filter_fn(w) * disk_SED(w)), bluelim, redlim)

    R1 = numR1/den1
    R2 = numR2/den2
    dR_analytic = R1 - R2

    # analytic second moment differences
    V1_kernel = lambda w:(R(w) - R1)**2
    V2_kernel = lambda w:(R(w) - R2)**2
    numV1 = galsim.integ.int1d(lambda w:V1_kernel(w) * filter_fn(w) * bulge_SED(w), bluelim, redlim)
    numV2 = galsim.integ.int1d(lambda w:V2_kernel(w) * filter_fn(w) * disk_SED(w), bluelim, redlim)
    V1 = numV1/den1
    V2 = numV2/den2
    dV_analytic = V1 - V2

    print 'image delta R:    {}'.format(dR_image)
    print 'analytic delta R: {}'.format(dR_analytic)
    print 'image delta V:    {}'.format(dV_image)
    print 'analytic delta V: {}'.format(dV_analytic)
    np.testing.assert_almost_equal(dR_image, dR_analytic, 5,
                                   err_msg="Moment Shift from DCR doesn't match analytic formula")
    np.testing.assert_almost_equal(dV_image, dV_analytic, 5,
                                   err_msg="Moment Shift from DCR doesn't match analytic formula")


    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_chromatic_seeing_moments():
    """Check that surface brightness distribution second moments obey expected behavior
    for chromatic seeing when comparing stars drawn with different SEDs."""

    import time
    t1 = time.time()

    pixel_scale = 0.0075
    stamp_size = 1024

    # stars are fundamentally delta-fns with an SED
    star1 = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), bulge_SED)
    star2 = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), disk_SED)
    pix = galsim.Pixel(pixel_scale)

    indices = [-0.2, 0.6, 1.0]
    for index in indices:

        mono_PSF = galsim.Gaussian(half_light_radius=PSF_hlr)
        PSF = galsim.ChromaticShiftAndDilate(mono_PSF,
                                             dilate_fn=lambda w:(w/500.0)**index)

        final1 = galsim.Convolve([star1, PSF, pix])
        final2 = galsim.Convolve([star2, PSF, pix])

        image1 = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
        image2 = galsim.ImageD(stamp_size, stamp_size, pixel_scale)

        # final1.draw(filter_wave, filter_throughput, image=image1)
        # final2.draw(filter_wave, filter_throughput, image=image2)
        image1 = final1.draw(filter_fn, bluelim, redlim, 100, image=image1)
        image2 = final2.draw(filter_fn, bluelim, redlim, 100, image=image2)

        mom1 = getmoments(image1)
        mom2 = getmoments(image2)
        dr2byr2_image = ((mom1[2]+mom1[3]) - (mom2[2]+mom2[3])) / (mom1[2]+mom1[3])

        # analytic moment differences
        num1 = galsim.integ.int1d(lambda w:(w/500.0)**(2*index) * filter_fn(w) * bulge_SED(w),
                                  bluelim, redlim)
        num2 = galsim.integ.int1d(lambda w:(w/500.0)**(2*index) * filter_fn(w) * disk_SED(w),
                                  bluelim, redlim)
        den1 = galsim.integ.int1d(lambda w:filter_fn(w) * bulge_SED(w), bluelim, redlim)
        den2 = galsim.integ.int1d(lambda w:filter_fn(w) * disk_SED(w), bluelim, redlim)

        r2_1 = num1/den1
        r2_2 = num2/den2

        dr2byr2_analytic = (r2_1 - r2_2) / r2_1

        np.testing.assert_almost_equal(dr2byr2_image, dr2byr2_analytic, 4,
                                       err_msg="Moment Shift from chromatic seeing doesn't"+
                                               " match analytic formula")

        print 'image delta(r^2) / r^2:    {}'.format(dr2byr2_image)
        print 'analytic delta(r^2) / r^2: {}'.format(dr2byr2_analytic)

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_monochromatic_filter():
    """Check that ChromaticObject drawn through a very narrow band filter matches analogous
    GSObject.
    """

    import time
    t1 = time.time()

    pixel_scale = 0.2
    stamp_size = 32

    chromatic_gal = galsim.Chromatic(galsim.Gaussian(fwhm=1.0), bulge_SED)
    GS_gal = galsim.Gaussian(fwhm=1.0)

    shift_fn = lambda w:(0, (galsim.dcr.get_refraction(w, zenith_angle) - R610) / galsim.arcsec)
    dilate_fn = lambda wave: (wave/500.0)**(-0.2)
    mono_PSF = galsim.Gaussian(half_light_radius=PSF_hlr)
    chromatic_PSF = galsim.ChromaticShiftAndDilate(mono_PSF, shift_fn, dilate_fn)
    chromatic_PSF.applyShear(e1=PSF_e1, e2=PSF_e2)

    pix = galsim.Pixel(pixel_scale)
    chromatic_final = galsim.Convolve([chromatic_gal, chromatic_PSF, pix])

    fws = [350, 475, 625, 750, 875, 975] # approximage ugrizy filter central wavelengths
    for fw in fws:
        chromatic_image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
        chromatic_image = chromatic_final.draw(lambda x:1.0, fw-0.01, fw+0.01, 1,
                                               image=chromatic_image)
        # take out normalization
        chromatic_image /= 0.02
        chromatic_image /= bulge_SED(fw)

        # now do non-chromatic version
        GS_PSF = galsim.Gaussian(half_light_radius=PSF_hlr)
        GS_PSF.applyShear(e1=PSF_e1, e2=PSF_e2)
        GS_PSF.applyDilation(dilate_fn(fw))
        GS_PSF.applyShift(shift_fn(fw))
        GS_final = galsim.Convolve([GS_gal, GS_PSF, pix])
        GS_image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)
        GS_final.draw(image=GS_image)
        # plotme(GS_image)

        printval(chromatic_image, GS_image)
        np.testing.assert_array_almost_equal(chromatic_image.array, GS_image.array, 5,
                err_msg="ChromaticObject.draw() with monochromatic filter doesn't match"+
                        "GSObject.draw()")

        getmoments(GS_image)
    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

def test_chromatic_flux():
    import time
    t1 = time.time()

    pixel_scale = 0.1
    stamp_size = 64

    # stars are fundamentally delta-fns with an SED
    star = galsim.Chromatic(galsim.Gaussian(fwhm=1e-8), bulge_SED)
    pix = galsim.Pixel(pixel_scale)
    mono_PSF = galsim.Gaussian(half_light_radius=PSF_hlr)
    PSF = galsim.ChromaticShiftAndDilate(mono_PSF,
                                         dilate_fn=lambda w:(w/500.0)**(-0.2))

    final = galsim.Convolve([star, PSF, pix])
    image = galsim.ImageD(stamp_size, stamp_size, pixel_scale)

    image = final.draw(filter_fn, bluelim, redlim, 100, image=image)
    ChromaticConvolve_flux = image.array.sum()

    image = galsim.ChromaticObject.draw(final, filter_fn, bluelim, redlim, 100, image=image)
    ChromaticObject_flux = image.array.sum()

    # analytic integral...
    analytic_flux = galsim.integ.int1d(lambda w: bulge_SED(w) * filter_fn(w), bluelim, redlim)

    np.testing.assert_almost_equal(ChromaticObject_flux/analytic_flux, 1.0, 5,
                                   err_msg="Drawn ChromaticObject flux doesn't match " +
                                   "analytic prediction")
    np.testing.assert_almost_equal(ChromaticConvolve_flux/analytic_flux, 1.0, 5,
                                   err_msg="Drawn ChromaticConvolve flux doesn't match " +
                                   "analytic prediction")

    t2 = time.time()
    print 'time for %s = %.2f'%(funcname(),t2-t1)

if __name__ == "__main__":
    # test_direct_sum_vs_chromatic()
    # test_chromatic_add()
    # test_dcr_moments()
    # test_chromatic_seeing_moments()
    # test_monochromatic_filter()
    # test_chromatic_flux()
    # test_draw2()
    compare_integrators()
