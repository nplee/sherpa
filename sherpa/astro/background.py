#
#  Copyright (C) 2007, 2020  Smithsonian Astrophysical Observatory
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

"""Support multiple background components for a PHA dataset.

"""

from sherpa.models.model import CompositeModel, ArithmeticModel
from sherpa.utils.err import DataErr


__all__ = ('BackgroundSumModel', 'add_response')


class BackgroundSumModel(CompositeModel, ArithmeticModel):
    """Combine multiple background datasets.

    Define the model expression to be applied to the source
    region accounting for the background models.

    Parameters
    ----------
    srcdata : sherpa.astro.data.DataPHA instance
        The source dataset.
    bkgmodels : dict
        The background components, where the key is the identifier
        in this dataset and the value is the model. This dictionary
        cannot be empty.

    """

    def __init__(self, srcdata, bkgmodels):
        self.srcdata = srcdata
        self.bkgmodels = bkgmodels
        scale_factor = self.srcdata.sum_background_data(lambda key, bkg:1)
        bkgnames = [model.name for model in bkgmodels.values()]
        name = '%g * (' % scale_factor + ' + '.join(bkgnames) + ')'
        CompositeModel.__init__(self, name, self.bkgmodels.values())

    def calc(self, p, *args, **kwargs):
        def eval_bkg_model(key, bkg):
            bmodel = self.bkgmodels.get(key)
            if bmodel is None:
                raise DataErr('bkgmodel', key)
            # FIXME: we're not using p here (and therefore assuming that the
            # parameter values have already been updated to match the contents
            # of p)
            return bmodel(*args, **kwargs)

        # Evaluate the background model for each dataset using the same
        # grid and apply the background-to-source correction factors.
        #
        # This will only work if the scaling factors are scalars,
        # since if there are any array elements then the models
        # have been evaluated on the energy/wavelength grid,
        # but the correction factors are defined in channel space.
        #
        return self.srcdata.sum_background_data(eval_bkg_model)


def add_response(session, id, data, model):
    """Create the response model describing the source and model.

    Include any background components and apply the response
    model for the dataset.

    Parameters
    ----------
    session : sherpa.astro.ui.utils.Session instance
    id : int ot str
        The identifier for the dataset.
    data : sherpa.astro.data.DataPHA instance
        The dataset (may be a background dataset).
    model : sherpa.models.model.ArithmeticModel instance
        The model (without response or background components)
        to match to data.

    Returns
    -------
    fullmodel : sherpa.models.model.ArithmeticModel
        The model including the necessary response models and
        background components.

    """

    if not data.subtracted:
        bkg_srcs = session._background_sources.get(id, {})
        if len(bkg_srcs.keys()) != 0:
            model = (model +
                     BackgroundSumModel(data, bkg_srcs))

    resp = session._get_response(id, data)
    return resp(model)
