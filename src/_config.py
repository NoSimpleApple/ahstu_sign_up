import configparser
import pathlib
from typing import TypeAlias


ConfPath: TypeAlias = pathlib.Path


def config(cfgs_path_root: ConfPath):
    path = pathlib.Path(cfgs_path_root)
    if not (cfgs_path_list := sorted(path.glob("*.ini"))):
        raise FileNotFoundError(f"there is no valid configure file found"
                                f" in path {path.resolve(strict=False)}")

    def read_cfg(cfg_path):
        cfg = configparser.ConfigParser()
        cfg.optionxform = lambda optionstr: optionstr
        cfg.read(cfg_path, encoding="utf-8")
        return cfg

    return map(read_cfg, cfgs_path_list)
