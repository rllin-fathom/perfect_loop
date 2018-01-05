
from functools import partial
from itertools import islice, chain, tee
import os
import tempfile
from typing import Iterator, Tuple, List

import imageio
import numpy as np


def joint_entropy(channel1, channel2, range1, range2, bins):
    i1i2_hist, _, _ = np.histogram2d(channel1.flatten(),
                                     channel2.flatten(),
                                     bins=bins,
                                     range=[range1, range2])
    return entropy(i1i2_hist)


def hist_range(a, bins):
    '''Compute the histogram range of the values in the array a according to
    scipy.stats.histogram.'''
    a = np.asarray(a)
    a_max = a.max()
    a_min = a.min()
    s = 0.5 * (a_max - a_min) / float(bins - 1)
    return (a_min - s, a_max + s)


def entropy(hist):
    '''Compute entropy of the flattened data set (e.g. a density distribution).'''
    # normalize and convert to float
    hist = hist / float(np.sum(hist))
    # for each grey-value g with a probability p(g) = 0, the entropy is defined as 0, therefore we remove these values and also flatten the histogram
    hist = hist[np.nonzero(hist)]
    # compute entropy
    return -1. * np.sum(hist * np.log2(hist))


def windowing(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def np_rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def sum_yields(func):
    def wrapped(matrices, *args, **kwargs):
        return sum(ele for ele in func(matrices, *args, **kwargs))
    return wrapped


def apply_to_channel(func):
    def wrapped(matrices, *args, **kwargs):
        for channels in zip(*(np.rollaxis(matrix, 2) for matrix in matrices)):
            yield func(channels, *args, **kwargs)
    return wrapped


@apply_to_channel
def mutual_information(matrices, bins):
    h_ranges = [hist_range(matrix, bins) for matrix in matrices]

    hists = [np.histogram(matrix, bins=bins, range=h_range)
             for matrix, h_range in zip(matrices, h_ranges)]

    entropy_1, entropy_2 = tee((entropy(hist) for hist, _ in hists), 2)
    return (sum(entropy_1) - joint_entropy(*matrices, *h_ranges, bins),
            *entropy_2)


def video_to_mi(vid) -> Iterator[Tuple[float, float]]:
    """Window frames into pairs and apply mutual information."""
    num_frames = len(vid)

    windowed_frames = windowing(islice(vid, num_frames), 2)
    bin_ents = partial(mutual_information, bins=256)
    for idx, (mii, ent, *_) in enumerate(map(bin_ents, windowed_frames)):
        print('sum: ', sum(mii), sum(ent))
        yield (sum(mii), sum(ent))


def trimmed_local_mean(data,
                       window_len: int,
                       threshold: float) -> Iterator[int]:
    """Yields index where there is a sudden dip in mutual information."""
    m = np.ones(window_len)
    t_c = window_len // 2
    m[t_c] = 0
    for idx, data_part in enumerate(windowing(data, window_len)):
        mis, ents = zip(*data_part)
        if sum(m * mis) / (window_len - 1) / mis[t_c] >= threshold:
            yield idx + t_c


def segments(boundaries,
             min_frames: int,
             offset: float = None,
             limit: float = None) -> Iterator[Tuple[int, int]]:
    """Return boundary (start, end) when start - end >= min_frames.

    With offset and limit %.

    """
    for start, end in windowing(boundaries, 2):
        if offset:
            assert 0.0 <= offset <= 1.0
            start += int((end - start) * offset)
        if limit:
            assert 0.0 <= limit <= 1.0
            end = start + int((end - start) * limit)
        if end - start >= min_frames:
            yield (start, end)


def scenes_to_images(vid, scenes):
    frame_idx = 0
    vid_iter = vid.iter_data()
    for start_frame, end_frame in scenes:
        scene_len = int(end_frame - start_frame - 1)
        while not (start_frame < frame_idx < end_frame):
            frame = next(vid_iter)
            frame_idx += 1
        images = [frame for frame in islice(vid_iter, scene_len)]
        print('len(images): ', len(images))
        yield images, start_frame, end_frame
        frame_idx += scene_len


def scenes_to_gif(vid, scenes, fps):
    for images, start_frame, end_frame in scenes_to_images(vid, scenes):
        out_path = '{}_{}.gif'.format(start_frame, end_frame)
        to_gif(images, out_path, fps)
        yield out_path


def scenes_to_s3(vid, scenes, fps, s3, upload_dir):
    for images, start_frame, end_frame in scenes_to_images(vid, scenes):
        out_path = '{}_{}.gif'.format(start_frame, end_frame)
        to_gif(images, out_path, fps)
        file_path = s3.upload(out_path, upload_dir=upload_dir)
        print('uploaded:', file_path)
        yield file_path


def to_gif(images, output_path, fps):
    imageio.mimsave(output_path, images, fps=fps)


def video_to_gifs(file_path: str):
    vid = imageio.get_reader(file_path, 'ffmpeg')
    print('read video')
    mis = video_to_mi(vid)
    boundaries = trimmed_local_mean(mis, 24, 1.4)
    segs = segments(boundaries, 48)
    return list(scenes_to_gif(vid, segs, fps=48))


def video_to_s3(file_path: str, s3, max_gifs = 1):
    vid = imageio.get_reader(file_path, 'ffmpeg')
    print('read video')
    mis = video_to_mi(vid)
    boundaries = trimmed_local_mean(mis, 24, 1.4)
    segs = segments(boundaries, 48)
    print('upload_dir: ', os.path.basename(os.path.dirname(file_path)))
    return list(
        islice(
            scenes_to_s3(vid, segs, 48, s3, os.path.basename(os.path.dirname(file_path))),
            1))


def scenes_to_summary(vid, scenes, fps, upload_dir, max_scenes):
    print('max_scenes: ', type(max_scenes))
    scenes_images = islice(scenes_to_images(vid, scenes), max_scenes)
    # TODO: replace with a gif writer that can write frame by frame.
    images = list(chain.from_iterable(scene
                                      for scene, _, _ in scenes_images))
    return images


def video_to_summary(file_path: str,
                     gfy_client,
                     min_scene_secs: int,
                     max_scenes: int) -> Iterator[str]:
    upload_dir = os.path.basename(os.path.dirname(file_path))

    vid = imageio.get_reader(file_path, 'ffmpeg')
    mis_and_ents = video_to_mi(vid)
    boundaries = trimmed_local_mean(mis_and_ents, window_len=24, threshold=1.4)
    segs = segments(boundaries,
                    min_frames=int(24 * min_scene_secs),
                    offset=0.15)
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = os.path.join(tmp_dir, 'summary.gif')
        yield 'process'
        images = scenes_to_summary(vid=vid,
                                   scenes=segs,
                                   fps=24,
                                   upload_dir=upload_dir,
                                   max_scenes=max_scenes)
        yield 'saving'
        to_gif(images, out_path, 24)
        yield 'upload'
        gfy_client.upload_from_file(file_path=out_path)



