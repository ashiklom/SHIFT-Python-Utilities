import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject
from rasterio.enums import Resampling
import progressbar

def reproject_raster(input_raster, output, crs=None, resampling_method='nearest', resolution=None, progress_bar=True):
    """
    Reprojects and north orients a raster. Wrapper for rasterio.warp.reproject

    Parameters
    ----------
    input_raster : str
        Path to input raster
    
    output : str
        Write path
    
    crs : str (optional)
        destination crs (can be the same as input and raster will just north orient)
     
    resampling_method: str (optional)
        String pertaining to the desired resampling method. Default: nearest
        
    resolution: tuple(float, float) (optional)
        Output resolution, Default: input raster resolution
    Returns
    -------
        None (Writes reprojection to the outpath)
    """
    
    assert resampling_method in dir(Resampling), f"Invalid resampling method, Supported methods: {[method for method in dir(Resampling) if '_' not in method]}"
    
    resampling_method = getattr(Resampling, resampling_method)
    
    with rio.open(input_raster) as src:
        # copy the profile
        profile = src.profile
        
        # If no crs is provided, use the input rasters crs (north orient)
        if crs is None:
            crs = src.crs
        else:
            crs = rio.crs.CRS.from_string(crs)
            
        if resolution is None:
            resolution = resolution=src.transform._scaling
        else:
            assert isinstance(resolution, tuple), f"Resolution must be a tuple, {src.transform._scaling}"
        
        #calculate transform array and shape of reprojected raster
        transform, width, height = calculate_default_transform(
            src.crs,
            crs, 
            src.width, 
            src.height,
            resolution=resolution,
            *src.bounds
        )
        
        #update meta data
        profile.update(transform=transform, width=width, height=height, crs=crs)
        
        with rio.open(output, "w", **profile) as dst:
            #set band descriptions
            dst.descriptions = src.descriptions
            # reproject and write each band one by one
            if progress_bar:
                bar = progressbar.ProgressBar(maxval=len(range(1, 1 + dst.count))).start()
            for i in range(1, 1 + dst.count):
                rio.warp.reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst,i),
                    src_crs=src.crs,
                    src_transform=src.transform,
                    dst_crs=crs,
                    dst_transform=transform,
                    dst_nodata=src.nodata,
                    resampling=resampling_method
                )
            if progress_bar:
                bar.update(i)