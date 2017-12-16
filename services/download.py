from copy import copy
import os
from urllib.parse import urlparse

import numpy as np

from pytube import YouTube
from moviepy.video.tools.cuts import FramesMatch, FramesMatches

import fire


def download(url: str, output_dir: str, overwrite: bool = False) -> str:
    yt = YouTube(url)
    stream = yt.streams.filter(file_extension='mp4',
                               res='240p',
                               adaptive=True).first()
    #id = urlparse(url).query.lstrip('v=')
    #filename = '{}.{}'.format(id, stream.subtype)
    output_path = os.path.join(output_dir, stream.default_filename)
    if not overwrite and os.path.isfile(output_path):
        return output_path

    stream.download(output_path=output_dir)
    return output_path


def from_clip(clip, dist_thr, max_d, fps=None, dark_mean=100, dark_std=10):
    """ Finds all the frames tht look alike in a clip, for instance to make a
    looping gif.
    This teturns a  FramesMatches object of the all pairs of frames with
    (t2-t1 < max_d) and whose distance is under dist_thr.
    This is well optimized routine and quite fast.
    Examples
    ---------
    
    We find all matching frames in a given video and turn the best match with
    a duration of 1.5s or more into a GIF:
    >>> from moviepy.editor import VideoFileClip
    >>> from moviepy.video.tools.cuts import find_matching_frames
    >>> clip = VideoFileClip("foo.mp4").resize(width=200)
    >>> matches = find_matching_frames(clip, 10, 3) # will take time
    >>> best = matches.filter(lambda m: m.time_span > 1.5).best()
    >>> clip.subclip(best.t1, best.t2).write_gif("foo.gif")
    Parameters
    -----------
    clip
      A MoviePy video clip, possibly transformed/resized
    
    dist_thr
      Distance above which a match is rejected
    
    max_d
      Maximal duration (in seconds) between two matching frames
    
    fps
      Frames per second (default will be clip.fps)
    
    """ 
    
    N_pixels = clip.w * clip.h * 3
    dot_product = lambda F1, F2: (F1*F2).sum()/N_pixels
    F = {} # will store the frames and their mutual distances
    
    def distance(t1, t2):
        uv = dot_product(F[t1]['frame'], F[t2]['frame'])
        u, v = F[t1]['|F|sq'], F[t2]['|F|sq']
        return np.sqrt(u+v - 2*uv)
    
    matching_frames = [] # the final result.
    
    for (t,frame) in clip.iter_frames(with_times=True, progress_bar=True):
        if frame.mean() <= dark_mean and frame.mean(2).std() <= dark_std:
            continue

        flat_frame = 1.0*frame.flatten()
        F_norm_sq = dot_product(flat_frame, flat_frame)
        F_norm = np.sqrt(F_norm_sq)

        for t2 in list(F.keys()):
            # forget old frames, add 't' to the others frames
            # check for early rejections based on differing norms
            if (t-t2) > max_d:
                F.pop(t2)
            else:
                F[t2][t] = {'min':abs(F[t2]['|F|'] - F_norm),
                            'max':F[t2]['|F|'] + F_norm}
                F[t2][t]['rejected']= (F[t2][t]['min'] > dist_thr)
        
        t_F = sorted(F.keys())
        
        F[t] = {'frame': flat_frame, '|F|sq': F_norm_sq, '|F|': F_norm}
                
        for i,t2 in enumerate(t_F):
            # Compare F(t) to all the previous frames
            
            if F[t2][t]['rejected']:
                continue
            
            dist = distance(t, t2)
            F[t2][t]['min'] = F[t2][t]['max'] = dist
            F[t2][t]['rejected']  = (dist >= dist_thr)
            
            for t3 in t_F[i+1:]:
                # For all the next times t3, use d(F(t), F(t2)) to
                # update the bounds on d(F(t), F(t3)). See if you can
                # conclude on wether F(t) and F(t3) match.
                t3t, t2t3 = F[t3][t], F[t2][t3]
                t3t['max'] = min(t3t['max'], dist+ t2t3['max'])
                t3t['min'] = max(t3t['min'], dist - t2t3['max'],
                                 t2t3['min'] - dist)
                                      
                if t3t['min'] > dist_thr:
                    t3t['rejected'] = True
    
        # Store all the good matches (t2,t)
        matching_frames += [(t1, t, F[t1][t]['min'], F[t1][t]['max']) for t1 in F
                            if (t1!=t) and not F[t1][t]['rejected']]
                   
    return FramesMatches([FramesMatch(*e) for e in matching_frames])


if __name__ == '__main__':
    fire.Fire({'download': download})

