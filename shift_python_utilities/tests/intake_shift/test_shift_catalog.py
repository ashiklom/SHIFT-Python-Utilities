import pytest
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import os
from shift_python_utilities.intake_shift import shift_catalog

root_dir = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
root_dir = os.path.join(root_dir, "test_data")

@pytest.fixture
def cat():
    return shift_catalog()

def get_dataset(cat, dataset):
  # Verify each type of dataset can be read in
    if isinstance(dataset, tuple):
        parent, child = dataset
        key = child
        dataset = getattr(getattr(cat, parent), child)()
    else:
        key = dataset
        dataset = getattr(cat, dataset)()
    return dataset
def test_aviris_data(cat):
    cat.aviris_v1_gridded().read_chunked()

def test_time_date_filter(cat):
    ds = cat.L2a(date="20220228", time="204228")  
    assert "20220228" in ds.urlpath and "204228" in ds.urlpath

    
@pytest.mark.parametrize(
    "dataset, date, time, mask, expected",
    [
        (("L1", "glt"), "20220228", "183924", True, 2),
        (("L1", "igm"), "20220228", "183924",True, 3),
        (("L1", "obs"), "20220228", "183924",True, 11),
        (("L1", "rdn"), "20220228", "183924",True, 337),
        ("L2a", "20220228", "183924", True, 337),
        (("L1", "glt"), "20220228", "183924", [10, 5, 15, 333, 420], 2),
        (("L1", "igm"), "20220228", "183924", [1], 3),
        (("L1", "obs"), "20220228", "183924", [0, 10], 11),
        (("L1", "rdn"), "20220228", "183924", [10, 5, 15, 333, 420], 420),
        ("L2a", "20220228", "183924", [10, 5, 15, 333, 420], 420)
    ]
)
    
def test_bad_bands_filter(cat, dataset, date, time, mask, expected):
    dataset = get_dataset(cat, dataset)
    
    # if isinstance(mask, list):   
    #     tmp = np.ones((425))
    #     tmp[mask] = 0
    #     mask = tmp.astype(bool)
    ds = dataset(date=date, time=time, filter_bands=mask).read_chunked()
    try:
        assert int(ds.attrs['bands']) == expected
    except:
        assert len(ds.wavelength) == expected
        
@pytest.mark.parametrize(
    "dataset, date, time, chunks, expected",
    [
        (("L1", "rdn"), "20220228", "183924", {'y': 1}, 'y'),
        (("L1", "rdn"), "20220228", "183924",{'x': 1}, 'x'),
        (("L1", "rdn"), "20220228", "183924",{'band': 1}, 'wavelength'),
    ]
)   
def test_chunking(cat, dataset, date, time, chunks, expected):
    dataset = get_dataset(cat, dataset)
    ds = dataset(date=date, time=time, chunks=chunks).read_chunked()
    assert ds.chunksizes[expected][0] == 1
    
@pytest.mark.parametrize(
    "dataset, date, time, subset, expected",
    [
        (("L1", "rdn"), "20220228", "183924", None, (425, 598, 4388)),
        (("L1", "rdn"), "20220228", "183924",{'x': slice(20, 180), 'y':slice(55, 500)}, (425, 160, 445))
    ]
)   
def test_subsetting(cat, dataset, date, time, subset, expected):
    dataset = get_dataset(cat, dataset)
    ds = dataset(date=date, time=time, subset=subset).read_chunked()
    assert (ds.dims['wavelength'], ds.dims['x'], ds.dims['y']) == expected

@pytest.mark.parametrize(
    "dataset, date, time, subset",
    [
        (("L1", "rdn"), "20220228", "183924", {'x':slice(29, 200), 'y':slice(34, 500)}),
        (("L2a"), "20220228", "183924", {'x':slice(29, 200), 'y':slice(34, 500)})
    ]
)

    
def test_ortho(cat,dataset, date, time, subset):
    dataset = get_dataset(cat, dataset)

    ds = dataset(date=date, time=time, ortho=True, subset=subset).read_chunked()

    igm = cat.L1.igm(date=date, time=time, subset=subset).read_chunked()

    fig,ax=plt.subplots(1,1, figsize=(20, 6))
    cp = ax.contourf(ds.lon.values, ds.lat.values, ds.elevation.values, levels=15)
    fig,ax=plt.subplots(1,1, figsize=(20, 6))
    cp2 = ax.contourf(igm.easting.values, igm.northing.values, igm.elevation.values, levels=15)
    
    assert np.all(cp.cvalues == cp2.cvalues)

    

@pytest.mark.parametrize(
    "dataset, date, time, subset",
    [
        (("L2a"), "20220224", "200332", {'lat':[3812959.0852389 , 3810526.08057343], 'lon':[228610.68861488, 237298.1187180]}),
        (("L2a"), "20220224", "200332", gpd.read_file(os.path.join(root_dir,"intake_shift_shp", "intake_shift_shp.shp")))
    ]
)

    
def test_lat_lon_and_shape(cat,dataset, date, time, subset):
    dataset = get_dataset(cat, dataset)

    ds = dataset(date=date, time=time, ortho=True, subset=subset).read_chunked()

#     igm = cat.L1.igm(date=date, time=time, ortho=True).read_chunked()

#     fig,ax=plt.subplots(1,1, figsize=(20, 6))
#     cp = ax.contourf(ds.lon.values, ds.lat.values, ds.elevation.values, levels=15)
#     fig,ax=plt.subplots(1,1, figsize=(20, 6))
#     cp2 = ax.contourf(igm.easting.values, igm.northing.values, igm.elevation.values, levels=15)
    
#     assert np.all(cp.cvalues == cp2.cvalues)