import bpy
import os
import re


def is_head_skin_type(skin_name):
    return re.match("^xskin-c\\d{3}(f|m|u)(a|c).*-head-head(|01)$", skin_name.lower())


def is_body_skin_type(skin_name):
    return re.match("^xskin-b\\d{3}(f|m|u)(a|c)(skn|fit|fat|chd).*-body.*", skin_name.lower())


def is_hand_skin_type(skin_name):
    return re.match("^xskin-(h)(u|f|m)(l|r)(c|o|p).*hand-.*", skin_name.lower())


def is_nude_skin_type(skin_name):
    return re.match("^xskin-n(f|m|u)(skn|fit|fat|chd)_01.*-pelvis-.*", skin_name.lower())


def is_npc_head_skin_type(skin_name):
    return re.search("(f|m|u)(a|c)_.*-head-.*", skin_name.lower())


def is_npc_body_skin_type(skin_name):
    return re.search("(f|m|u)(a|c|)(skn|fit|fat|chd)_.*-pelvis-body.*", skin_name.lower())


def is_hot_date_npc_head_skin_type(skin_name):
    return re.match("xskin-c.*(f|m|u)(a|)(skn|fit|fat|)(drk|med|lgt|)_.*-head-.*", skin_name.lower())


def is_unleashed_npc_body_skin_type(skin_name):
    return re.match("xskin-b.*_01-pelvis-body$", skin_name.lower())


def is_costume_skin_type(skin_name):
    return skin_name.lower().startswith("xskin-ct-")


def is_body_texture_type(texture_name):
    return re.match("^b\\d{3}(f|m|u)(a|c)(skn|fit|fat|chd)", texture_name.lower())


def is_npc_body_texture_type(texture_name):
    return re.search("(f|m|u)(a|c|)(drk|med|lgt)_", texture_name.lower())


def create_head_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    body_id = skin_type[1:4]
    sex = skin_type[4]
    age = skin_type[5]

    for skin_color in skin_colors:
        texture_names.append(("c" + body_id + sex + age + skin_color + "_" + name).lower())
        texture_names.append(("c" + body_id + sex + age + skin_color + "_").lower())
        texture_names.append(("c" + body_id + sex + age + "_" + name + skin_color).lower())

    return texture_names


def create_body_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = None if len(split_skin_name) == 1 else split_skin_name[1]

    body_id = skin_type[1:4]
    sex = skin_type[4]
    age = skin_type[5]
    weight = skin_type[6:9]

    for skin_color in skin_colors:
        if name is not None:
            texture_names.append(("b" + body_id + sex + age + weight + skin_color + "_" + name ).lower())

        texture_names.append(("b" + body_id + sex + age + weight + skin_color + "_").lower())
        texture_names.append(("b" + body_id + sex + age + weight + "t" + skin_color + "_").lower()) # b823faskn

    return texture_names


def create_hand_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    split_skin_name = skin_name.split("-")

    sex = split_skin_name[1][1]
    hand = split_skin_name[1][2]
    position = split_skin_name[1][3]

    texture_names = list()

    for sex in ["u", sex.lower()]:
        for side in ["a", "l", "r"]:
            for skin_color in skin_colors:
                texture_names.append(("h" + sex + side + position + skin_color).lower())

            texture_names.append(("h" + sex + side + position).lower())
            texture_names.append(("g" + sex + side + position).lower())
            texture_names.append(("_g" + sex + side + position).lower())

    return texture_names


def create_nude_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    body_id = skin_type[1:4]
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


def create_npc_head_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    xskin_split = skin_name.split("-")
    split_skin_name = xskin_split[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    for skin_color in skin_colors:
        texture_names.append((skin_type + skin_color + "_" + name).lower())

        if len(xskin_split) >= 3:
            texture_names.append((skin_type + skin_color + "_" + name + "-" + xskin_split[2]).lower()) # pa-onset

    return texture_names


def create_npc_body_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    xskin_split = skin_name.split("-")
    split_skin_name = xskin_split[1]
    sex_age_weight_span = re.search("(f|m|u)(a|c|)(skn|fit|fat|chd)_", split_skin_name.lower()).span()
    skin_type = split_skin_name[:sex_age_weight_span[1] - 1]
    name = split_skin_name[sex_age_weight_span[1]:]

    texture_names.append((skin_type + "_" + name).lower())
    texture_names.append(("b" + skin_type + "_" + name).lower())

    for skin_color in skin_colors:
        texture_names.append((skin_type + skin_color + "_" + name).lower())
        texture_names.append((skin_type[:-3] + skin_color + "_" + name).lower())

        if name == "01":
            texture_names.append((skin_type + skin_color + "_").lower())

        if len(xskin_split) >= 3:
            texture_names.append((skin_type + skin_color + "_" + name + "-" + xskin_split[2]).lower()) # pa-onset

    return texture_names


def create_hot_date_npc_head_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt", "gt"] # gt for CCook
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    split_skin_name = skin_name.split("-")[1]
    sex_age_weight_span = re.search("(f|m|u)(a|)(skn|fit|fat|)(drk|med|lgt|)_", split_skin_name.lower()).span()
    skin_type = split_skin_name[:sex_age_weight_span[1] - 1]
    name = split_skin_name[sex_age_weight_span[1]:]

    for skin_color in skin_colors:
        texture_names.append((skin_type + skin_color + "_" + name).lower())
        for weight in ["skn", "fit", "fat"]:
            texture_names.append((skin_type + weight + skin_color + "_" + name).lower())

    return texture_names


def create_unleashed_npc_body_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    texture_names = list()

    split_skin_name = skin_name.split("-")[1].split("_", 1)
    skin_type = split_skin_name[0]
    name = split_skin_name[1]

    for skin_color in skin_colors:
        texture_names.append((skin_type + skin_color + "_" + name).lower())

    return texture_names


def create_costume_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]

    split_skin_name = skin_name.split("-")

    skin_type = split_skin_name[1]
    for element in split_skin_name[2:-3]:
        skin_type += "-" + element

    identifier = split_skin_name[-3]

    texture_names = list()

    for skin_color in skin_colors:
        texture_name = skin_type + skin_color + "-" + identifier
        texture_names.append(texture_name.lower())

    return texture_names


def create_default_texture_file_name_variants(skin_name, preferred_skin_color):
    skin_colors = ["drk", "med", "lgt"]
    skin_colors = [preferred_skin_color] + [x for x in skin_colors if x != preferred_skin_color]


def create_material(obj, texture_name, texture_file_path):
    if texture_name.lower() in ["white", "grey"]:
        texture_name = texture_name.lower()

    material = bpy.data.materials.get(texture_name)
    if material is None:
        if texture_name == "grey":
            material = bpy.data.materials.new(name=texture_name)
            material.use_nodes = True

            principled_BSDF = material.node_tree.nodes.get('Principled BSDF')
            principled_BSDF.inputs[0].default_value = (0.2, 0.2, 0.2, 1.0)
            principled_BSDF.inputs[2].default_value = 1.0
            principled_BSDF.inputs[12].default_value = 0.0

        elif texture_name == "white":
            material = bpy.data.materials.new(name=texture_name)
            material.use_nodes = True

            principled_BSDF = material.node_tree.nodes.get('Principled BSDF')
            principled_BSDF.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
            principled_BSDF.inputs[2].default_value = 1.0
            principled_BSDF.inputs[12].default_value = 0.0

        else:
            material = bpy.data.materials.new(name=texture_name)

            image = bpy.data.images.get(texture_file_path)
            if image is None:
                image = bpy.data.images.load(texture_file_path)
            material.use_nodes = True

            image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            image_node.image = image

            principled_BSDF = material.node_tree.nodes.get('Principled BSDF')
            material.node_tree.links.new(image_node.outputs[0], principled_BSDF.inputs[0])
            principled_BSDF.inputs[2].default_value = 1.0
            principled_BSDF.inputs[12].default_value = 0.0

            if os.path.splitext(texture_file_path)[1] == ".tga":
                material.node_tree.links.new(image_node.outputs[1], principled_BSDF.inputs[4])
                material.blend_method = 'BLEND'

    if material.name not in obj.data.materials:
        obj.data.materials.append(material)


def reduce_texture_file_list(texture_file_list, texture_file_names):
    zipped_texture_file_names = list(zip(texture_file_names, range(len(texture_file_names))))
    reduced_texture_file_list = list()

    for file_path in texture_file_list:
        file_texture_name = os.path.splitext(os.path.basename(file_path))[0]
        for texture_name in zipped_texture_file_names:
            if file_texture_name.lower().startswith(texture_name[0].lower()):
                reduced_texture_file_list.append(tuple((file_path, texture_name[1])))

    if len(reduced_texture_file_list) == 0:
        return list()

    reduced_texture_file_list.sort(key=lambda tup: tup[1])
    return list(zip(*reduced_texture_file_list))[0]


def fixup_skin_name_and_default_texture(texture_file_names, skin_name, default_texture):
    # base game
    if skin_name == "xskin-c_firefighter-HEAD-HEAD":
        default_texture = "C_Firefighter"

    if skin_name == "xskin-c_pizzaguy-HEAD-HEAD":
        default_texture = "pizzaguyface"

    if skin_name == "xskin-c_postal-HEAD-HEAD":
        default_texture = "Postalface"

    if skin_name == "xskin-ffskn_01-PELVIS-BODY":
        default_texture = "ffsknmed_01"

    if skin_name == "xskin-c_skeleton-HEAD-HEAD":
        texture_file_names += ["C_skeleton".lower(), "C_skeleneg".lower()]

    if skin_name == "xskin-skeleton_01-PELVIS-BODY" or skin_name == "xskin-skeletonchd_01-PELVIS-BODY":
        texture_file_names += ["Skeleton_01".lower(), "Skeleneg_01".lower()]

    if default_texture.lower() == "repoizerringb3drt":
        texture_file_names += ["repoizerringA3DRT".lower(), "repoizerringB3DRT".lower(), "repoizerringC3DRT".lower()]

    # deluxe
    if skin_name == "xskin-b011fafit_01-PELVIS-BODY":
        default_texture = "b011fafitmed_redshirtshortsta"

    if skin_name == "xskin-B103Maskn_longarms-PELVIS-BODY":
        default_texture = "b103masknmed_dkbluejacket"

    if skin_name == "xskin-b325fafit_01-PELVIS-BODY":
        default_texture = "B325FaFitmed_bluefractals"

    if skin_name == "xskin-B335Mafit_WDSCoat-01-PELVIS-BODY":
        default_texture = "b335mafitmed_manblsar"

    if skin_name == "xskin-B345MAFit_WDSRetro-PELVIS-BODY":
        default_texture = "b345mafitmed_flowersar"

    # house party
    if skin_name == "xskin-cpcrasherma_01-HEAD-HEAD":
        texture_file_names.append("cPCrasherMA-01".lower())

    if skin_name == "xskin-pcrasherma_01-PELVIS-BODY":
        texture_file_names.append("PCrasher-MA-01".lower())

    if skin_name == "xskin-c030fa_eurotrsh-HEAD-HEAD":
        texture_file_names.append(default_texture.lower())

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

    if skin_name == "xskin-B700MAFit_ct-PELVIS-BODY":
        default_texture = "B700MAFit_ct"
    if skin_name == "xskin-B701MAFit_ct-PELVIS-BODY":
        default_texture = "B701MAFit_ct"
    if skin_name == "xskin-B702MAFit_ct-PELVIS-BODY":
        default_texture = "B702MAFit_ct"
    if skin_name == "xskin-B703MAFit_ct-PELVIS-BODY":
        default_texture = "B703MAFit_ct"
    if skin_name == "xskin-B709MAFit_ct-PELVIS-BODY":
        default_texture = "B709MAFit_ct"
    if skin_name == "xskin-B710MAFit_ct-PELVIS-BODY":
        default_texture = "B710MAFit_ct"
    if skin_name == "xskin-B712MAFit_ct-PELVIS-BODY":
        default_texture = "B712MAFit_ct"
    if skin_name == "xskin-B716MAFit_ct-PELVIS-BODY":
        default_texture = "B716MAFit_ct"
    if skin_name == "xskin-B719MAFit_ct-PELVIS-BODY":
        default_texture = "B719MAFit_ct"
    if skin_name == "xskin-B710FAFit_ct-PELVIS-BODY":
        default_texture = "B710FAFit_ct"
    if skin_name == "xskin-B712FAFit_ct-PELVIS-BODY":
        default_texture = "B712FAFit_ct"
    if skin_name == "xskin-B716FAFit_ct-PELVIS-BODY":
        default_texture = "B716FAFit_ct"
    if skin_name == "xskin-B717FAFit_ct-PELVIS-BODY":
        default_texture = "B717FAFit_ct"
    if skin_name == "xskin-B719FAFit_ct-PELVIS-BODY":
        default_texture = "B719FAFit_ct"

    # hot date
    if skin_name == "xskin-B415MAfit_rockabilly-PELVIS-BODY":
        texture_file_names.append("B415MAfit_rockabilly".lower())

    if skin_name == "xskin-C405FAlgt_janitor-HEAD-HEAD":
        texture_file_names.append("C_lgt_janitor".lower())

    if skin_name == "xskin-b046fafit_cowg-PELVIS-MBODY5":
        skin_name = "xskin-b046fafit_cowg-PELVIS-BODY"

    # unleashed:
    if skin_name == "xskin-B008dog_greyhound-PELVIS-DOGBODY" or skin_name == "xskin-B008dog_greyhound-HEAD-DOGBODY-HEAD":
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

    # makin magic
    if skin_name == "xskin-b823faskn_01-PELVIS-BODY":
        default_texture = "b823fasknmed"

    if skin_name == "xskin-B825MaFit_gs1sar-PELVIS-BODY":
        default_texture = "b825mafitmed_gs1sar"

    if skin_name == "xskin-C203FC_CreepyBen-HEAD-HEAD":
        skin_name = "xskin-C203MC_CreepyBen-HEAD-HEAD"

    if skin_name == "xskin-CMagicFAFit_BlueGenie-HEAD-HEAD":
        default_texture = "CMagicFA_BlueGenie"

    return skin_name, default_texture


def add_job_and_npc_textures(texture_file_names, skin_name, preferred_skin_color):
    # base game
    if skin_name.startswith("xskin-b003fa"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-CatsuitFfit_", preferred_skin_color)

    if skin_name.startswith("xskin-b008fa"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-MayorFfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-PoliticsFfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-TopCopFfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-TopDocFfit_", preferred_skin_color)

    if skin_name.startswith("xskin-b012fa"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-ScrubsFfit_", preferred_skin_color)

    if skin_name == "xskin-b002mafit_01-PELVIS-BODY":
        texture_file_names.append("pizzaguysuit".lower())

    if skin_name == "xskin-b003mafit_01-PELVIS-BODY":
        texture_file_names.append("Postalsuit".lower())

    if skin_name.startswith("xskin-b002ma"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-ScrubsMfit_", preferred_skin_color)

    if skin_name.startswith("xskin-b003ma"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-EMTMfit_", preferred_skin_color)

    if skin_name.startswith("xskin-b004ma"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-MayorMfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-PoliticsMfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-TopCopMfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-TopDocMfit_", preferred_skin_color)

    if skin_name == "xskin-c004fa_gma1-HEAD-HEAD":
        texture_file_names.append("C_socwkr".lower())

    if skin_name == "xskin-c003ma_romancrew-HEAD-HEAD":
        texture_file_names.append("C_Handy".lower())
        texture_file_names.append("C_Repo".lower())

    # livin large
    if skin_name.startswith("xskin-b008fa"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-infoverlordFfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-UFOinvestFfit_", preferred_skin_color)
    if skin_name.startswith("xskin-b004ma"):
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-HypnotistMfit_", preferred_skin_color)
        texture_file_names += create_npc_body_texture_file_name_variants("xskin-UFOinvestMfit_", preferred_skin_color)

    # house party
    if skin_name == "xskin-nffit_01-PELVIS-MBODY":
        texture_file_names += ["b_fa_eurotrash_swim", "b_fa_eurotrash_nekkid"]

    # unleashed
    if skin_name == "xskin-Petjudge_Mafit_01-PELVIS-BODY":
        texture_file_names += create_npc_body_texture_file_name_variants(
            "xskin-Petjudge_Mafit_02-PELVIS-BODY",
            preferred_skin_color
        )


def load_textures_internal(obj, texture_file_list, skin_name, default_texture, preferred_skin_color):
    texture_file_names = list()
    find_secondary_textures = False

    skin_name, default_texture = fixup_skin_name_and_default_texture(
        texture_file_names,
        skin_name,
        default_texture
    )

    if default_texture.lower() in ["white", "grey"]:
        create_material(obj, default_texture, "")
        return

    if is_head_skin_type(skin_name):
        texture_file_names += create_head_texture_file_name_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif is_body_skin_type(skin_name):
        texture_file_names += create_body_texture_file_name_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif is_hand_skin_type(skin_name):
        texture_file_names += create_hand_texture_file_name_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True
    elif is_nude_skin_type(skin_name):
        texture_file_names += create_nude_texture_file_name_variants(skin_name, preferred_skin_color)
        find_secondary_textures = True

    elif is_npc_head_skin_type(skin_name):
        texture_file_names += create_npc_head_texture_file_name_variants(skin_name, preferred_skin_color)
    elif is_npc_body_skin_type(skin_name):
        texture_file_names += create_npc_body_texture_file_name_variants(skin_name, preferred_skin_color)
    elif is_hot_date_npc_head_skin_type(skin_name):
        texture_file_names += create_hot_date_npc_head_texture_file_name_variants(skin_name, preferred_skin_color)
    elif is_unleashed_npc_body_skin_type(skin_name):
        texture_file_names += create_unleashed_npc_body_texture_file_name_variants(skin_name, preferred_skin_color)

    elif is_costume_skin_type(skin_name):
        texture_file_names += create_costume_texture_file_name_variants(skin_name, preferred_skin_color)
        for texture_name in texture_file_names:
            for file_path in texture_file_list:
                file_texture_name = os.path.splitext(os.path.basename(file_path))[0]
                if file_texture_name.lower() == texture_name.lower():
                    create_material(obj, file_texture_name, file_path)
        return

    if is_body_skin_type(skin_name) and is_npc_body_texture_type(default_texture):
        skin_color_span = is_npc_body_texture_type(default_texture).span()
        skin_type = default_texture[:skin_color_span[0] + 1]
        bone_model = default_texture[skin_color_span[1] - 1:]
        npc_body_skin_name = "xskin-" + skin_type + "fit" + bone_model
        texture_file_names += create_npc_body_texture_file_name_variants(npc_body_skin_name, preferred_skin_color)

    if default_texture != "x" and default_texture.lower() not in texture_file_names:
        if not is_head_skin_type(skin_name) and not is_body_skin_type(skin_name):
            for file_path in texture_file_list:
                file_texture_name = os.path.splitext(os.path.basename(file_path))[0]
                if file_texture_name.lower() == default_texture.lower():
                    create_material(obj, file_texture_name, file_path)
                    return
        elif is_body_skin_type(skin_name) and not is_body_texture_type(default_texture):
            texture_file_names.append(default_texture)

    add_job_and_npc_textures(texture_file_names, skin_name, preferred_skin_color)

    if skin_name.startswith("xskin-B601MAFit_"):
        find_secondary_textures = False

    texture_file_list = reduce_texture_file_list(texture_file_list, texture_file_names)

    for file_path in texture_file_list:
        file_texture_name = os.path.splitext(os.path.basename(file_path))[0]
        for texture_name in texture_file_names:
            if file_texture_name.lower() == texture_name.lower():
                create_material(obj, file_texture_name, file_path)

    if find_secondary_textures:
        for file_path in texture_file_list:
            file_texture_name = os.path.splitext(os.path.basename(file_path))[0]
            for texture_name in texture_file_names:
                if file_texture_name.lower().startswith(texture_name.lower()):
                    create_material(obj, file_texture_name, file_path)


def load_textures(obj, texture_file_list, skin_name, default_texture, preferred_skin_color):
    load_textures_internal(
        obj,
        texture_file_list,
        skin_name,
        default_texture,
        preferred_skin_color,
    )

    if not obj.data.materials and is_body_skin_type(skin_name):
        weights = ["skn", "fit", "fat"]
        current_weight = skin_name[12:15]
        for weight in filter(lambda x: x != current_weight, weights):
            skin_name = skin_name[:12] + weight + skin_name[15:]
            load_textures_internal(
                obj,
                texture_file_list,
                skin_name,
                default_texture,
                preferred_skin_color,
            )
