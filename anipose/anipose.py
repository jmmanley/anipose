#!/usr/bin/env python3

import os
import os.path
import toml
import click
import time

pass_config = click.make_pass_decorator(dict)

DEFAULT_CONFIG = {
    "calibration": {"animal_calibration": False},
    "pipeline": {
        "videos_raw": "videos-raw",
        "pose_2d": "pose-2d",
        "pose_2d_filter": "pose-2d-filtered",
        "pose_3d": "pose-3d",
        "videos_labeled_2d": "videos-labeled",
        "videos_labeled_2d_filter": "videos-labeled-filtered",
        "calibration_videos": "calibration",
        "calibration_results": "calibration",
        "videos_labeled_3d": "videos-3d",
        "angles": "angles",
        "summaries": "summaries",
        "videos_combined": "videos-combined",
        "gpus": 0,
        "npool": 1,
    },
    "filter": {
        "enabled": False,
        "medfilt": 13,
        "offset_threshold": 25,
        "score_threshold": 0.8,
        "spline": True,
    },
    "labeling": {"dot_size": 7},
}

pause_time = 300


def full_path(path):
    path_user = os.path.expanduser(path)
    path_full = os.path.abspath(path_user)
    path_norm = os.path.normpath(path_full)
    return path_norm


def load_config(fname):
    if fname is None:
        fname = "config.toml"

    if os.path.exists(fname):
        config = toml.load(fname)
    else:
        config = dict()

    # put in the defaults
    if "path" not in config:
        if os.path.exists(fname) and os.path.dirname(fname) != "":
            config["path"] = os.path.dirname(fname)
        else:
            config["path"] = os.getcwd()

    config["path"] = full_path(config["path"])

    if "project" not in config:
        config["project"] = os.path.basename(config["path"])

    for k, v in DEFAULT_CONFIG.items():
        if k not in config:
            config[k] = v
        elif isinstance(v, dict):  # handle nested defaults
            for k2, v2 in v.items():
                if k2 not in config[k]:
                    config[k][k2] = v2

    return config


@click.group()
@click.version_option()
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    help='The config file to use instead of the default "config.toml" .',
)
@click.pass_context
def cli(ctx, config):
    ctx.obj = load_config(config)


@cli.command()
@pass_config
def calibrate(config):
    from .calibrate_intrinsics import calibrate_intrinsics_all
    from .calibrate_extrinsics import calibrate_extrinsics_all

    click.echo("Calibrating...")
    calibrate_intrinsics_all(config)
    calibrate_extrinsics_all(config)


@cli.command()
@pass_config
def calibrate_intrinsics(config):
    from .calibrate_intrinsics import calibrate_intrinsics_all

    click.echo("Calibrating intrinsics...")
    calibrate_intrinsics_all(config)


@cli.command()
@pass_config
def calibrate_extrinsics(config):
    from .calibrate_extrinsics import calibrate_extrinsics_all

    click.echo("Calibrating extrinsics...")
    calibrate_extrinsics_all(config)


@cli.command()
@pass_config
def calibration_errors(config):
    from .calibration_errors import get_errors_all

    click.echo("Getting all the calibration errors...")
    get_errors_all(config)


@cli.command()
@pass_config
def analyze(config):
    from .pose_videos import pose_videos_all
    from .filter_pose import filter_pose_all

    click.echo("Analyzing videos...")

    while True:
        pose_videos_all(config)
        time.sleep(pause_time)


@cli.command()
@pass_config
def filter(config):
    from .filter_pose import filter_pose_all
    
    click.echo("Filtering tracked points...")
    filter_pose_all(config)


@cli.command()
@pass_config
def triangulate(config):
    from .triangulate import triangulate_all

    click.echo("Triangulating points...")
    triangulate_all(config)


@cli.command()
@pass_config
def angles(config):
    from .compute_angles import compute_angles_all

    click.echo("Computing angles...")
    compute_angles_all(config)


@cli.command()
@pass_config
def summarize_3d(config):
    from .summarize import summarize_angles, summarize_pose3d

    click.echo("Summarizing angles...")
    summarize_angles(config)

    click.echo("Summarizing 3D pose...")
    summarize_pose3d(config)


@cli.command()
@pass_config
def summarize_2d(config):
    from .summarize import summarize_pose2d, summarize_pose2d_filtered

    click.echo("Summarizing pose 2d...")
    summarize_pose2d(config)

    if config["filter"]["enabled"]:
        click.echo("Summarizing pose 2d filtered...")
        summarize_pose2d_filtered(config)


@cli.command()
@pass_config
def summarize_errors(config):
    from .summarize import summarize_errors

    click.echo("Summarizing errors...")
    summarize_errors(config)


@cli.command()
@pass_config
def label_2d(config):
    from .label_videos import label_videos_all

    click.echo("Labeling videos in 2D...")
    label_videos_all(config)


@cli.command()
@pass_config
def label_2d_filter(config):
    from .label_videos import label_videos_filtered_all
    from .summarize import summarize_pose2d, summarize_pose2d_filtered, summarize_errors
    from .filter_pose import filter_pose_all

    click.echo("Labeling (and summarizing) videos in 2D...")

    while True:
        summarize_pose2d(config)
    
        if config["filter"]["enabled"]:
            filter_pose_all(config)
            summarize_pose2d_filtered(config)

        summarize_errors(config)
    
        label_videos_filtered_all(config)
     
        time.sleep(pause_time)


@cli.command()
@pass_config
def label_3d(config):
    from .label_videos_3d import label_videos_3d_all

    click.echo("Labeling videos in 3D...")
    label_videos_3d_all(config)


@cli.command()
@pass_config
def label_combined(config):
    from .label_combined import label_combined_all

    click.echo("Labeling combined videos...")
    label_combined_all(config)


@cli.command()
@pass_config
def draw_calibration(config):
    from .common import get_calibration_board_image
    import cv2

    click.echo("Drawing calibration board...")
    img = get_calibration_board_image(config)
    cv2.imwrite("calibration.png", img)


@cli.command()
@pass_config
def run_data(config):
    from .calibrate_intrinsics import calibrate_intrinsics_all
    from .calibrate_extrinsics import calibrate_extrinsics_all
    from .pose_videos import pose_videos_all
    from .triangulate import triangulate_all

    click.echo("Calibrating...")
    calibrate_intrinsics_all(config)
    calibrate_extrinsics_all(config)

    click.echo("Analyzing videos...")
    pose_videos_all(config)

    click.echo("Triangulating points...")
    triangulate_all(config)

    click.echo("Running data processing")


@cli.command()
@pass_config
def run_viz(config):
    from .label_videos import label_videos_filtered_all, label_videos_all
    from .label_videos_3d import label_videos_3d_all

    click.echo("Labeling videos in 2D...")
    if config["filter"]["enabled"]:
        label_videos_filtered_all(config)
    else:
        label_videos_all(config)
    click.echo("Labeling videos in 3D...")
    label_videos_3d_all(config)


@cli.command()
@pass_config
def run_all(config):
    from .calibrate_intrinsics import calibrate_intrinsics_all
    from .calibrate_extrinsics import calibrate_extrinsics_all
    from .pose_videos import pose_videos_all
    from .triangulate import triangulate_all
    from .compute_angles import compute_angles_all

    click.echo("Calibrating...")
    calibrate_intrinsics_all(config)
    calibrate_extrinsics_all(config)

    click.echo("Analyzing videos...")
    pose_videos_all(config)

    if config["filter"]["enabled"]:
        from .filter_pose import filter_pose_all

        click.echo("Filtering tracked points...")
        filter_pose_all(config)

    click.echo("Triangulating points...")
    triangulate_all(config)

    click.echo("Computing angles...")
    compute_angles_all(config)

    from .label_videos import label_videos_filtered_all, label_videos_all
    from .label_videos_3d import label_videos_3d_all

    click.echo("Labeling videos in 2D...")
    if config["filter"]["enabled"]:
        label_videos_filtered_all(config)
    else:
        label_videos_all(config)
    click.echo("Labeling videos in 3D...")
    label_videos_3d_all(config)


@cli.command()
@pass_config
def check_progress(config):
    for i in range(3): print()
    print('Project:', config["project"])
    print()
    _check_progress(config)
   
def __check_progress(config, session_path):
    from glob import glob
    from .common import natural_keys, get_nframes

    pipeline_videos_raw = config['pipeline']['videos_raw']
    pipeline_pose = config['pipeline']['pose_2d']

    config_name = os.path.join(config['model_folder'], 'config.yaml')

    source_folder = os.path.join(session_path, pipeline_videos_raw)
    outdir = os.path.join(session_path, pipeline_pose)

    videos = glob(os.path.join(source_folder, '*.avi'))
    videos = sorted(videos, key=natural_keys)
    
    n_analyzed = 0
    n_labeled  = 0

    for video in videos:
        basename = os.path.basename(video)
        basename, ext = os.path.splitext(basename)
        
        dataname = os.path.join(outdir, basename + '.h5')
        
        if os.path.exists(dataname):   
            n_analyzed += 1
    
    pipeline_videos_labeled = config['pipeline']['videos_labeled_2d_filter']
    pipeline_pose = config['pipeline']['pose_2d_filter']

    labels_fnames = glob(os.path.join(session_path, pipeline_pose, '*.h5'))
    labels_fnames = sorted(labels_fnames, key=natural_keys)

    outdir = os.path.join(session_path, pipeline_videos_labeled)
    
    for fname in labels_fnames:
        basename = os.path.basename(fname)
        basename = os.path.splitext(basename)[0]
        out_fname = os.path.join(outdir, basename+'.avi')
        vidname = os.path.join(session_path, pipeline_videos_raw, basename+'.avi')
        if os.path.exists(vidname):
            if os.path.exists(out_fname) and \
               abs(get_nframes(out_fname) - get_nframes(vidname)) < 100:
                n_labeled += 1
    
    if len(videos)>0:
        print(os.path.basename(session_path))
        print('    Analyzed: ', n_analyzed, ' out of ', len(videos), ' videos.')
        print('    Labeled:  ', n_labeled, ' out of ', len(videos), ' videos.')

from .common import make_process_fun
_check_progress = make_process_fun(__check_progress)


if __name__ == "__main__":
    cli()
