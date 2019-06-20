import h5py
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
#this function is from Ben
def ATL06_to_dict(filename, dataset_dict):
    """
        Read selected datasets from an ATL06 file

        Input arguments:
            filename: ATl06 file to read
            dataset_dict: A dictinary describing the fields to be read
                    keys give the group names to be read,
                    entries are lists of datasets within the groups
        Output argument:
            D6: dictionary containing ATL06 data.  Each dataset in
                dataset_dict has its own entry in D6.  Each dataset
                in D6 contains a list of numpy arrays containing the
                data
    """

    D6=[]
    pairs=[1, 2, 3]
    beams=['l','r']
    # open the HDF5 file
    with h5py.File(filename) as h5f:
        # loop over beam pairs
        for pair in pairs:
            # loop over beams
            for beam_ind, beam in enumerate(beams):
                # check if a beam exists, if not, skip it
                if '/gt%d%s/land_ice_segments' % (pair, beam) not in h5f:
                    continue
                # loop over the groups in the dataset dictionary
                temp={}
                for group in dataset_dict.keys():
                    for dataset in dataset_dict[group]:
                        DS='/gt%d%s/%s/%s' % (pair, beam, group, dataset)
                        # since a dataset may not exist in a file, we're going to try to read it, and if it doesn't work, we'll move on to the next:
                        try:
                            temp[dataset]=np.array(h5f[DS])
                            # some parameters have a _FillValue attribute.  If it exists, use it to identify bad values, and set them to np.NaN
                            if '_FillValue' in h5f[DS].attrs:
                                fill_value=h5f[DS].attrs['_FillValue']
                                bad = temp[dataset]==fill_value
                                temp[dataset]=np.float64(temp[dataset])
                                temp[dataset][bad]=np.NaN
                        except KeyError as e:
                            pass
                if len(temp) > 0:
                    # it's sometimes convenient to have the beam and the pair as part of the output data structure: This is how we put them there.
                    temp['pair']=np.zeros_like(temp['h_li'])+pair
                    temp['beam']=np.zeros_like(temp['h_li'])+beam_ind
                    #temp['filename']=filename
                    D6.append(temp)
    return D6

def point_covert(row):
    geom = Point(row['longitude'],row['latitude'])
    return geom

def ATL06_2_gdf(ATL06_fn,dataset_dict):
    """
    function to convert ATL06 hdf5 to geopandas dataframe, containing columns as passed in dataset dict
    Used Ben's ATL06_to_dict function
    """
    if ('latitude' in dataset_dict['land_ice_segments']) != True:
        dataset_dict['land_ice_segments'].append('latitude')
    if ('longitude' in dataset_dict['land_ice_segments']) != True:
        dataset_dict['land_ice_segments'].append('longitude')
    #use Ben's Scripts to convert to dict
    data_dict = ATL06_to_dict(ATL06_fn,dataset_dict)
    #this will give us 6 tracks
    i = 0
    for track in data_dict:
        #1 track
        #convert to datafrmae
        df = pd.DataFrame(track)
        df['p_b'] = str(track['pair'][0])+'_'+str(track['beam'][0])
        df['geometry'] = df.apply(point_covert,axis=1)
        if i==0:
            df_final = df.copy()
        else:
            df_final = df_final.append(df)
        i = i+1
    gdf_final = gpd.GeoDataFrame(df_final,geometry='geometry',crs={'init':'epsg:4326'})
    return gdf_final

