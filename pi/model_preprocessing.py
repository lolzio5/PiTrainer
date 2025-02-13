import numpy as np
import json
from scipy.stats import skew, kurtosis
from rep_analysis import SetData
from math import isnan

def line_to_axes(line: list[ list[float, float, float] ]) -> tuple[ list[float], list[float], list[float] ]:
    x = [line[i][0] for i in range(len(line))]
    y = [line[i][1] for i in range(len(line))]
    z = [line[i][2] for i in range(len(line))]
    return x, y, z


def extract_features(sig: list[float]) -> dict[str, float]:
    return {
        'mean': np.mean(sig),
        'std': np.std(sig),
        'median': np.median(sig),
        'min': np.min(sig),
        'max': np.max(sig),
        'iqr': np.percentile(sig, 75) - np.percentile(sig, 25),
        'skew': skew(sig, bias=False),
        'kurtosis': kurtosis(sig, fisher=True, bias=False)
    }

def replace_nan_dict_vals(x: dict, val):
    for key in x:
        if isnan(x[key]):
            x[key] = val

    return x


def process_rep_to_dict(accel3d, vel3d, pos3d, mag3d):
    accel = line_to_axes(accel3d)
    vel = line_to_axes(vel3d)
    pos = line_to_axes(pos3d)
    mag = line_to_axes(mag3d)

    # magnetometer is known to be fussy
    # check for constant stream ie. for nans in output

    magx_features = extract_features(mag[0])
    magx_features = replace_nan_dict_vals(magx_features, 0)
    magy_features = extract_features(mag[1])
    magy_features = replace_nan_dict_vals(magy_features, 0)
    magz_features = extract_features(mag[2])
    magz_features = replace_nan_dict_vals(magz_features, 0)
    

    data = {
        'accel_x': extract_features(accel[0]),
        'accel_y': extract_features(accel[1]),
        'accel_z': extract_features(accel[2]),
        'vel_x': extract_features(vel[0]),
        'vel_y': extract_features(vel[1]),
        'vel_z': extract_features(vel[2]),
        'pos_x': extract_features(pos[0]),
        'pos_y': extract_features(pos[1]),
        'pos_z': extract_features(pos[2]),
        'mag_x': magx_features,
        'mag_y': magy_features,
        'mag_z': magz_features
    }

    return data

def process_rep_to_features(accel3d, vel3d, pos3d, mag3d, all_features):
    accel = line_to_axes(accel3d)
    vel = line_to_axes(vel3d)
    pos = line_to_axes(pos3d)
    mag = line_to_axes(mag3d)

    all_features['accel_x'] = update_features(accel[0], all_features['accel_x'])
    all_features['accel_y'] = update_features(accel[1], all_features['accel_y'])
    all_features['accel_z'] = update_features(accel[2], all_features['accel_z'])
    
    all_features['vel_x'] = update_features(vel[0], all_features['vel_x'])
    all_features['vel_y'] = update_features(vel[1], all_features['vel_y'])
    all_features['vel_z'] = update_features(vel[2], all_features['vel_z'])

    all_features['pos_x'] = update_features(pos[0], all_features['pos_x'])
    all_features['pos_y'] = update_features(pos[1], all_features['pos_y'])
    all_features['pos_z'] = update_features(pos[2], all_features['pos_z'])

    all_features['mag_x'] = update_features(mag[0], all_features['mag_x'])
    all_features['mag_y'] = update_features(mag[1], all_features['mag_y'])
    all_features['mag_z'] = update_features(mag[2], all_features['mag_z'])
    
    return all_features


def update_features(sig: list[float], features: dict[str, list[float]]) -> dict[str, list[float]]:
    if 'mean' in features.keys():
        features['mean'].append(np.mean(sig))
    else:
        features['mean'] = [np.mean(sig)]

    if 'std' in features.keys():
        features['std'].append(np.std(sig))
    else:
        features['std'] = [np.std(sig)]

    if 'median' in features.keys():
        features['median'].append(np.median(sig))
    else:
        features['median'] = [np.median(sig)]

    if 'min' in features.keys():
        features['min'].append(np.min(sig))
    else:
        features['min'] = [np.min(sig)]

    if 'max' in features.keys():
        features['max'].append(np.max(sig))
    else:
        features['max'] = [np.max(sig)]

    if 'iqr' in features.keys():
        features['iqr'].append( np.percentile(sig, 75) - np.percentile(sig, 25) )
    else:
        features['iqr'] = [np.percentile(sig, 75) - np.percentile(sig, 25)]

    cur_skew = skew(sig, bias=False)
    cur_skew = 0 if isnan(cur_skew) else cur_skew
    if 'skew' in features.keys():
        features['skew'].append(cur_skew)
    else:
        features['skew'] = [cur_skew]

    cur_kurtosis = kurtosis(sig, fisher=True, bias=False)
    cur_kurtosis = 0 if isnan(cur_kurtosis) else cur_kurtosis
    if 'kurtosis' in features.keys():
        features['kurtosis'].append(cur_kurtosis)
    else:
        features['kurtosis'] = [cur_kurtosis]

    return features

def clear_workout_features(features) -> None:
    features = {
        'accel_x': {},
        'accel_y': {},
        'accel_z': {},
        'vel_x': {},
        'vel_y': {},
        'vel_z': {},
        'pos_x': {},
        'pos_y': {},
        'pos_z': {},
        'mag_x': {},
        'mag_y': {},
        'mag_z': {}
    }

    return features