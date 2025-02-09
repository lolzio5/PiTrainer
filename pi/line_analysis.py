import numpy as np
from filtering import MovingAverage

def distance_pnt2pnt(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    return np.linalg.norm(np.array(p1) - np.array(p2))
    # return np.sqrt( (p1[0] - p2[0])**2 + (p1[1] - p1[1])**2 + (p1[2] - p2[2])**2 )

def closest_point_on_line(point: tuple[float, float, float], line: list[tuple[float, float, float]]):
    min_dist: float = np.inf
    closest_point: tuple[float, float, float] = None
    for linept in line:
        dist: float = distance_pnt2pnt(point, linept)
        if dist < min_dist:
            min_dist = dist
            closest_point = linept

    return closest_point, min_dist

def average_line(points, num_points=200):
    avx = MovingAverage(num_points)
    avy = MovingAverage(num_points)
    avz = MovingAverage(num_points)

    return [ 
        (
            avx.update(points[i][0]),
            avy.update(points[i][1]),
            avz.update(points[i][2])
        )
        for i in range(len(points))
     ]

def zscore(data: list[float]) -> float:
    # chanign to np arrays will allow for multi dimensional arrays
    return (np.array(data) - np.mean(data)) / np.std(data)

#Not used?
def get_average_rep(data: list[ list[ list[float, float, float] ] ]) -> list[ list[float, float, float]]:
    # data is a list of reps ie. a list of list of points
    # average each point in each rep
    return [ (
            np.mean([point[0] for point in rep]),
            np.mean([point[1] for point in rep]),
            np.mean([point[2] for point in rep]) ) 
        for rep in data
        ]

def distance_analysis(pos: list[ list[float, float, float] ]):
    av_line = average_line(pos, num_points=100)

    min_dists = []
    for point in pos:
        _, dist = closest_point_on_line(point=point, line=av_line)
        min_dists.append(dist)

    sd = np.std(min_dists)
    dist_range = np.max(min_dists) - np.min(min_dists)
    mean = np.mean(min_dists)
    median = np.median(min_dists)

    return min_dists, sd, dist_range

def get_pos_scores(pos_reps):
    pos_scores = []
    for pos_rep in pos_reps:
        min_dists, sd, dist_range = distance_analysis(pos_rep)
        score = zscore(min_dists)
        pos_scores.append(score)

    # normalize scores - 0 to 100
    score_range = np.max(pos_scores) - np.min(pos_scores)
    pos_scores = [ 100*(score - np.min(pos_scores)) // score_range for score in pos_scores]

    return pos_scores

## RETHINK
def overall_score(vel_based_scores, pos_based_scores, mag_based_scores):
    final_score = []
    # CHECK SAME LENGTH
    if len(vel_based_scores) == len(pos_based_scores) == len(mag_based_scores):

        # coefficients may be adjusted
        for i in range(vel_based_scores):
            final_score.append(
                0.6*pos_based_scores[i] + 0.3*vel_based_scores[i] + 0.1*mag_based_scores[i]
            )

        return final_score
    else:
        return "Invalid Input"


