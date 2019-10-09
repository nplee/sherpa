#
#  Copyright (C) 2019  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Basic tests of the plot functionality in sherpa.astro.ui.

It is based on sherpa/ui/tests/test_ui_plot.py, but focusses on the
new routines, and "astro-specific" (currently PHA only) capabilities
that are in the astro layer.

"""

import logging
import numpy as np

from sherpa.astro import ui

# the chips plot tests mean that we can't test the plot instances
# from sherpa.plot import DataPlot, FitPlot, ModelPlot

from sherpa.utils.err import IdentifierErr
from sherpa.utils.testing import requires_plotting

import pytest

_data_chan = np.linspace(1, 10, 10, dtype=np.int8)
_data_counts = np.asarray([0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
                          dtype=np.int8)

_data_bkg = np.asarray([1, 0, 0, 1, 0, 0, 2, 0, 0, 1],
                       dtype=np.int8)

_arf = np.asarray([0.8, 0.8, 0.9, 1.0, 1.1, 1.1, 0.7, 0.6, 0.6, 0.6])

# using a "perfect" RMF, in that there's a one-to-one mapping
# from channel to energy
#
_energies = np.linspace(0.5, 1.5, 11)

# How much longer is the background exposure compared to the source
# exposure; chose a non-integer value to make it more obvious when
# it is being applied (e.g. compared to the scaling ratios applied
# to the backscal values).
#
_bexpscale = 2.5


def example_pha_data():
    """Create an example data set."""

    etime = 1201.0
    d = ui.DataPHA('example', _data_chan.copy(),
                   _data_counts.copy(),
                   exposure=etime,
                   backscal=0.1)

    a = ui.create_arf(_energies[:-1].copy(),
                      _energies[1:].copy(),
                      specresp=_arf.copy(),
                      exposure=etime)

    r = ui.create_rmf(_energies[:-1].copy(),
                      _energies[1:].copy(),
                      e_min=_energies[:-1].copy(),
                      e_max=_energies[1:].copy(),
                      startchan=1,
                      fname=None)

    d.set_arf(a)
    d.set_rmf(r)
    return d


def example_pha_with_bkg_data():
    """Create an example data set with background

    There is no response for the background.
    """

    d = example_pha_data()

    b = ui.DataPHA('example-bkg', _data_chan.copy(),
                   _data_bkg.copy(),
                   exposure=1201.0 * _bexpscale,
                   backscal=0.4)

    d.set_background(b)
    return d


def example_model():
    """Create an example model."""

    ui.create_model_component('const1d', 'cpt')
    cpt = ui.get_model_component('cpt')
    cpt.c0 = 1.02e2
    return cpt


def example_bkg_model():
    """Create an example background model."""

    ui.create_model_component('powlaw1d', 'bcpt')
    bcpt = ui.get_model_component('bcpt')
    bcpt.gamma = 0.0  # use a flat model to make it easy to evaluate
    bcpt.ampl = 1e-1
    return bcpt


def setup_example(idval):
    """Set up a simple dataset for use in the tests.

    A *very basic* ARF is used, along with an ideal RMF. The
    way this is created means the analysis is in channel space
    by default.

    Parameters
    ----------
    idval : None, int, str
        The dataset identifier.

    See Also
    --------
    setup_example_bkg
    """

    d = example_pha_data()
    m = example_model()
    if idval is None:
        ui.set_data(d)
        ui.set_source(m)

    else:
        ui.set_data(idval, d)
        ui.set_source(idval, m)


def setup_example_bkg(idval):
    """Set up a simple dataset + background for use in the tests.

    Parameters
    ----------
    idval : None, int, str
        The dataset identifier.

    See Also
    --------
    setup_example, setup_example_bkg_model
    """

    d = example_pha_with_bkg_data()
    m = example_model()
    if idval is None:
        ui.set_data(d)
        ui.set_source(m)

    else:
        ui.set_data(idval, d)
        ui.set_source(idval, m)


def setup_example_bkg_model(idval):
    """Set up a simple dataset + background for use in the tests.

    This includes a model for the background, unlike
    setup-example_bkg.

    Parameters
    ----------
    idval : None, int, str
        The dataset identifier.

    See Also
    --------
    setup_example_bkg
    """

    d = example_pha_with_bkg_data()
    m = example_model()
    bm = example_bkg_model()
    if idval is None:
        ui.set_data(d)
        ui.set_source(m)
        ui.set_bkg_model(bm)

    else:
        ui.set_data(idval, d)
        ui.set_source(idval, m)
        ui.set_bkg_model(idval, bm)


"""
Functions that could be tested:

plot_model
plot_source
plot_model_component
plot_source_component
plot_order

plot_bkg
plot_bkg_model
plot_bkg_resid
plot_bkg_ratio
plot_bkg_delchi
plot_bkg_chisqr
plot_bkg_fit
plot_bkg_source
plot_bkg_fit_ratio
plot_bkg_fit_resid
plot_bkg_fit_delchi

plot_arf

get_arf_plot                 X
get_bkg_chisqr_plot
get_bkg_delchi_plot
get_bkg_fit_plot             X
get_bkg_model_plot           X
get_bkg_plot                 X
get_bkg_ratio_plot
get_bkg_resid_plot           X
get_bkg_source_plot
get_model_component_plot
get_model_plot               X
get_order_plot
get_source_component_plot
get_source_plot              X

"""


# The following tests do not check whether returned values are
# of the expected class instance, since the chips plot tests
# use a mock object and so mess-up simple "isinstance(x, ModelPlot)"
# checks.
#

@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_arf_plot(idval):
    """Basic testing of get_arf_plot
    """

    setup_example(idval)
    if idval is None:
        ap = ui.get_arf_plot()
    else:
        ap = ui.get_arf_plot(idval)

    assert ap.xlo == pytest.approx(_energies[:-1])
    assert ap.xhi == pytest.approx(_energies[1:])

    assert ap.y == pytest.approx(_arf)

    assert ap.title == 'test-arf'
    assert ap.xlabel == 'Energy (keV)'

    # the y label depends on the backend (due to LaTeX)
    # assert ap.ylabel == 'cm$^2$'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_plot(idval):
    """Basic testing of get_bkg_plot
    """

    setup_example_bkg(idval)
    if idval is None:
        bp = ui.get_bkg_plot()
    else:
        bp = ui.get_bkg_plot(idval)

    assert bp.x == pytest.approx(_data_chan)

    # normalise by exposure time and bin width, but bin width here
    # is 1 (because it is being measured in channels).
    #
    yexp = _data_bkg / 1201.0 / _bexpscale
    assert bp.y == pytest.approx(yexp)

    assert bp.title == 'example-bkg'
    assert bp.xlabel == 'Channel'
    assert bp.ylabel == 'Counts/sec/channel'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_plot_energy(idval):
    """Basic testing of get_bkg_plot: energy
    """

    # The way I have set up the data means that set_analysis
    # doesn't seem to change the setting for the background,
    # which should be tracked down (Sep 2019) but not just now.
    #
    setup_example_bkg(idval)
    if idval is None:
        ui.set_analysis('energy')
        ui.get_bkg().units = 'energy'
        bp = ui.get_bkg_plot()
    else:
        ui.set_analysis(idval, 'energy')
        ui.get_bkg(idval).units = 'energy'
        bp = ui.get_bkg_plot(idval)

    # TODO: is this a bug in the plotting code, or does it just
    # indicate that the test hasn't set up the correct invariants
    # (which may be true as the code above has to change the units
    # setting of the background object)?
    #
    # I was expecting bp.x to return energy and not channel values
    #
    assert bp.x == pytest.approx(_data_chan)

    # normalise by exposure time and bin width, but bin width here
    # is 1 (because it is being measured in channels).
    #
    yexp = _data_bkg / 1201.0 / _bexpscale
    assert bp.y == pytest.approx(yexp)

    assert bp.title == 'example-bkg'
    assert bp.xlabel == 'Energy (keV)'
    assert bp.ylabel == 'Counts/sec/keV'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
@pytest.mark.parametrize("gfunc", [ui.get_bkg_plot,
                                   ui.get_bkg_model_plot,
                                   ui.get_bkg_fit_plot])
def test_get_bkg_plot_no_bkg(idval, gfunc):
    """Basic testing of get_bkg_XXX_plot when there's no background
    """

    setup_example(idval)
    with pytest.raises(IdentifierErr):
        if idval is None:
            gfunc()
        else:
            gfunc(idval)


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_model_plot(idval):
    """Basic testing of get_model_plot
    """

    setup_example(idval)
    if idval is None:
        mp = ui.get_model_plot()
    else:
        mp = ui.get_model_plot(idval)

    assert mp.xlo == pytest.approx(_data_chan)
    assert mp.xhi == pytest.approx(_data_chan + 1)

    # The model is a constant, but integrated across the energy bin,
    # so the energy width is important here to get the normalization
    # right. It should also be divided by the channel width, but in
    # this case each bin has a channel width of 1.
    #
    yexp = _arf * 1.02e2 * (_energies[1:] - _energies[:-1])
    assert mp.y == pytest.approx(yexp)

    assert mp.title == 'Model'
    assert mp.xlabel == 'Channel'
    assert mp.ylabel == 'Counts/sec/channel'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_model_plot_energy(idval):
    """Basic testing of get_model_plot: energy
    """

    setup_example(idval)
    if idval is None:
        ui.set_analysis('energy')
        mp = ui.get_model_plot()
    else:
        ui.set_analysis(idval, 'energy')
        mp = ui.get_model_plot(idval)

    assert mp.xlo == pytest.approx(_energies[:-1])
    assert mp.xhi == pytest.approx(_energies[1:])

    # This should be normalized by the bin width, but it is cancelled
    # out by the fact that the model normalization has to be multiplied
    # by the bin width (both in energy).
    #
    yexp = _arf * 1.02e2
    assert mp.y == pytest.approx(yexp)

    assert mp.title == 'Model'
    assert mp.xlabel == 'Energy (keV)'
    assert mp.ylabel == 'Counts/sec/keV'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_source_plot_warning(caplog, idval):
    """Does get_source_plot create a warning about channel space?

    This is a logged warning, not a UserWarning.
    """

    setup_example(idval)
    if idval is None:
        ui.get_source_plot()
    else:
        ui.get_source_plot(idval)

    emsg = 'Channel space is unappropriate for the PHA unfolded ' + \
           'source model,\nusing energy.'

    assert len(caplog.record_tuples) == 1
    rec = caplog.record_tuples[0]
    assert len(rec) == 3
    loc, lvl, msg = rec

    assert loc == 'sherpa.astro.plot'
    assert lvl == logging.WARNING
    assert msg == emsg


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_source_plot_energy(idval):
    """Basic testing of get_source_plot: energy
    """

    setup_example(idval)
    if idval is None:
        ui.set_analysis('energy')
        sp = ui.get_source_plot()
    else:
        ui.set_analysis(idval, 'energy')
        sp = ui.get_source_plot(idval)

    assert sp.xlo == pytest.approx(_energies[:-1])
    assert sp.xhi == pytest.approx(_energies[1:])

    yexp = 1.02e2 * np.ones(10)
    assert sp.y == pytest.approx(yexp)

    assert sp.title == 'Source Model of example'
    assert sp.xlabel == 'Energy (keV)'

    # y label depends on the backend
    # assert sp.ylabel == 'f(E)  Photons/sec/cm$^2$/keV'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_model_plot(idval):
    """Basic testing of get_bkg_model_plot
    """

    setup_example_bkg_model(idval)
    if idval is None:
        bp = ui.get_bkg_model_plot()
    else:
        bp = ui.get_bkg_model_plot(idval)

    print(bp)
    assert bp.xlo == pytest.approx(_data_chan)
    assert bp.xhi == pytest.approx(_data_chan + 1)

    # TODO: this is the same output as test_get_bkg_model_plot_energy,
    #       which doesn't make sense.
    yexp = _arf / (_bexpscale * 100)
    assert bp.y == pytest.approx(yexp)

    assert bp.title == 'Model'
    assert bp.xlabel == 'Channel'
    assert bp.ylabel == 'Counts/sec/channel'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_model_plot_energy(idval):
    """Basic testing of get_bkg_model_plot: energy
    """

    # The way I have set up the data means that set_analysis
    # doesn't seem to change the setting for the background,
    # which should be tracked down (Sep 2019) but not just now.
    #
    setup_example_bkg_model(idval)
    if idval is None:
        ui.set_analysis('energy')
        ui.get_bkg().units = 'energy'
        bp = ui.get_bkg_model_plot()
    else:
        ui.set_analysis(idval, 'energy')
        ui.get_bkg(idval).units = 'energy'
        bp = ui.get_bkg_model_plot(idval)

    # TODO: is this a bug in the plotting code, or does it just
    # indicate that the test hasn't set up the correct invariants
    # (which may be true as the code above has to change the units
    # setting of the background object)?
    #
    # I was expecting bp.x to return energy and not channel values
    #
    assert bp.xlo == pytest.approx(_data_chan - 0.5)
    assert bp.xhi == pytest.approx(_data_chan + 0.5)

    # TODO: The factor of 100 comes from the bin width (0.1 keV), but
    # why is there a scaling by _bexpscale?
    yexp = _arf / (_bexpscale * 100)
    assert bp.y == pytest.approx(yexp)

    assert bp.title == 'Model'
    assert bp.xlabel == 'Energy (keV)'
    assert bp.ylabel == 'Counts/sec/keV'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_resid_plot(idval):
    """Basic testing of get_bkg_resid_plot
    """

    setup_example_bkg_model(idval)
    if idval is None:
        bp = ui.get_bkg_resid_plot()
    else:
        bp = ui.get_bkg_resid_plot(idval)

    assert bp.x == pytest.approx(_data_chan)

    # correct the counts by the bin width and exposure time
    #
    yexp = (_data_bkg * 100.0 / 1201.0 - _arf) / (_bexpscale * 100)
    assert bp.y == pytest.approx(yexp)

    assert bp.title == 'Residuals of example-bkg - Bkg Model'
    assert bp.xlabel == 'Channel'
    assert bp.ylabel == 'Counts/sec/channel'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_resid_plot_energy(idval):
    """Basic testing of get_bkg_resid_plot: energy
    """

    setup_example_bkg_model(idval)
    if idval is None:
        ui.set_analysis('energy')
        ui.get_bkg().units = 'energy'
        bp = ui.get_bkg_resid_plot()
    else:
        ui.set_analysis(idval, 'energy')
        ui.get_bkg(idval).units = 'energy'
        bp = ui.get_bkg_resid_plot(idval)

    assert bp.x == pytest.approx(_data_chan)

    # correct the counts by the bin width and exposure time
    #
    yexp = (_data_bkg * 100.0 / 1201.0 - _arf) / (_bexpscale * 100)
    assert bp.y == pytest.approx(yexp)

    assert bp.title == 'Residuals of example-bkg - Bkg Model'
    assert bp.xlabel == 'Energy (keV)'
    assert bp.ylabel == 'Counts/sec/keV'


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_fit_plot(idval):
    """Basic testing of get_bkg_fit_plot
    """

    setup_example_bkg_model(idval)
    if idval is None:
        fp = ui.get_bkg_fit_plot()
    else:
        fp = ui.get_bkg_fit_plot(idval)

    dp = fp.dataplot
    mp = fp.modelplot

    assert dp.title == 'example-bkg'
    assert mp.title == 'Background Model Contribution'

    for plot in [dp, mp]:
        assert plot.xlabel == 'Channel'
        assert plot.ylabel == 'Counts/sec/channel'
        assert plot.x == pytest.approx(_data_chan)

    yexp = _data_bkg / 1201.0 / _bexpscale
    assert dp.y == pytest.approx(dp.y)

    yexp = _arf / 100.0 / _bexpscale
    assert mp.y == pytest.approx(yexp)


@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
def test_get_bkg_fit_plot_energy(idval):
    """Basic testing of get_bkg_fit_plot: energy
    """

    setup_example_bkg_model(idval)
    if idval is None:
        ui.set_analysis('energy')
        ui.get_bkg().units = 'energy'
        fp = ui.get_bkg_fit_plot()
    else:
        ui.set_analysis(idval, 'energy')
        ui.get_bkg(idval).units = 'energy'
        fp = ui.get_bkg_fit_plot(idval)

    dp = fp.dataplot
    mp = fp.modelplot

    assert dp.title == 'example-bkg'
    assert mp.title == 'Background Model Contribution'

    for plot in [dp, mp]:
        assert plot.xlabel == 'Energy (keV)'
        assert plot.ylabel == 'Counts/sec/keV'
        assert plot.x == pytest.approx(_data_chan)

    yexp = _data_bkg / 1201.0 / _bexpscale
    assert dp.y == pytest.approx(dp.y)

    yexp = _arf / 100.0 / _bexpscale
    assert mp.y == pytest.approx(yexp)


def check_bkg_fit(plotfunc):
    """Is the background fit displayed?

    This only checks the plot object, not the plot "hardcopy" output
    (e.g. the pixel display/PNG output).
    """

    dplot = ui._session._bkgdataplot
    mplot = ui._session._bkgmodelplot

    # check the "source" plots are not set
    for plot in [ui._session._dataplot, ui._session._modelplot]:
        assert plot.x is None
        assert plot.y is None

    xlabel = 'Channel' if plotfunc == ui.plot_bkg_fit else ''

    # check plot basics
    for plot in [dplot, mplot]:
        assert plot.xlabel == xlabel
        assert plot.ylabel == 'Counts/sec/channel'

        assert plot.x == pytest.approx(_data_chan)

    assert dplot.title == 'example-bkg'
    assert mplot.title == 'Background Model Contribution'

    yexp = _data_bkg / 1201.0 / _bexpscale
    assert dplot.y == pytest.approx(yexp)

    yexp = _arf / (_bexpscale * 100)
    assert mplot.y == pytest.approx(yexp)


def check_bkg_resid(plotfunc):
    """Is the background residual displayed?

    This only checks the plot object, not the plot "hardcopy" output
    (e.g. the pixel display/PNG output).

    There is limited checks of the actual values, since the
    assumption is that this test is just to check the plots were
    constructed from its components, and that other tests above
    will have checked that the components work.

    """

    # check the "other" background plots are not set
    plot = None
    for pf, pd in [(ui.plot_bkg_fit_delchi, ui._session._bkgdelchiplot),
                   (ui.plot_bkg_fit_ratio, ui._session._bkgratioplot),
                   (ui.plot_bkg_fit_resid, ui._session._bkgresidplot)]:
        if pf == plotfunc:
            assert plot is None  # a precaution
            plot = pd
            continue
        else:
            assert pd.x is None
            assert pd.y is None

    # very limited checks
    #
    assert plot.xlabel == 'Channel'
    assert plot.ylabel != ''  # depends on the plot type
    assert plot.title == ''

    assert plot.x == pytest.approx(_data_chan)
    assert plot.y is not None

    # the way the data and model are constructed, all residual values
    # should be negative, and the ratio values positive (or zero).
    #
    if plotfunc == ui.plot_bkg_fit_ratio:
        assert np.all(plot.y >= 0)
    else:
        assert np.all(plot.y < 0)


@requires_plotting
@pytest.mark.usefixtures("clean_astro_ui")
@pytest.mark.parametrize("idval", [None, 1, "one", 23])
@pytest.mark.parametrize("plotfunc,checkfuncs",
                         [(ui.plot_bkg_fit, [check_bkg_fit]),
                          (ui.plot_bkg_fit_delchi, [check_bkg_fit, check_bkg_resid]),
                          (ui.plot_bkg_fit_ratio, [check_bkg_fit, check_bkg_resid]),
                          (ui.plot_bkg_fit_resid, [check_bkg_fit, check_bkg_resid])])
def test_bkg_plot_xxx(idval, plotfunc, checkfuncs):
    """Test background plotting - channel space"""

    setup_example_bkg_model(idval)
    if idval is None:
        plotfunc()
    else:
        plotfunc(idval)

    # The X label of the plots may depend on whether there are 1
    # or two plots. The following isn't ideal but let's see how
    # it goes.
    #
    for checkfunc in checkfuncs:
        checkfunc(plotfunc)
