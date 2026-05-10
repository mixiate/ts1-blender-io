"""CFP format tests."""

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


def test_cfp(files_directory: str) -> None:
    """Test reading all cfp files in the specified directory."""
    cfp_file_list = list(Path(files_directory).rglob("*.cfp"))

    bcf_file_list = Path(files_directory).rglob("*.bcf")
    for bcf_file_path in bcf_file_list:
        bcf_file = bcf.read_file(bcf_file_path)

        read_cfps(cfp_file_list, bcf_file_path.parents[0], bcf_file.skills)

    cmx_file_list = Path(files_directory).rglob("*.cmx")
    for cmx_file_path in cmx_file_list:
        bcf_file = cmx.read_file(cmx_file_path)

        read_cfps(cfp_file_list, cmx_file_path.parents[0], bcf_file.skills)
