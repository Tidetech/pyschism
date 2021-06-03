import argparse
from datetime import datetime, timedelta
import json
import logging
import pathlib

from pyproj import CRS

from pyschism.forcing.baroclinic import GOFS, RTOFS
from pyschism.forcing.tides import Tides
from pyschism.forcing.bctides import Bctides, iettype, ifltype, itetype, isatype
from pyschism.mesh import Hgrid, Vgrid


logger = logging.getLogger(__name__)


class BctidesCli:
    def __init__(self, args: argparse.Namespace):

        bctides = Bctides(
                args.hgrid,
                args.start_date,
                args.run_days,
                vgrid=args.vgrid,
            )

        if args.Z0 is not None:
            bctides.Z0 = args.Z0

        bctides.write(args.output_directory, overwrite=args.overwrite)

    @staticmethod
    def add_subparser_action(subparsers):
        add_bctides_options_to_parser(subparsers.add_parser('bctides'))


def add_bctides_options_to_parser(parser):
    parser.add_argument(
        "hgrid",
        action=HgridAction,
        help='Path to the SCHISM hgrid file.'
    )
    parser.add_argument(
        '--hgrid-crs',
        action=HgridCrsAction,
        help='Coordinate reference system string of hgrid.'
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwrite of output files."
    )
    parser.add_argument(
        "--log-level",
        choices=[name.lower() for name in logging._nameToLevel],
        default="warning",
    )
    parser.add_argument(
        "--run-days",
        type=lambda x: timedelta(days=float(x)),
        required=True,
        help='Number of simulation days.'

    )
    parser.add_argument(
        "--start-date",
        type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
        # help=''
        # action=DateAction,
    )
    # bctides.add_argument(
    #     "--date-formatting",
    #     type=str,
    #     type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"),
    #     # help=''
    # )
    parser.add_argument(
        "--output-directory",
        "-o",
        type=pathlib.Path,
        required=True
    )
    parser.add_argument(
        "--vgrid",
        action=VgridAction,
        default=Vgrid.default(),
    )
    parser.add_argument(
        '--tides',
        '--tidal-database',
        choices=['hamtide', 'tpxo'],
        default='hamtide',
        dest='tidal_database'
    )
    parser.add_argument(
        '--hycom',
        '--baroclinic-database',
        choices=['rtofs', 'gofs'],
        dest='baroclinic_database',
        default='gofs',
    )
    parser.add_argument(
        '--include-velocity',
        action='store_true'
    )
    parser.add_argument('--Z0', type=float)
    parser.add_argument("--cutoff-depth", type=float, default=50.0)
    add_bctypes_options_to_parser(parser)


class HgridAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        tmp_parser = argparse.ArgumentParser()
        tmp_parser.add_argument('--hgrid-crs')
        tmp_args, _ = tmp_parser.parse_known_args()
        hgrid = Hgrid.open(values, crs=tmp_args.hgrid_crs)
        if len(hgrid.boundaries.open) == 0:
            raise TypeError(f"Hgrid provided {values} contains no open boundaries.")
        setattr(namespace, self.dest, hgrid)


class HgridCrsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if values is not None:
            namespace.hgrid.nodes._crs = CRS.from_user_input(values)
        setattr(namespace, self.dest, values)


class VgridAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, Vgrid.open(values))


def add_bctypes_options_to_parser(parser):
    _iettype = parser.add_mutually_exclusive_group()
    _iettype.add_argument(
        "--iettype",
        dest="iettype",
        action=CustomBoundaryAction,
        const=iettype.Iettype,
        help='Per-boundary specification option for elevation variable. '
             'The format required is a json-style string. For example: '
             '--iettype=\'{"1": 3}\' would apply iettype-3 to boundary with '
             'id equal to "1".'
    )
    _iettype.add_argument(
        "--elev-th",
        "--iettype-1",
        dest="iettype",
        type=iettype.Iettype1,
        help='Global elevation options for time history.',
    )
    _iettype.add_argument(
        '--elev-val',
        '--iettype-2',
        dest='iettype',
        type=iettype.Iettype2,
        help='Global constant elevation option.',
    )

    _iettype.add_argument(
        "--elev-tides",
        "--iettype-3",
        dest="iettype",
        nargs=0,
        const=iettype.Iettype3,  # the option string is present but not followed by a command-line argument. In this case the value from const will be produced.
        action=Iettype3Action,
    )

    _iettype.add_argument(
        '--elev-subtides',
        '--elev-2d',
        '--iettype-4',
        dest='iettype',
        nargs=0,
        const=iettype.Iettype4,
        action=Iettype4Action,
    )

    _iettype.add_argument(
        '--elev-tides-subtides',
        '--tides-elev-2d',
        '--elev-2d-tides',
        '--iettype-5',
        dest='iettype',
        nargs=0,
        const=iettype.Iettype5,
        action=Iettype5Action,
    )

    _iettype.add_argument(
        '--elev-zero',
        '--iettype-_1',
        dest='iettype',
        type=iettype.Iettype_1,
    )
    _ifltype = parser.add_mutually_exclusive_group()
    _ifltype.add_argument(
        "--ifltype",
        dest="ifltype",
        nargs=1,  # 0 or more
        const={},
        action=CustomBoundaryAction,
    )
    _ifltype.add_argument(
        '--flux-th',
        '--ifltype-1',
        dest='ifltype',
        type=ifltype.Ifltype1
    )
    _ifltype.add_argument(
        '--flux-val',
        '--ifltype-2',
        dest='ifltype',
        type=ifltype.Ifltype2
    )

    _ifltype.add_argument(
        '--uv-tides',
        '--ifltype-3',
        nargs="?",  # 0 or more
        action=Ifltype3Action,
        dest='ifltype',
        const=ifltype.Ifltype3,
    )

    _ifltype.add_argument(
        '--uv-subtides',
        '--uv-3d',
        '--uv3D',
        '--ifltype-4',
        action=Ifltype4Action,
        dest='ifltype',
        nargs=0,
        const=ifltype.Ifltype4,
    )

    _ifltype.add_argument(
        '--uv-tides-subtides',
        '--uv-3d-tides',
        '--uv3d-tides',
        '--uv3D-tides',
        '--uv3D-tides',
        '--ifltype-5',
        action=Ifltype5Action,
        nargs=0,
        dest='ifltype',
        const=ifltype.Ifltype5,
    )

    _ifltype.add_argument(
        '--uv-zero',
        '--flather',
        action='store_const',
        dest='ifltype',
        const=ifltype.Ifltype_1,
    )
    _itetype = parser.add_mutually_exclusive_group()
    _itetype.add_argument(
        "--itetype",
        dest="itetype",
        nargs=1,  # 0 or more
        const={},
        action=CustomBoundaryAction,
    )
    _itetype.add_argument(
        '--temp-th',
        '--itetype-1',
        dest='itetype',
        type=itetype.Itetype1
    )
    _itetype.add_argument(
        '--temp-val',
        '--itetype-2',
        dest='itetype',
        type=itetype.Itetype2
    )

    _itetype.add_argument(
        '--temp-ic',
        '--itetype-3',
        dest='itetype',
        type=itetype.Itetype3,
    )

    _itetype.add_argument(
        '--temp-3d',
        '--itetype-4',
        action=Itetype4Action,
        dest='itetype',
        nargs=0,
        const=itetype.Itetype4,
    )
    _isatype = parser.add_mutually_exclusive_group()
    _isatype.add_argument(
        "--isatype",
        dest="isatype",
        nargs=1,  # 0 or more
        const={},
        action=CustomBoundaryAction,
    )
    _isatype.add_argument(
        '--salt-th',
        '--isatype-1',
        dest='isatype',
        type=isatype.Isatype1
    )
    _isatype.add_argument(
        '--salt-val',
        '--isatype-2',
        dest='isatype',
        type=isatype.Isatype2
    )

    _isatype.add_argument(
        '--salt-ic',
        '--isatype-3',
        dest='isatype',
        type=isatype.Isatype3,
    )

    _isatype.add_argument(
        '--salt-3d',
        '--isatype-4',
        action=Isatype4Action,
        dest='isatype',
        nargs=0,
        const=isatype.Isatype4,
    )


baroclinic_databases = {
    'gofs': GOFS,
    'rtofs': RTOFS,
}


def get_tides(args: argparse.Namespace):
    def get_elevation():
        return True if args.tidal_database is not None else False

    def get_velocity():
        vgrid = Vgrid.default() if args.vgrid is None else args.vgrid
        return (
            True
            if args.include_velocity is True or vgrid.is3D() is True
            else False
        )

    return Tides(
        elevation=get_elevation(),
        velocity=get_velocity(),
        tidal_database=args.tidal_database,
    )


class CustomBoundaryAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if isinstance(values, str):
            if "iettype" in option_string:
                values = json.loads(values)
                for bnd_id, tval in values.items():
                    if not isinstance(tval, int):
                        raise TypeError(
                            'Boundary type must be an integer, not type '
                            f'{type(tval)}.')
                    if tval == 3:
                        namespace.hgrid.boundaries.set_forcing(
                            bnd_id,
                            iettype=iettype.Iettype3(get_tides(namespace))
                            )
                    else:
                        raise ValueError
        setattr(namespace, self.dest, values)


class Iettype3Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                iettype=self.const(get_tides(namespace)))
        setattr(namespace, self.dest, self.const)


class Iettype4Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                iettype=self.const(baroclinic_databases[
                    namespace.baroclinic_database]()))
        setattr(namespace, self.dest, self.const)


class Iettype5Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                iettype=self.const(
                    get_tides(namespace),
                    baroclinic_databases[namespace.baroclinic_database]()
                    )
            )
        setattr(namespace, self.dest, self.const)


class Ifltype3Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                ifltype=values(get_tides(namespace)))
        setattr(namespace, self.dest, values)


class Ifltype4Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                ifltype=self.const(baroclinic_databases[
                    namespace.baroclinic_database]()))
        setattr(namespace, self.dest, values)


class Ifltype5Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                ifltype=self.const(
                    get_tides(namespace),
                    baroclinic_databases[namespace.baroclinic_database]()
                    )
            )
        setattr(namespace, self.dest, values)


class Itetype4Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                itetype=self.const(baroclinic_databases[
                    namespace.baroclinic_database]()))
        setattr(namespace, self.dest, self.const)


class Isatype4Action(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        for boundary in namespace.hgrid.boundaries.open.itertuples():
            namespace.hgrid.boundaries.set_forcing(
                boundary.id,
                isatype=self.const(baroclinic_databases[
                    namespace.baroclinic_database]()))
        setattr(namespace, self.dest, self.const)
