from datetime import datetime
from time import time

from pyschism.mesh.hgrid import Hgrid
from pyschism.forcing.nws.nws2.gfs2 import GFS


if __name__ == "__main__":
    t0 = time()

    # now = datetime.now()
    # last_cycle = np.datetime64(pd.DatetimeIndex([now-timedelta(hours=2)]).floor('6H').values[0], 'h').tolist()
    # start = (last_cycle - timedelta(days=1)).replace(hour=0)
    start = datetime(2023, 10, 1)
    rnday = 10
    # record = 5
    # outdir = path = pathlib.Path('./GFS_2023')

    hgrid = Hgrid.open("../../static/hgrid.gr3", crs="epsg:4326")
    pscr = "/sciclone/pscr/lcui01/GFS/"
    gfs = GFS(level=1, pscr=pscr, bbox=hgrid.bbox)
    gfs.write(start_date=start, rnday=rnday, air=True, prc=True, rad=True)

    print(f"It took {(time()-t0)/60} mins to process {rnday} days")
