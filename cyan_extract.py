import os
import datetime
import pandas as pd
import numpy as np
import requests
import xarray as xr


def getL3Burl(instr_name, prod_suff, temp_res, target_dt):
    from datetime import timedelta
    satfileurl = ''
    if 'MERIS' in instr_name:
        if 'DAY' in temp_res:
            l3filename = target_dt.strftime('M%Y%j.L3b_DAY_CYAN.nc')
        elif '7D' in temp_res:
            idyjul = int(target_dt.strftime('%j')) - 1
            # calculate the next number divisible by 7
            idyjul_hi = 7 * (1 + int(idyjul / 7))
            dt_hi = target_dt + timedelta(days=idyjul_hi-idyjul-1)
            dt_lo = dt_hi - timedelta(days=6)
            l3filename = dt_lo.strftime(
                'M%Y%j') + dt_hi.strftime('%Y%j.L3b_7D_' + prod_suff + '.nc')  # MERIS 7-day L3b
        else:
            print('ERROR - Bad temporal specification:', temp_res)
            return ''
    elif 'OLCI' in instr_name:
        if 'DAY' in temp_res:
            l3filename = target_dt.strftime('L%Y%j.L3b_DAY_CYAN.nc')
            # l3filename = target_dt.strftime('L%Y%j.L3m_DAY_CYAN_CI_cyano_CYAN_CONUS_300m.tif') #OLCI daily L3b
        elif '7D' in temp_res:  # L20170152017021.L3b_7D_S3A_CYAN.nc
            idyjul = int(target_dt.strftime('%j')) - 1
            # calculate the next number divisible by 7
            idyjul_hi = 7 * (1 + int(idyjul / 7))
            dt_hi = target_dt + timedelta(days=idyjul_hi-idyjul-1)
            dt_lo = dt_hi - timedelta(days=6)
            l3filename = dt_lo.strftime(
                'L%Y%j') + dt_hi.strftime('%Y%j.L3b_7D_S3A_' + prod_suff + '.nc')
            # MERIS 7-day L3b
        else:
            print('ERROR - Bad temporal specification:', temp_res)
            return ''
    else:
        print('ERROR - Bad instrument specification:', instr_name)
        return ''

    return 'https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/' + l3filename


def process_L3B_file(ds):
    '''
    Process L3b_DAY_CYAN nc file into pandas dataframe, convert bins to lat/lon location
    '''
    df_BinIndex = pd.DataFrame(ds.BinIndex.values).reset_index()

    df = pd.DataFrame(ds.BinList.values)
    for k in list(ds.keys())[1:-1]:
        tmp = pd.DataFrame(ds[k].values)
        df[k] = tmp['sum']

    out = pd.merge_asof(left=df, right=df_BinIndex, left_on="bin_num",
                        right_on="start_num", direction='backward')

    nrows = ds.dims['binIndexDim']
    latbin = (np.arange(0, nrows, dtype=np.float_) + 0.5) * \
        (180.0 / nrows) - 90.0
    out['clat'] = out['index'].apply(lambda x: latbin[x])
    out['clon'] = (360.0 * (out['bin_num'] -
                   out['start_num'] + 0.5) / out['max']) - 180.0
    out['north'] = out['clat'] + (90.0 / nrows)
    out['south'] = out['clat'] - (90.0 / nrows)
    out['west'] = out['clon'] - (180.0 / out['max'])
    out['east'] = out['clon'] + (180.0 / out['max'])

    out_cols = ['bin_num', 'CI_stumpf', 'CI_cyano', 'CI_noncyano', 'MCI_stumpf',
                'clat', 'clon', 'north', 'south', 'west', 'east']

    return out[out_cols]


def extract_cyan(date_frome: datetime.date, date_to: datetime.date, file='cyan_data'):

    local = "./data/"
    df = pd.DataFrame()

    for i in range((date_to - date_frome).days+1):

        day_of = date_frome + datetime.timedelta(days=i)
        url = getL3Burl(instr_name='OLCI', prod_suff='CYAN',
                        temp_res='DAY', target_dt=day_of)
        fn = url.split('/')[-1]
        print(day_of, ": Processing", url)
        try:
            r = requests.get(url)
            with open(local + fn, 'wb') as f:
                f.write(r.content)

            ds = xr.open_dataset(local + fn, group="level-3_binned_data")

            df_tmp = process_L3B_file(ds=ds)
            df_tmp['date'] = day_of

            df = pd.concat([df, df_tmp], axis=0)
            print("  Complete: ", df_tmp.shape)

            os.remove(local + fn)

        except:
            print("No data for", day_of)

    print("Extraction Completed:", df.shape)

    df.to_parquet(local + file)


# extract_cyan(date_frome=datetime.date(2024, 4, 1),
#              date_to=datetime.date(2024, 4, 10),
#              file='cyan_data')

local = "./data/"
day_of = datetime.date(2024, 4, 1)
url = getL3Burl(instr_name='OLCI', prod_suff='CYAN',
                temp_res='DAY', target_dt=day_of)
print(url)
fn = url.split('/')[-1]
print(fn)
r = requests.get(url)
with open(local + fn, 'wb') as f:
    f.write(r.content)

ds = xr.open_dataset(local + fn, group="level-3_binned_data")
