/* -*- c++ -*-
 * Copyright (c) 2012-2015 by the GalSim developers team on GitHub
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

#ifndef GalSim_Table_H
#define GalSim_Table_H

#include <vector>
#include <algorithm>
#include <string>
#include <sstream>
#include <stdexcept>
#include <iostream>
#include <functional>

#include "Std.h"
#include "OneDimensionalDeviate.h"

namespace galsim {

    // All code between the @cond and @endcond is excluded from Doxygen documentation
    //! @cond

    /// @brief Basic exception class thrown by Table
    class TableError : public std::runtime_error
    {
    public:
        TableError(const std::string& m) : std::runtime_error("Table Error: " +m) {}
    };

    /// @brief Exception class for Table access ouside the allowed range
    class TableOutOfRange : public TableError
    {
        template <typename A>
        static std::string BuildErrorMessage(A val, A min, A max)
        {
            // See discussion in Std.h about this initial value.
            std::ostringstream oss(" ");
            oss << "Argument "<<val<<" out of range ("<<min<<".."<<max<<")";
            return oss.str();
        }
    public:
        template <typename A>
        TableOutOfRange(A val, A min, A max) :
            TableError(BuildErrorMessage(val,min,max)) {}
    };

    /// @brief Exception class for I/O errors when reading in a Table
    class TableReadError : public TableError
    {
    public:
        TableReadError(const std::string& c) : TableError("Data read error for line ->"+c) {}
    };

    //! @endcond

    /**
     * @brief A single entry in a Table including an argument and an value.
     *
     * There are two template arguments:
     * A is the type of the argument
     * V is the type of the value
     */
    template<class V, class A>
    class TableEntry
    {
    public:
        TableEntry(A a, V v) : arg(a), val(v) {}
        A arg;
        V val;
        bool operator==(const TableEntry rhs) const { return arg==rhs.arg; }
        bool operator==(const A rhs) const { return arg==rhs; }
        bool operator!=(const TableEntry rhs) const { return arg!=rhs.arg; }
        bool operator!=(const A rhs) const { return arg!=rhs; }
        bool operator>(const TableEntry rhs) const { return arg>rhs.arg; }
        bool operator>(const A rhs) const { return arg>rhs; }
        bool operator<(const TableEntry rhs) const { return arg<rhs.arg; }
        bool operator<(const A rhs) const { return arg<rhs; }
        bool operator<=(const TableEntry rhs) const { return arg<=rhs.arg; }
        bool operator<=(const A rhs) const { return arg>=rhs; }
        bool operator>=(const TableEntry rhs) const { return arg>=rhs.arg; }
        bool operator>=(const A rhs) const { return arg>=rhs; }
    };

    /**
     * @brief A class to represent lookup tables for a function y = f(x).
     *
     * A is the type of the argument of the function.
     * V is the type of the value of the function.
     *
     * Requirements for A,V:
     *   A must have ordering operators (< > ==) and the normal arithmetic ops (+ - * /)
     *   V must have + and *.
     */
    template<class V, class A>
    class Table
    {
    public:
        enum interpolant { linear, spline, floor, ceil };

        /// Construct empty table
        Table(interpolant i) : iType(i), isReady(false) {}

        /// Table from two arrays:
        Table(const A* argvec, const V* valvec, int N, interpolant in);
        Table(const std::vector<A>& a, const std::vector<V>& v, interpolant in);

        Table(std::istream& is, interpolant in) : iType(in), isReady(false)
        { read(is); }

        void clear() { v.clear(); isReady=false; }
        void read(std::istream& is);

        /// new element for table.
        void addEntry(const A a, const V v);

        /// lookup & interp. function value.
        V operator() (const A a) const;

        /// interp, but exception if beyond bounds
        V lookup(const A a) const;

        /// interp many values at once.
        void interpMany(const A* argvec, V* valvec, int N) const;

        /// size of table
        int size() const { return v.size(); }

        /// Smallest argument
        A argMin() const
        {
            setup();
            return _argMin();
        }

        /// Largest argument
        A argMax() const
        {
            setup();
            return _argMax();
        }

        template <class T>
        void TransformVal(T& xfrm)
        {
            for (iter p=v.begin(); p!=v.end(); ++p) p->val = xfrm(p->arg, p->val);
            isReady=false; setup();
        }

        template <class T>
        void TransformArg(T& xfrm)
        {
            for (iter p=v.begin(); p!=v.end(); ++p)
                p->arg = xfrm(p->arg, p->val);
            isReady=false; setup();
        }

        void dump() const
        {
            setup();
            for (citer p=v.begin(); p!=v.end(); ++p)
                std::cout << p->arg << " " << p->val << std::endl;
        }

        typedef TableEntry<V,A> Entry;
        const std::vector<Entry>& getV() const { return v; }
        interpolant getInterp() const { return iType; }

    private:
        typedef typename std::vector<Entry>::const_iterator citer;
        typedef typename std::vector<Entry>::iterator iter;

        interpolant iType;
        mutable bool isReady; //< Flag if table has been prepped.
        mutable bool equalSpaced; //< Flag set if arguments are nearly equally spaced.
        mutable A dx; //<  ...in which case this is argument interval
        mutable int lastIndex; //< Index for last lookup into table.
        mutable A lower_slop; // tolerance for lower argument
        mutable A upper_slop; // tolerance for upper argument

        mutable std::vector<Entry> v;
        mutable std::vector<V> y2; //< vector of 2nd derivs for spline

        //@{
        /// Private versions that don't check for a null table:
        A _argMin() const { return v.front().arg; }
        A _argMax() const { return v.back().arg; }
        //@}

        /// get index to 1st element >= argument.  Can throw the exception here.
        int upperIndex(const A a) const;

        void sortIt() const { std::sort(v.begin(), v.end()); }
        void setup() const; //< Do any necessary preparation;
        void setupSpline() const; //<  Calculate the y2 vector

        /// Interpolate value btwn p & --p:
        mutable V (*interpolate)(A a, int i, const std::vector<Entry>& v,
                                 const std::vector<V>& y2);

        static V linearInterpolate(A a, int i, const std::vector<Entry>& v,
                                   const std::vector<V>& y2);
        static V splineInterpolate(A a, int i, const std::vector<Entry>& v,
                                   const std::vector<V>& y2);
        static V floorInterpolate(A a, int i, const std::vector<Entry>& v,
                                  const std::vector<V>& y2);
        static V ceilInterpolate(A a, int i, const std::vector<Entry>& v,
                                 const std::vector<V>& y2);
    };

    /**
     * @brief Table<double,double> works as a FluxDensity for OneDimensionalDeviate,
     *        so specialize to add the FluxDensity functionality.
     */
    class TableDD:
        public Table<double,double>,
        public FluxDensity
    {
    public:
        //@{
        /// Constructors just use Table constructors:
        TableDD(interpolant i) : Table<double,double>(i) {}
        TableDD(const double* argvec, const double* valvec, int N, interpolant in) :
            Table<double,double>(argvec,valvec,N,in) {}
        TableDD(const std::vector<double>& a, const std::vector<double>& v,
                interpolant in=linear) : Table<double,double>(a,v,in) {}
        TableDD(std::istream& is, interpolant in) : Table<double,double>(is,in) {}
        //@}

        /// Virtual function from FluxDensity just calls Table version.
        double operator()(double a) const { return Table<double,double>::operator()(a); }
    };

    /**
     * @brief A class to represent an argument grid for a Table2D.
     *
     * Basically a std::vector with a few extra bells and whistles to deal with potentially
     * equally-spaced arguments, upper and lower slop, and fast indexing.
     */
    template<class A>
    class ArgGrid
    {
    public:
        ArgGrid(const A* args, int N);

        int upperIndex(const A a) const;

        // pass through a few std::vector methods.
        const A& front() const {return grid.front();}
        const A& back() const {return grid.back();}
        const A& operator[](int i) const {return grid[i];}

        // A few convenient additional member variables.
        A lower_slop, upper_slop;
        bool equalSpaced;
        A da;
        mutable int lastIndex;

        const std::vector<A>& getGrid() const { return grid; }

    private:
        typedef typename std::vector<A>::const_iterator citer;
        std::vector<A> grid;
    };

    /**
     * @brief A class to represent lookup tables for a function z = f(x, y).
     *
     * A is the type of the argument of the function.
     * V is the type of the value of the function.
     *
     * Requirements for A,V:
     *   A must have ordering operators (< > ==) and the normal arithmetic ops (+ - * /)
     *   V must have + and *.
     */
    template<class V, class A>
    class Table2D
    {
    public:
        enum interpolant { linear, floor, ceil, nearest };

        /// Table from xargs, yargs, vals
        Table2D(const A* xargs, const A* yargs, const V* valarray, int Nx, int Ny, interpolant in);

        A xmin() const {return xgrid.front();}
        A xmax() const {return xgrid.back();}
        A ymin() const {return ygrid.front();}
        A ymax() const {return ygrid.back();}

        /// interp, but exception if beyond bounds
        V lookup(const A x, const A y) const;

        /// interp many values at once
        void interpManyScatter(const A* xvec, const A* yvec, V* valvec, int N) const;
        void interpManyOuter(const A* xvec, const A* yvec, V* valvec, int Nx, int Ny) const;

        const std::vector<A>& getXArgs() const { return xgrid.getGrid(); }
        const std::vector<A>& getYArgs() const { return ygrid.getGrid(); }
        const std::vector<V>& getVals() const { return vals; }
        int getNx() const {return Nx;}
        int getNy() const {return Ny;}
        interpolant getInterp() const { return iType; }

    private:
        interpolant iType;
        const int Nx, Ny; // Array dimensions
        const ArgGrid<A> xgrid;
        const ArgGrid<A> ygrid;

        std::vector<V> vals;

        typedef V (Table2D<V,A>::*Table2DMemFn)(const A x, const A y, int i, int j) const;
        Table2DMemFn interpolate;
        V linearInterpolate(const A x, const A y, int i, int j) const;
        V floorInterpolate(const A x, const A y, int i, int j) const;
        V ceilInterpolate(const A x, const A y, int i, int j) const;
        V nearestInterpolate(const A x, const A y, int i, int j) const;
    };
}

#endif
