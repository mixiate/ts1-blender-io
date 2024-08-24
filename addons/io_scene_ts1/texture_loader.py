"""Find and load textures for imported meshes."""

import bpy
import pathlib
import re


def is_head_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is a head."""
    return re.match("^xskin-c\\d{3}(f|m|u)(a|c)_.*-head-head$", skin_name.lower())


def is_body_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is a body."""
    return re.match("^xskin-(b|f|h|l|s|w)\\d{3}(f|m|u)(a|c)(skn|fit|fat|chd).*-pelvis-body$", skin_name.lower())


def is_hand_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is a hand."""
    return re.match("^xskin-h(u|f|m)(l|r)(c|o|p)-(l|r)_hand-(fist|hand|point)(f|m|c)(l|r)$", skin_name.lower())


def is_nude_body_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is a nude body."""
    return re.match("^xskin-n(f|m|u)(skn|fit|fat|chd)_01-pelvis-.*body.*", skin_name.lower())


def is_npc_head_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is an npc head."""
    return re.match("^xskin-c((?!\\d{3}).).*(f|m|u)(a|c)_.*-head-head$", skin_name.lower())


def is_sex_npc_head_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is an npc head with sex indicator."""
    return re.match("^xskin-c((?!\\d{3}).).*(f|m|u)_.*-head-head$", skin_name.lower())


def is_weight_npc_head_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is an npc head with weight indicator."""
    return re.match("^xskin-c((?!\\d{3}).).*(f|m|u)(skn|fit|fat)_.*-head-head$", skin_name.lower())


def is_age_weight_npc_head_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is an npc head with age and weight indicators."""
    return re.match("^xskin-c((?!\\d{3}).).*(f|m|u)(a|c)(skn|fit|fat)_.*-head-head$", skin_name.lower())


def is_npc_body_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is an npc body."""
    return re.match("^xskin-((?!\\d{3}).).*(f|m|u)(a|c|)(skn|fit|fat|chd)_.*-pelvis-body$", skin_name.lower())


def is_unleashed_npc_body_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is an unleashed npc body."""
    return re.match("xskin-b((?!\\d{3}).).*_01-pelvis-body$", skin_name.lower())


def is_costume_body_skin_type(skin_name: str) -> re.Match | None:
    """Return a regex match if the skin type is a costume body."""
    return re.match("^xskin-ct-.*-pelvis-body$", skin_name.lower())


def list_head_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for a head skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = []

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = None if len(split_skin_name) == 1 else split_skin_name[1]

    body_id = skin_type[1:4]
    sex = skin_type[4]
    age = skin_type[5]

    for skin_color in skin_colors:
        if name is not None:
            texture_names.append(("c" + body_id + sex + age + skin_color + "_" + name).lower())

        texture_names.append(("c" + body_id + sex + age + skin_color + "_").lower())

    return texture_names


def list_body_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for a body skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = []

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = None if len(split_skin_name) == 1 else split_skin_name[1]

    clothes = skin_type[0]
    body_id = skin_type[1:4]
    sex = skin_type[4]
    age = skin_type[5]
    weight = skin_type[6:9]

    for skin_color in skin_colors:
        if name is not None:
            texture_names.append((clothes + body_id + sex + age + weight + skin_color + "_" + name).lower())

        texture_names.append((clothes + body_id + sex + age + weight + skin_color + "_").lower())

    return texture_names


def list_hand_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for a hand skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    split_skin_name = skin_name.split("-")

    hand_sex = split_skin_name[1][1]
    hand_side = split_skin_name[1][2]
    hand_position = split_skin_name[1][3]

    texture_names: list[str] = []

    for sex in ["u", hand_sex.lower()]:
        for side in ["a", hand_side, "c"]:
            texture_names.extend(("h" + sex + side + hand_position + skin_color).lower() for skin_color in skin_colors)

            texture_names.append(("h" + sex + side + hand_position).lower())
            texture_names.append(("g" + sex + side + hand_position).lower())
            texture_names.append(("_g" + sex + side + hand_position).lower())

    return texture_names


def list_nude_body_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for a nude body skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = []

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    sex = skin_type[1]
    weight = skin_type[2:5]

    for skin_color in skin_colors:
        texture_names.append(("n" + sex + weight + skin_color + "_" + name).lower())
        texture_names.append(("u" + sex + weight + skin_color + "_" + name).lower())
        texture_names.append(("n" + sex + weight + skin_color + "_").lower())
        texture_names.append(("u" + sex + weight + skin_color + "_").lower())

        if sex.lower() == "u":
            texture_names.append(("n" + "f" + weight + skin_color).lower())
            texture_names.append(("n" + "m" + weight + skin_color).lower())
            texture_names.append(("u" + "f" + weight + skin_color).lower())
            texture_names.append(("u" + "m" + weight + skin_color).lower())

    return texture_names


def list_npc_head_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for an npc head skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    split_skin_name = re.search("(?<=xskin-).*(?=-head-head)", skin_name.lower()).group(0).split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    return [(skin_type + skin_color + "_" + name).lower() for skin_color in skin_colors]


def list_age_weight_npc_head_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for an npc head with age and weight skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = []

    split_skin_name = re.search("(?<=xskin-).*(?=-head-head)", skin_name.lower()).group(0).split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    for skin_color in skin_colors:
        texture_names.append((skin_type + skin_color + "_" + name).lower())
        texture_names.append((skin_type[:-3] + skin_color + "_" + name).lower())

    return texture_names


def list_npc_body_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for an npc body skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = []

    split_skin_name = skin_name.lower().removeprefix("xskin-").removesuffix("-pelvis-body")
    sex_age_weight_span = re.search("(f|m|u)(a|c|)(skn|fit|fat|chd)_", split_skin_name.lower()).span()
    skin_type = split_skin_name[: sex_age_weight_span[1] - 1]
    name = split_skin_name[sex_age_weight_span[1] :]

    texture_names.append((skin_type + "_" + name).lower())
    texture_names.append(("b" + skin_type + "_" + name).lower())

    for skin_color in skin_colors:
        texture_names.append((skin_type + skin_color + "_" + name).lower())
        texture_names.append((skin_type[:-3] + skin_color + "_" + name).lower())

        if name == "01":
            texture_names.append((skin_type + skin_color + "_").lower())

    return texture_names


def list_unleashed_npc_body_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for an unleashed npc body skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    return [(skin_type + skin_color + "_" + name).lower() for skin_color in skin_colors]


def list_costume_body_texture_variants(skin_name: str, preferred_skin_color: str) -> list[str]:
    """List potential texture file names for a costume body skin."""
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    split_skin_name = skin_name.split("-")

    skin_type = split_skin_name[1]
    for element in split_skin_name[2:-3]:
        skin_type += "-" + element

    identifier = split_skin_name[-3]

    texture_names = []

    for skin_color in skin_colors:
        texture_name = skin_type + skin_color + "-" + identifier
        texture_names.append(texture_name.lower())

    return texture_names


def create_material(obj: bpy.types.Object, texture_name: str, texture_file_path: pathlib.Path) -> None:
    """Load the texture file, create a Blender material using it and add it to a material slot in the object."""
    if texture_name.lower() in ["white", "grey"]:
        texture_name = texture_name.lower()

    material_list = [material.name.casefold() for material in bpy.data.materials]
    try:
        material_index = material_list.index(texture_name.casefold())
        material = bpy.data.materials[material_index]
    except ValueError as _:
        material = None

    if material is None:
        if texture_name == "grey":
            material = bpy.data.materials.new(name=texture_name.lower())
            material.use_nodes = True

            principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
            principled_bsdf.inputs[0].default_value = (0.2, 0.2, 0.2, 1.0)
            principled_bsdf.inputs[2].default_value = 1.0
            principled_bsdf.inputs[12].default_value = 0.0

        elif texture_name == "white":
            material = bpy.data.materials.new(name=texture_name)
            material.use_nodes = True

            principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
            principled_bsdf.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
            principled_bsdf.inputs[2].default_value = 1.0
            principled_bsdf.inputs[12].default_value = 0.0

        else:
            material = bpy.data.materials.new(name=texture_name)

            image = bpy.data.images.get(texture_file_path.as_posix())
            if image is None:
                image = bpy.data.images.load(texture_file_path.as_posix())
            material.use_nodes = True

            image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            image_node.image = image

            principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
            material.node_tree.links.new(image_node.outputs[0], principled_bsdf.inputs[0])
            principled_bsdf.inputs[2].default_value = 1.0
            principled_bsdf.inputs[12].default_value = 0.0

            if texture_file_path.suffix.lower() == ".tga":
                material.node_tree.links.new(image_node.outputs[1], principled_bsdf.inputs[4])
                material.blend_method = 'BLEND'

    if material.name not in obj.data.materials:
        obj.data.materials.append(material)


def fix_texture_file_name(texture_file_name: str) -> str:
    """Fix texture file name mistakes in The Sims."""
    fixed_texture_file_names = {
        "B204MAFaMedFat_PeasantMan": "B204MAFatMed_FatPeasantMan",
        "CCookMfatgt_Chef": "CCookMfatlgt_Chef",
        "C209MA_TattooMandrk": "C209MAdrk_TattooMan",
        "C209MA_TattooManmed": "C209MAmed_TattooMan",
        "C209MA_TattooManlgt": "C209MAlgt_TattooMan",
        "CWAITMfitdrk_Xfancy": "CWAITMdrk_Xfancy",
        "CWAITMfitmed_Xfancy": "CWAITMmed_Xfancy",
        "CWAITMfitlgt_Xfancy": "CWAITMlgt_Xfancy",
        "b823faskntlgt_blacklayertee": "b823fasknlgt_blacklayertee",
        "b823faskntmed_blacklayertee": "b823fasknmed_blacklayertee",
    }

    return fixed_texture_file_names.get(texture_file_name, texture_file_name)


def reduce_texture_file_list(
    texture_file_list: list[pathlib.Path],
    texture_file_names: list[str],
    *,
    fix_textures: bool,
) -> list[pathlib.Path]:
    """Reduce the list of texture files to only those that match the given list."""
    zipped_texture_file_names = list(zip(texture_file_names, range(len(texture_file_names))))
    reduced_texture_file_list: list[tuple[pathlib.Path, int]] = []

    for file_path in texture_file_list:
        file_texture_name = file_path.stem
        if fix_textures:
            file_texture_name = fix_texture_file_name(file_texture_name)

        reduced_texture_file_list.extend(
            (file_path, texture_name[1])
            for texture_name in zipped_texture_file_names
            if file_texture_name.lower().startswith(texture_name[0].lower())
        )

    if len(reduced_texture_file_list) == 0:
        return []

    reduced_texture_file_list.sort(key=lambda x: x[1])
    return list(next(zip(*reduced_texture_file_list)))


def fixup_skin_name_and_default_texture(skin_name: str, default_texture: str) -> tuple[str, str]:
    """Fix mistakes in the skin name and default texture in files from The Sims 1."""
    # base game
    if skin_name == "xskin-b001fcchd_01-PELVIS-BODYCHD":
        skin_name = "xskin-b001fcchd_01-PELVIS-BODY"

    if skin_name == "xskin-b001mcchd_01-PELVIS-BODYCHD":
        skin_name = "xskin-b001mcchd_01-PELVIS-BODY"

    if skin_name == "xskin-b011fcchd_01-PELVIS-BODYCHD":
        skin_name = "xskin-b011fcchd_01-PELVIS-BODY"

    if skin_name == "xskin-b011ucchd_01-PELVIS-BODYCHD":
        skin_name = "xskin-b011ucchd_01-PELVIS-BODY"

    if skin_name == "xskin-c001ma_ross-HEAD-HEADB":
        skin_name = "xskin-c001ma_ross-HEAD-HEAD"

    if skin_name == "xskin-c_firefighter-HEAD-HEAD":
        default_texture = "C_Firefighter"

    if skin_name == "xskin-c_pizzaguy-HEAD-HEAD":
        default_texture = "pizzaguyface"

    if skin_name == "xskin-c_postal-HEAD-HEAD":
        default_texture = "Postalface"

    if skin_name == "xskin-militaryffit_01-PELVIS-MBODY":
        skin_name = "xskin-militaryffit_01-PELVIS-BODY"

    # house party
    if skin_name == "xskin-b046fafit_cowg-PELVIS-MBODY5":
        skin_name = "xskin-b046fafit_cowg-PELVIS-BODY"

    if skin_name == "xskin-B721MC_ct-PELVIS-BODY":
        skin_name = "xskin-B721MCChd_ct-PELVIS-BODY"

    if skin_name == "xskin-B722MC_ct-PELVIS-BODY":
        skin_name = "xskin-B722MCChd_ct-PELVIS-BODY"

    if skin_name == "xskin-B723FC_ct-PELVIS-BODY":
        skin_name = "xskin-B723FCChd_ct-PELVIS-BODY"

    if skin_name == "xskin-B724FC_ct-PELVIS-BODY":
        skin_name = "xskin-B724FCChd_ct-PELVIS-BODY"

    if skin_name == "xskin-B724FC_ct-PELVIS-BODY":
        skin_name = "xskin-B724FCChd_ct-PELVIS-BODY"

    if skin_name == "xskin-cpcrasherma_01-HEAD-HEAD":
        default_texture = "cPCrasherMA-01"

    if skin_name == "xskin-pcrasherma_01-PELVIS-BODY":
        default_texture = "PCrasher-MA-01"

    # vacation
    if skin_name == "xskin-C506MC_Swim1-HEAD-HEAD01":
        skin_name = "xskin-C506MC_Swim1-HEAD-HEAD"

    if skin_name == "xskin-C507FC_Swim2-HEAD-HEAD01":
        skin_name = "xskin-C507FC_Swim2-HEAD-HEAD"

    # unleashed:
    if skin_name in {"xskin-B008dog_greyhound-PELVIS-DOGBODY", "xskin-B008dog_greyhound-HEAD-DOGBODY-HEAD"}:
        default_texture = "b008dog_greyhound"

    if skin_name == "xskin-b000kat_orangetabby-HEAD-CATJAW":
        default_texture = "cathead"

    if skin_name == "xskin-b000kat_orangetabby-PELVIS-BODY":
        default_texture = "catbody"

    if skin_name == "xskin-CGardener_MaFat_Unleashed-HEAD-HEAD":
        default_texture = "cgardener_ma_unleashed"

    # superstar
    if skin_name == "xskin-csuperstarfa_bandannarocker-HEAD-HEAD":
        skin_name = "xskin-c550fa_bandannarocker-HEAD-HEAD"

    if skin_name == "xskin-csuperstarfa_rockerchick-HEAD-HEAD":
        skin_name = "xskin-C558FA_rockerchick-HEAD-HEAD"

    if skin_name == "xskin-CSuperstarMA_Photographer-HEAD-HEAD":
        skin_name = "xskin-CSuperstarMASkn_Photographer-HEAD-HEAD"

    if skin_name == "xskin-CSuperstarFA_SushiChef-HEAD-HEADF01":
        skin_name = "xskin-CSuperstarFA_SushiChef-HEAD-HEAD"

    # makin magic
    if skin_name == "xskin-B203FAFit_Suffragette-PELVIS-BODY01":
        skin_name = "xskin-B203FAFit_Suffragette-PELVIS-BODY"

    if skin_name == "xskin-B205FAFat_Madame-PELVIS-BODY01":
        skin_name = "xskin-B205FAFat_Madame-PELVIS-BODY"

    if skin_name == "xskin-B208FAFit_Jenna-PELVIS-BODY01":
        skin_name = "xskin-B208FAFit_Jenna-PELVIS-BODY"

    if skin_name == "xskin-C203FC_CreepyBen-HEAD-HEAD":
        skin_name = "xskin-C203MC_CreepyBen-HEAD-HEAD"

    if skin_name == "xskin-CMagicFAFit_BlueGenie-HEAD-HEAD":
        default_texture = "CMagicFA_BlueGenie"

    if skin_name == "xskin-magic-wizeyelashes-R_HAND-WAX_JAR01":
        default_texture = "wizeyelash"

    if skin_name == "xskin-magic-wizeyelashes-R_HAND-WAX_JAR08":
        default_texture = "wizeyelash"

    # expansion shared
    if skin_name == "xskin-S100FCChd_original-PELVIS-BODYU":
        skin_name = "xskin-S100FCChd_original-PELVIS-BODY"

    if skin_name == "xskin-S100MCChd_original-PELVIS-BODYU":
        skin_name = "xskin-S100MCChd_original-PELVIS-BODY"

    if skin_name == "xskin-W504FAfat_Winter4-PELVIS-BODY_FAT_WINTER4":
        skin_name = "xskin-W504FAfat_Winter4-PELVIS-BODY"

    if skin_name == "xskin-W504FAfit_Winter4-PELVIS-BODY_FIT_WINTER4":
        skin_name = "xskin-W504FAfit_Winter4-PELVIS-BODY"

    if skin_name == "xskin-W504FAskn_Winter4-PELVIS-BODY_SKN_WINTER4":
        skin_name = "xskin-W504FAskn_Winter4-PELVIS-BODY"

    # official downloads
    if skin_name in {"xskin-B015dog_pug-HEAD-DOGBODY-HEAD", "xskin-B015dog_pug-PELVIS-DOGBODY"}:
        default_texture = "B015dog_pug"

    if skin_name == "xskin-b200mafit_ctb-PELVIS-BODYB":
        skin_name = "xskin-b200mafit_ctb-PELVIS-BODY"

    if skin_name == "xskin-B619MA_FlameTroop-PELVIS-BODY":
        default_texture = "B619MAFATlgt_FlameTroop"

    if skin_name == "xskin-B621MAFIT_NOD_RTRPR-PELVIS-BODY_FIT":
        default_texture = "B621MAFITlgt_RTRPR"

    if skin_name == "xskin-C609MA_rocketofficer-HEAD-HEADSET":
        default_texture = "B609_rocketofficerheadset"

    if skin_name == "xskin-C630MA_Locke-HEAD-HEAD01":
        skin_name = "xskin-C630MA_Locke-HEAD-HEAD"

    if skin_name == "xskin-C634FA_Petrova-HEAD-HEAD.03":
        skin_name = "xskin-C634FA_Petrova-HEAD-HEAD"

    return skin_name, default_texture


def add_job_and_npc_textures(texture_names: list[str], skin_name: str, preferred_skin_color: str) -> None:
    """Add any job and npc textures for the given skin to the list of texture names."""
    # base game
    if skin_name.startswith("xskin-b001ma"):
        texture_names += list_npc_body_texture_variants("xskin-ExtremeMfit_01-pelvis-body", preferred_skin_color)

    if skin_name == "xskin-b002fafat_01-PELVIS-BODY":
        texture_names.append("GardenerFFat_01".lower())

    if skin_name.startswith("xskin-b002ma"):
        texture_names += list_npc_body_texture_variants("xskin-PoliceMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-ScrubsMfit_01-pelvis-body", preferred_skin_color)

    if skin_name == "xskin-b002mafit_01-PELVIS-BODY":
        texture_names.append("pizzaguysuit".lower())

    if skin_name.startswith("xskin-b003fa"):
        texture_names += list_npc_body_texture_variants("xskin-BurglarFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-CatsuitFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-EMTFfit_01-pelvis-body", preferred_skin_color)

    if skin_name.startswith("xskin-b003ma"):
        texture_names += list_npc_body_texture_variants("xskin-BurglarMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-EMTMfit_01-pelvis-body", preferred_skin_color)

    if skin_name == "xskin-b003mafat_01-PELVIS-BODY":
        texture_names.append("HandyMFat_01".lower())

    if skin_name == "xskin-b003mafit_01-PELVIS-BODY":
        texture_names.append("Postalsuit".lower())

    if skin_name.startswith("xskin-b004ma"):
        texture_names += list_npc_body_texture_variants("xskin-BusinessMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-MayorMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-PoliticsMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-SciMidMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-TopCopMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-TopDocMfit_01-pelvis-body", preferred_skin_color)

    if skin_name == "xskin-b005mafit_01-PELVIS-BODY":
        texture_names.append("RepoMFit_01".lower())

    if skin_name.startswith("xskin-b008fa"):
        texture_names += list_npc_body_texture_variants("xskin-BusinessFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-MayorFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-PoliticsFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-TopCopFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-TopDocFfit_01-pelvis-body", preferred_skin_color)

    if skin_name.startswith("xskin-b009fa"):
        texture_names += list_npc_body_texture_variants("xskin-SciMidFfit_01-pelvis-body", preferred_skin_color)

    if skin_name == "xskin-b004ucchd_01-PELVIS-BODY":
        texture_names += list_npc_body_texture_variants("xskin-MilCadetUfit_01-pelvis-body", preferred_skin_color)

    if skin_name.startswith("xskin-b011fa"):
        texture_names += list_npc_body_texture_variants("xskin-ExtremeFfit_01-pelvis-body", preferred_skin_color)

    if skin_name.startswith("xskin-b012fa"):
        texture_names += list_npc_body_texture_variants("xskin-PoliceFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-ScrubsFfit_01-pelvis-body", preferred_skin_color)

    if skin_name == "xskin-c004fa_gma1-HEAD-HEAD":
        texture_names.append("C_socwkr".lower())

    if skin_name == "xskin-c003ma_romancrew-HEAD-HEAD":
        texture_names.append("C_Handy".lower())
        texture_names.append("C_Repo".lower())

    if skin_name == "xskin-c_skeleton-HEAD-HEAD":
        texture_names += ["C_skeleton".lower(), "C_skeleneg".lower()]

    if skin_name in {"xskin-skeleton_01-PELVIS-BODY", "xskin-skeletonchd_01-PELVIS-BODY"}:
        texture_names += ["Skeleton_01".lower(), "Skeleneg_01".lower()]

    # livin large
    if skin_name.startswith("xskin-b004ma"):
        texture_names += list_npc_body_texture_variants("xskin-HypnotistMfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-UFOinvestMfit_01-pelvis-body", preferred_skin_color)

    if skin_name.startswith("xskin-b008fa"):
        texture_names += list_npc_body_texture_variants("xskin-infoverlordFfit_01-pelvis-body", preferred_skin_color)
        texture_names += list_npc_body_texture_variants("xskin-UFOinvestFfit_01-pelvis-body", preferred_skin_color)

    # house party
    if skin_name == "xskin-nffit_01-PELVIS-MBODY":
        texture_names += ["b_fa_eurotrash_swim", "b_fa_eurotrash_nekkid"]

    # unleashed
    if skin_name == "xskin-Petjudge_Mafit_01-PELVIS-BODY":
        texture_names += list_npc_body_texture_variants("xskin-Petjudge_Mafit_02-pelvis-body", preferred_skin_color)


def load_textures(
    obj: bpy.types.Object,
    texture_file_list: list[pathlib.Path],
    skin_name: str,
    default_texture: str,
    preferred_skin_color: str,
    *,
    fix_textures: bool,
) -> None:
    """Find and load all the applicable textures for the given skin, create materials and add them to the object."""
    texture_file_names: list[str] = []
    find_secondary_textures = False

    if fix_textures:
        skin_name, default_texture = fixup_skin_name_and_default_texture(skin_name, default_texture)

    if is_head_skin_type(skin_name):
        texture_file_names += list_head_texture_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif is_body_skin_type(skin_name):
        texture_file_names += list_body_texture_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif is_hand_skin_type(skin_name):
        texture_file_names += list_hand_texture_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif is_nude_body_skin_type(skin_name):
        texture_file_names += list_nude_body_texture_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif (
        is_npc_head_skin_type(skin_name)
        or is_sex_npc_head_skin_type(skin_name)
        or is_weight_npc_head_skin_type(skin_name)
    ):
        texture_file_names += list_npc_head_texture_variants(skin_name, preferred_skin_color)
    elif is_age_weight_npc_head_skin_type(skin_name):
        texture_file_names += list_age_weight_npc_head_texture_variants(skin_name, preferred_skin_color)
    elif is_npc_body_skin_type(skin_name):
        texture_file_names += list_npc_body_texture_variants(skin_name, preferred_skin_color)
    elif is_unleashed_npc_body_skin_type(skin_name):
        texture_file_names += list_unleashed_npc_body_texture_variants(skin_name, preferred_skin_color)
    elif is_costume_body_skin_type(skin_name):
        texture_file_names += list_costume_body_texture_variants(skin_name, preferred_skin_color)

    add_job_and_npc_textures(texture_file_names, skin_name, preferred_skin_color)

    if fix_textures:
        if skin_name.lower().startswith("xskin-B601MAFit_".lower()):
            find_secondary_textures = False
        if skin_name.lower().startswith("xskin-B620MAFit_".lower()):
            find_secondary_textures = False
        if skin_name.lower().startswith("xskin-B632MAFit_".lower()):
            find_secondary_textures = False
        if skin_name.lower().startswith("xskin-B634FAFit_".lower()):
            find_secondary_textures = False
        if skin_name.lower().startswith("xskin-C620MA_".lower()):
            find_secondary_textures = False

    reduced_texture_file_list = reduce_texture_file_list(
        texture_file_list,
        texture_file_names,
        fix_textures=fix_textures,
    )

    for file_path in reduced_texture_file_list:
        original_file_texture_name = file_path.stem
        file_texture_name = original_file_texture_name
        if fix_textures:
            file_texture_name = fix_texture_file_name(file_texture_name)

        for texture_name in texture_file_names:
            if file_texture_name.lower() == texture_name.lower():
                create_material(obj, original_file_texture_name, file_path)

    if find_secondary_textures:
        for file_path in reduced_texture_file_list:
            original_file_texture_name = file_path.stem
            file_texture_name = original_file_texture_name
            if fix_textures:
                file_texture_name = fix_texture_file_name(file_texture_name)

            for texture_name in texture_file_names:
                if file_texture_name.lower().startswith(texture_name.lower()):
                    create_material(obj, original_file_texture_name, file_path)

    if not obj.data.materials and default_texture != "x":
        if default_texture.lower() in ["white", "grey"]:
            create_material(obj, default_texture, pathlib.Path())
            return

        for file_path in texture_file_list:
            original_file_texture_name = file_path.stem
            file_texture_name = original_file_texture_name
            if fix_textures:
                file_texture_name = fix_texture_file_name(file_texture_name)

            if file_texture_name.lower() == default_texture.lower():
                create_material(obj, original_file_texture_name, file_path)
                return
