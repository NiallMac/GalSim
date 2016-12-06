/* -*- c++ -*-
 * Copyright (c) 2012-2016 by the GalSim developers team on GitHub
 * https://github.com/GalSim-developers
 *
 * This file is part of GalSim: The modular galaxy image simulation toolkit.
 * https://github.com/GalSim-developers/GalSim
 *
 * GalSim is free software: redistribution and use in source and binary forms,
 * with or without modification, are permitted provided that the following
 * conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions, and the disclaimer given in the accompanying LICENSE
 *    file.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions, and the disclaimer given in the documentation
 *    and/or other materials provided with the distribution.
 */

//#define DEBUGLOGGING

#include "galsim/IgnoreWarnings.h"

#define BOOST_NO_CXX11_SMART_PTR

#include "SBInclinedSersic.h"
#include "SBInclinedSersicImpl.h"
#include "integ/Int.h"
#include "Solve.h"

namespace galsim {

    SBInclinedSersic::SBInclinedSersic(double n, Angle inclination, double size, double height,
            SBInclinedSersic::RadiusType rType, double flux,
            double trunc, bool flux_untruncated, const GSParamsPtr& gsparams) :
        SBProfile(new SBInclinedSersicImpl(n, inclination, size, height, rType, flux, trunc,
                flux_untruncated, gsparams)) {}

    SBInclinedSersic::SBInclinedSersic(const SBInclinedSersic& rhs) : SBProfile(rhs) {}

    SBInclinedSersic::~SBInclinedSersic() {}

    double SBInclinedSersic::getN() const
    {
        assert(dynamic_cast<const SBInclinedSersicImpl*>(_pimpl.get()));
        return static_cast<const SBInclinedSersicImpl&>(*_pimpl).getN();
    }

    Angle SBInclinedSersic::getInclination() const
    {
        assert(dynamic_cast<const SBInclinedSersicImpl*>(_pimpl.get()));
        return static_cast<const SBInclinedSersicImpl&>(*_pimpl).getInclination();
    }

    double SBInclinedSersic::getHalfLightRadius() const
    {
        assert(dynamic_cast<const SBInclinedSersicImpl*>(_pimpl.get()));
        return static_cast<const SBInclinedSersicImpl&>(*_pimpl).getHalfLightRadius();
    }

    double SBInclinedSersic::getScaleRadius() const
    {
        assert(dynamic_cast<const SBInclinedSersicImpl*>(_pimpl.get()));
        return static_cast<const SBInclinedSersicImpl&>(*_pimpl).getScaleRadius();
    }

    double SBInclinedSersic::getScaleHeight() const
    {
        assert(dynamic_cast<const SBInclinedSersicImpl*>(_pimpl.get()));
        return static_cast<const SBInclinedSersicImpl&>(*_pimpl).getScaleHeight();
    }

    double SBInclinedSersic::getTrunc() const
    {
        assert(dynamic_cast<const SBInclinedSersicImpl*>(_pimpl.get()));
        return static_cast<const SBInclinedSersicImpl&>(*_pimpl).getTrunc();
    }

    // NB.  This function is virtually wrapped by repr() in SBProfile.cpp
    std::string SBInclinedSersic::SBInclinedSersicImpl::serialize() const
    {
        std::ostringstream oss(" ");
        // NB. The choice of digits10 + 4 is because the normal general output
        // scheme for double uses fixed notation if >= 0.0001, but then switches
        // to scientific for smaller numbers.  So those first 4 digits in 0.0001 don't
        // count for the number of required digits, which is nominally given by digits10.
        // cf. http://stackoverflow.com/questions/4738768/printing-double-without-losing-precision
        // Unfortunately, there doesn't seem to be an easy equivalent of python's %r for
        // printing the repr of a double that always works and doesn't print more digits than
        // it needs.  This is the reason why we reimplement the __repr__ methods in python
        // for all the SB classes except SBProfile.  Only the last one can't be done properly
        // in python, so it will use the C++ virtual function to get the right thing for
        // any subclass.  But possibly with ugly extra digits.
        oss.precision(std::numeric_limits<double>::digits10 + 4);
        oss << "galsim._galsim.SBInclinedSersic("<<getN()<<", "<<getInclination()<<", "<<getScaleRadius();
        oss <<", "<<getScaleHeight()<<", None, "<<getFlux()<<", "<<getTrunc()<<", False";
        oss << ", galsim.GSParams("<<*gsparams<<"))";
        return oss.str();
    }

    LRUCache< boost::tuple<double, double, GSParamsPtr >, SersicInfo >
        SBInclinedSersic::SBInclinedSersicImpl::cache(sbp::max_sersic_cache);

    SBInclinedSersic::SBInclinedSersicImpl::SBInclinedSersicImpl(double n, Angle inclination, double size,
                                         double height, RadiusType rType, double flux,
                                         double trunc, bool flux_untruncated,
                                         const GSParamsPtr& gsparams) :
        SBProfileImpl(gsparams),
        _n(n),
        _inclination(inclination),
        _h0(height),
        _flux(flux),
        _trunc(trunc),
        _trunc_sq(trunc*trunc),
        _cosi(std::abs(inclination.cos())),
        _ksq_max(integ::MOCK_INF), // Start with infinite _ksq_max so we can use kValueHelper to
                                  // get a better value
        // Start with untruncated SersicInfo regardless of value of trunc
        _info(cache.get(boost::make_tuple(_n, 0., this->gsparams.duplicate())))
    {
        dbg<<"Start SBInclinedSersic constructor:\n";
        dbg<<"n = "<<_n<<std::endl;
        dbg<<"inclination = "<<_inclination<<std::endl;
        dbg<<"size = "<<size<<"  rType = "<<rType<<std::endl;
        dbg<<"scale height = "<<_h0<<std::endl;
        dbg<<"flux = "<<_flux<<std::endl;
        dbg<<"trunc = "<<_trunc<<"  flux_untruncated = "<<flux_untruncated<<std::endl;

        _truncated = (_trunc > 0.);

        // Set size of this instance according to type of size given in constructor
        switch (rType) {
          case HALF_LIGHT_RADIUS:
               {
                   _re = size;
                   if (_truncated) {
                       if (flux_untruncated) {
                           // Then given HLR and flux are the values for the untruncated profile.
                           _r0 = _re / _info->getHLR(); // getHLR() is in units of r0.
                       } else {
                           // This is the one case that is a bit complicated, since the
                           // half-light radius and trunc are both given in physical units,
                           // so we need to solve for what scale radius this corresponds to.
                           _r0 = _info->calculateScaleForTruncatedHLR(_re, _trunc);
                       }

                       // Update _info with the correct truncated version.
                       _info = cache.get(boost::make_tuple(_n,_trunc/_r0,
                                                           this->gsparams.duplicate()));

                       if (flux_untruncated) {
                           // Update the stored _flux and _re with the correct values
                           _flux *= _info->getFluxFraction();
                           _re = _r0 * _info->getHLR();
                       }
                   } else {
                       // Then given HLR and flux are the values for the untruncated profile.
                       _r0 = _re / _info->getHLR();
                   }
               }
               break;
          case SCALE_RADIUS:
               {
                   _r0 = size;
                   if (_truncated) {
                       // Update _info with the correct truncated version.
                       _info = cache.get(boost::make_tuple(_n,_trunc/_r0,
                                                           this->gsparams.duplicate()));

                       if (flux_untruncated) {
                           // Update the stored _flux with the correct value
                           _flux *= _info->getFluxFraction();
                       }
                   }
                   // In all cases, _re is the real HLR
                   _re = _r0 * _info->getHLR();
               }
               break;
          default:
               throw SBError("Unknown SBInclinedSersic::RadiusType");
        }
        dbg<<"hlr = "<<_re<<std::endl;
        dbg<<"r0 = "<<_r0<<std::endl;

        _inv_r0 = 1./_r0;
        _half_pi_h_sini_over_r = 0.5*M_PI*_h0*std::abs(_inclination.sin())/_r0,

        _r0_sq = _r0*_r0;
        _inv_r0 = 1./_r0;
        _inv_r0_sq = _inv_r0*_inv_r0;

        _shootnorm = _flux * _info->getXNorm(); // For shooting, we don't need the 1/r0^2 factor.
        _xnorm = _shootnorm * _inv_r0_sq;
        dbg<<"norms = "<<_xnorm<<", "<<_shootnorm<<std::endl;

        // Solve for the proper _maxk and _ksq_max

        double maxk_min = std::pow(this->gsparams->maxk_threshold, -1./3.);
        double clipk_min = std::pow(this->gsparams->kvalue_accuracy, -1./3.);

        // Check for face-on exponential case, which doesn't need the solver
        if(_cosi==1 and _n==1)
        {
            _maxk = maxk_min;
            _ksq_max = clipk_min*clipk_min;
        }
        else // Use the solver
        {
            // Bracket it appropriately, starting with guesses based on the 1/cosi scaling
            double maxk_max, clipk_max;
            // Check bounds on _cosi to make sure initial guess range isn't too big or small
            if(_cosi>0.01)
            {
                if(_cosi<0.96)
                {
                    maxk_max = maxk_min/_cosi;
                    clipk_max = clipk_min/_cosi;
                }
                else
                {
                    maxk_max = 1.05*maxk_min;
                    clipk_max = 1.05*clipk_min;
                }
            }
            else
            {
                maxk_max = 100*maxk_min;
                clipk_max = 100*clipk_min;
            }

            xdbg << "maxk_threshold = " << this->gsparams->maxk_threshold << std::endl;
            xdbg << "F(" << maxk_min << ") = " << std::max(kValueHelper(maxk_min,0.),kValueHelper(0.,maxk_min)) << std::endl;
            xdbg << "F(" << maxk_max << ") = " << std::max(kValueHelper(maxk_max,0.),kValueHelper(0.,maxk_max)) << std::endl;

            SBInclinedSersicKValueFunctor maxk_func(this,this->gsparams->maxk_threshold);
            Solve<SBInclinedSersicKValueFunctor> maxk_solver(maxk_func, maxk_min, maxk_max);
            maxk_solver.setMethod(Brent);

            if(maxk_func(maxk_min)<=0)
                maxk_solver.bracketLowerWithLimit(0.);
            else
                maxk_solver.bracketUpper();

            // Get the _maxk from the solver here. We add back on the tolerance to the result to
            // ensure that the k-value will be below the threshold.
            _maxk = maxk_solver.root() + maxk_solver.getXTolerance();

            xdbg << "_maxk = " << _maxk << std::endl;
            xdbg << "F(" << _maxk << ") = " << kValueHelper(0.,_maxk) << std::endl;

            xdbg << "kvalue_accuracy = " << this->gsparams->kvalue_accuracy << std::endl;
            xdbg << "F(" << clipk_min << ") = " << kValueHelper(0.,clipk_min) << std::endl;
            xdbg << "F(" << clipk_max << ") = " << kValueHelper(0.,clipk_max) << std::endl;

            SBInclinedSersicKValueFunctor clipk_func(this,this->gsparams->kvalue_accuracy);
            Solve<SBInclinedSersicKValueFunctor> clipk_solver(clipk_func, clipk_min, clipk_max);

            if(clipk_func(clipk_min)<=0)
                clipk_solver.bracketLowerWithLimit(0.);
            else
                clipk_solver.bracketUpper();

            // Get the clipk from the solver here. We add back on the tolerance to the result to
            // ensure that the k-value will be below the threshold.
            double clipk = clipk_solver.root() + clipk_solver.getXTolerance();
            _ksq_max = clipk*clipk;

            xdbg << "clipk = " << clipk << std::endl;
            xdbg << "F(" << clipk << ") = " << kValueHelper(0.,clipk) << std::endl;
        }
    }

    double SBInclinedSersic::SBInclinedSersicImpl::xValue(const Position<double>& p) const
    {
        throw std::runtime_error(
            "Real-space expression of SBInclinedSersic is not yet implemented.");
        return 0;
    }

    std::complex<double> SBInclinedSersic::SBInclinedSersicImpl::kValue(const Position<double>& k) const
    {
        double kx = k.x*_r0;
        double ky = k.y*_r0;
        return _flux * kValueHelper(kx,ky);
    }

    void SBInclinedSersic::SBInclinedSersicImpl::fillKImage(ImageView<std::complex<double> > im,
                                                double kx0, double dkx, int izero,
                                                double ky0, double dky, int jzero) const
    {
        dbg<<"SBInclinedSersic fillKImage\n";
        dbg<<"kx = "<<kx0<<" + i * "<<dkx<<", izero = "<<izero<<std::endl;
        dbg<<"ky = "<<ky0<<" + j * "<<dky<<", jzero = "<<jzero<<std::endl;
        if (izero != 0 || jzero != 0) {
            xdbg<<"Use Quadrant\n";
            fillKImageQuadrant(im,kx0,dkx,izero,ky0,dky,jzero);
        } else {
            xdbg<<"Non-Quadrant\n";
            const int m = im.getNCol();
            const int n = im.getNRow();
            std::complex<double>* ptr = im.getData();
            int skip = im.getNSkip();
            assert(im.getStep() == 1);

            kx0 *= _r0;
            dkx *= _r0;
            ky0 *= _r0;
            dky *= _r0;

            for (int j=0; j<n; ++j,ky0+=dky,ptr+=skip) {
                double kx = kx0;
                for (int i=0;i<m;++i,kx+=dkx)
                    *ptr++ = _flux * kValueHelper(kx,ky0);
            }
        }
    }

    void SBInclinedSersic::SBInclinedSersicImpl::fillKImage(ImageView<std::complex<double> > im,
                                                double kx0, double dkx, double dkxy,
                                                double ky0, double dky, double dkyx) const
    {
        dbg<<"SBInclinedSersic fillKImage\n";
        dbg<<"kx = "<<kx0<<" + i * "<<dkx<<" + j * "<<dkxy<<std::endl;
        dbg<<"ky = "<<ky0<<" + i * "<<dkyx<<" + j * "<<dky<<std::endl;
        const int m = im.getNCol();
        const int n = im.getNRow();
        std::complex<double>* ptr = im.getData();
        int skip = im.getNSkip();
        assert(im.getStep() == 1);

        kx0 *= _r0;
        dkx *= _r0;
        dkxy *= _r0;
        ky0 *= _r0;
        dky *= _r0;
        dkyx *= _r0;

        for (int j=0; j<n; ++j,kx0+=dkxy,ky0+=dky,ptr+=skip) {
            double kx = kx0;
            double ky = ky0;
            for (int i=0; i<m; ++i,kx+=dkx,ky+=dkyx)
                *ptr++ = _flux * kValueHelper(kx,ky);
        }
    }

    double SBInclinedSersic::SBInclinedSersicImpl::maxK() const { return _info->maxK() * _inv_r0; }
    double SBInclinedSersic::SBInclinedSersicImpl::stepK() const { return _info->stepK() * _inv_r0; }

    double SBInclinedSersic::SBInclinedSersicImpl::kValueHelper(
        double kx, double ky) const
    {
        // Get the base value for a Sersic profile

        double ky_cosi = ky*_cosi;

        double ky_cosi_sq = ky_cosi*ky_cosi;
        double ksq = kx*kx + ky_cosi_sq;
        double res_base;
        if (ksq > _ksq_max)
        {
            return 0.;
        }
        else
        {
            res_base =  _info->kValue(ksq);

            xxdbg << "res_base = " << res_base << std::endl;
        }

        // Calculate the convolution factor
        double res_conv;

        double scaled_ky = _half_pi_h_sini_over_r*ky;
        double scaled_ky_squared = scaled_ky*scaled_ky;

        if (scaled_ky_squared < _ksq_min)
        {
            // Use Taylor expansion to speed up calculation
            res_conv = (1. - 0.16666666667*scaled_ky_squared *
                          (1. - 0.116666666667*scaled_ky_squared));
            xxdbg << "res_conv (lower limit) = " << res_conv << std::endl;
        }
        else
        {
            res_conv = scaled_ky / std::sinh(scaled_ky);
            xxdbg << "res_conv (normal) = " << res_conv << std::endl;
        }


        double res = res_base*res_conv;

        return res;
    }

    boost::shared_ptr<PhotonArray> SBInclinedSersic::SBInclinedSersicImpl::shoot(int N, UniformDeviate ud) const
    {
        throw std::runtime_error(
            "Photon shooting not yet implemented for SBInclinedSersic profile.");
    }

    SBInclinedSersic::SBInclinedSersicImpl::
        SBInclinedSersicKValueFunctor::SBInclinedSersicKValueFunctor(
            const SBInclinedSersic::SBInclinedSersicImpl * p_owner,
            double target_k_value) :
        _p_owner(p_owner), _target_k_value(target_k_value)
    {}

    double SBInclinedSersic::SBInclinedSersicImpl::
        SBInclinedSersicKValueFunctor::operator()(double k) const
    {
        assert(_p_owner);
        double k_value = std::max(_p_owner->kValueHelper(0.,k),_p_owner->kValueHelper(k,0.));
        return k_value - _target_k_value;
    }
}
