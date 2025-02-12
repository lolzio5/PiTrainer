import numpy as np
import json
from scipy.stats import skew, kurtosis
from rep_analysis import SetData

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


def process_rep_to_dict(accel3d, vel3d, pos3d, mag3d):
    accel = line_to_axes(accel3d)
    vel = line_to_axes(vel3d)
    pos = line_to_axes(pos3d)
    mag = line_to_axes(mag3d)

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
        'mag_x': extract_features(mag[0]),
        'mag_y': extract_features(mag[1]),
        'mag_z': extract_features(mag[2])
    }

    return data