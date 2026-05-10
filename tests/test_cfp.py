"""CFP format tests."""

import itertools
import multiprocessing
from pathlib import Path

from ts1_formats import bcf
from ts1_formats import cfp
from ts1_formats import cmx


KNOWN_MISSING_CFP_FILES = [
    "xskill-k2a-praise-get-toss",
    "xskill-k2o-cathouse-ground-lay-look-back",
    "xskill-k2o-cathouse-ground-sit-look-back",
    "xskill-k2o-cathouse-levelone-lay-look-back",
    "xskill-k2o-cathouse-levelone-sit-look-back",
    "xskill-k2o-cathouse-leveltwo-lay-look-back",
    "xskill-k2o-cathouse-leveltwo-sit-look-back",
    "xskill-k2o-sit-lookdown-start",
    "xskill-a2o-oxybar-sit-breathe",
    "xskill-a2o-magicarena-castspell-castee",
    "xskill-a2o-magicarena-castspell-caster",
    "xskill-a2o-punch-idle-handsknees-cry",
    "xskill-a2o-pup-bored-cool-idle-start",
    "xskill-a2o-pup-bored-cool-idle-loop",
    "xskill-a2o-pup-bored-cool-idle-wobbly-swagger",
    "xskill-a2o-pup-bored-cool-idle-shrug",
]


def read_cfps(cfp_file_list: list[Path], directory: Path, skills: list[bcf.Skill]) -> None:
    """Read all the cfp files in the specified skills."""
    for skill in skills:
        if skill.animation_name in KNOWN_MISSING_CFP_FILES:
            continue

        cfp_file_path = directory / (skill.animation_name + ".cfp")
        if not cfp_file_path.is_file():
            cfp_file_path = next(x for x in cfp_file_list if x.stem.lower() == skill.animation_name.lower())

        cfp.read_file(cfp_file_path, skill.position_count, skill.rotation_count)


def read_bcf(file_path: Path, cfp_file_list: list[Path]) -> None:
    """Read a bcf file and all the cfp files in the specified skills."""
    bcf_file = bcf.read_file(file_path)
    read_cfps(cfp_file_list, file_path.parents[0], bcf_file.skills)


def read_cmx(file_path: Path, cfp_file_list: list[Path]) -> None:
    """Read a cmx file and all the cfp files in the specified skills."""
    bcf_file = cmx.read_file(file_path)
    read_cfps(cfp_file_list, file_path.parents[0], bcf_file.skills)


def test_cfp(files_directory: str) -> None:
    """Test reading all cfp files in the specified directory."""
    cfp_file_list = list(Path(files_directory).rglob("*.cfp"))

    pool = multiprocessing.Pool(None)

    bcf_file_list = Path(files_directory).rglob("*.bcf")
    pool.starmap(read_bcf, zip(bcf_file_list, itertools.repeat(cfp_file_list)))

    cmx_file_list = Path(files_directory).rglob("*.cmx")
    pool.starmap(read_cmx, zip(cmx_file_list, itertools.repeat(cfp_file_list)))
