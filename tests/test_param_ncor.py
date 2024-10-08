#! /usr/bin/env python
from datetime import datetime, timedelta
import logging
import tempfile
import unittest
import f90nml

from pyschism.mesh import Hgrid
from pyschism.driver import ModelConfig


class ModelConfigurationTestCase(unittest.TestCase):

    def test_ncor_zero(self):

        hgrid = Hgrid.open(
            "https://raw.githubusercontent.com/geomesh/test-data/main/NWM/hgrid.ll",
            crs="epsg:26918",
        )

        config = ModelConfig(
            hgrid,
            flags=[[3, 3, 0, 0]],
        )

        # create reference dates
        spinup_time = timedelta(days=0.0)
        start_date = datetime(2023, 9, 10)

        # create a coldstart object
        coldstart = config.coldstart(
            start_date=start_date,
            end_date=start_date + timedelta(days=3.0),
            timestep=150.0,
            dramp=spinup_time,
            dramp_ss=spinup_time,
            drampwind=spinup_time,
            nspool=timedelta(hours=1),
        )

        with tempfile.TemporaryDirectory() as tempdir:
            coldstart.write(tempdir, overwrite=True)

            nml = f90nml.read(f"{tempdir}/param.nml")
            assert "ncor" in nml["opt"]
            assert nml["opt"]["ncor"] == 0

    def test_ncor_one(self):

        hgrid = Hgrid.open(
            "https://raw.githubusercontent.com/geomesh/test-data/main/NWM/hgrid.ll",
            crs="epsg:4326",
        )

        config = ModelConfig(
            hgrid,
            flags=[[3, 3, 0, 0]],
        )

        # create reference dates
        spinup_time = timedelta(days=0.0)
        start_date = datetime(2023, 9, 10)

        # create a coldstart object
        coldstart = config.coldstart(
            start_date=start_date,
            end_date=start_date + timedelta(days=3.0),
            timestep=150.0,
            dramp=spinup_time,
            dramp_ss=spinup_time,
            drampwind=spinup_time,
            nspool=timedelta(hours=1),
        )

        with tempfile.TemporaryDirectory() as tempdir:
            coldstart.write(tempdir, overwrite=True)

            nml = f90nml.read(f"{tempdir}/param.nml")
            assert "ncor" in nml["opt"]
            assert nml["opt"]["ncor"] == 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    unittest.main()
