#!/usr/bin/env python3

import os.path

# Dependencies for video:
import os
from glob import glob
import io
from contextlib import redirect_stdout
import deeplabcut
import numpy as np

from .common import natural_keys, make_process_fun

from multiprocessing import Pool
from itertools import repeat


def rename_dlc_files(folder, base):
    files = glob(os.path.join(folder, base + "*"))
    for fname in files:
        basename = os.path.basename(fname)
        _, ext = os.path.splitext(basename)
        os.rename(os.path.join(folder, basename), os.path.join(folder, base + ext))


def process_session(config, session_path):
    pipeline_videos_raw = config["pipeline"]["videos_raw"]
    pipeline_pose = config["pipeline"]["pose_2d"]
    gpus = config["pipeline"]["gpus"]

    try:
        n_gpus = len(gpus)
    except:
        gpus = None
        n_gpus = 1

    config_name = os.path.join(config["model_folder"], "config.yaml")

    source_folder = os.path.join(session_path, pipeline_videos_raw)
    outdir = os.path.join(session_path, pipeline_pose)

    videos = glob(os.path.join(source_folder, "*.avi"))
    videos = sorted(videos, key=natural_keys)

    if len(videos) > 0:
        os.makedirs(outdir, exist_ok=True)

    videos_in_chunks = np.array_split(videos, n_gpus)

    with Pool(n_gpus) as p:
        p.starmap(
            process_gpu_batch,
            zip(repeat(config_name), videos_in_chunks, repeat(outdir), gpus),
        )


def process_gpu_batch(config_name, videos, outdir, gpu=None):

    for video in videos:
        basename = os.path.basename(video)
        basename, ext = os.path.splitext(basename)

        dataname = os.path.join(outdir, basename + ".h5")
        print(dataname)
        if os.path.exists(dataname):
            continue
        else:
            trap = io.StringIO()
            with redirect_stdout(trap):
                deeplabcut.analyze_videos(
                    config_name,
                    [video],
                    videotype=ext,
                    save_as_csv=True,
                    destfolder=outdir,
                    gputouse=gpu,
                )
        rename_dlc_files(outdir, basename)


pose_videos_all = make_process_fun(process_session)
