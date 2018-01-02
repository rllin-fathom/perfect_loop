import concurrent.futures as futures
from functools import partial
from itertools import islice, count
import multiprocessing as mpu
import time

import imageio
import numpy as np
import pywren

import mi

bins = 256
file_path = 'gangnam.mp4'
num_frames = 5
matrices = imageio.get_reader(file_path, 'ffmpeg')

    def mi_per_frames(channels, bins):
        return sum(mutual_information(channels, bins))

    mi_func = partial(mi_per_frames, bins=bins)

    channels = zip(*(np.rollaxis(matrix, 2) for matrix in matrices))
    frames = next(channels)
    print(len(frames))
    frames = next(channels)
    print(len(frames))
    print(frames[0].shape)

    pwex = pywren.default_executor()
    print('submitting')
    def mean(channels):
        return np.mean(channels)
    def increment(x):
        return x + 1

    futures = pwex.map(increment, range(10))
    #futures = pwex.map(mean, islice(channels, num_frames))
    #futures = pwex.map(mi_func, channels)
    print('submitted')

    now = time.time()
    result = pywren.get_all_results(futures)
    elapsed = time.time() - now

    print(elapsed, 'total seconds for', num_frames, 'frames')
    print(elapsed / num_frames, 'seconds per frame')

    print(result)
