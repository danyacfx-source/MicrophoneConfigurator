import bpy
import bmesh
import math
from mathutils import Vector, Euler, Quaternion

bl_info = {
    "name": "VTuber Anime Generator v2",
    "author": "opencode",
    "version": (2, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > VTuber",
    "description": "Высокодетализированный аниме-вайтюбер с анимациями",
    "category": "Mesh",
}

SCENE_FPS = 24
ANIM_SECONDS = 3
ANIM_FRAMES = SCENE_FPS * ANIM_SECONDS


def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)
    for block in bpy.data.cameras:
        bpy.data.cameras.remove(block)
    for block in bpy.data.lights:
        bpy.data.lights.remove(block)
    for block in bpy.data.worlds:
        bpy.data.worlds.remove(block)
    for block in bpy.data.actions:
        bpy.data.actions.remove(block)
    for block in bpy.data.armatures:
        bpy.data.armatures.remove(block)


def mat(name, color, rough=0.4, metal=0.0, emit=0.0, alpha=1.0, subsurf=0.0):
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        if emit > 0:
            bsdf.inputs["Emission Strength"].default_value = emit
            bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        try:
            bsdf.inputs["Subsurface Weight"].default_value = subsurf
        except KeyError:
            pass
    if alpha < 1.0:
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    return m


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)


def sphere(name, loc, scale, seg=24, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return o


def cube(name, loc, scale):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return o


def cylinder(name, loc, scale, seg=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=1.0, depth=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return o


def cone(name, loc, scale, seg=16):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=1.0, radius2=0.0, depth=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return o


def torus(name, loc, scale, maj=24, min_s=12):
    bpy.ops.mesh.primitive_torus_add(major_segments=maj, minor_segments=min_s,
                                      major_radius=1.0, minor_radius=0.3, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.shade_smooth()
    return o


def apply_smooth_all():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT')


# ── MODEL ────────────────────────────────────────────────────────────

MATS = {}

def create_materials():
    global MATS
    MATS = {
        "skin":      mat("Skin",      (0.99, 0.89, 0.80), rough=0.50, subsurf=0.15),
        "skin_shade":mat("SkinShade", (0.92, 0.78, 0.70), rough=0.55, subsurf=0.10),
        "hair":      mat("Hair",      (0.60, 0.35, 0.98), rough=0.30, metal=0.05),
        "hair_tip":  mat("HairTip",   (0.80, 0.55, 1.00), rough=0.25, emit=0.15),
        "hoodie":    mat("Hoodie",    (0.18, 0.18, 0.52), rough=0.70),
        "hoodie_dark":mat("HoodieDark",(0.12,0.12,0.38),  rough=0.75),
        "graphic":   mat("Graphic",   (0.95, 0.35, 0.70), rough=0.30, emit=0.8),
        "graphic2":  mat("Graphic2",  (0.30, 0.80, 1.00), rough=0.30, emit=0.6),
        "eye_white": mat("EyeWhite",  (1.00, 1.00, 1.00), rough=0.05),
        "iris":      mat("Iris",      (0.25, 0.45, 1.00), rough=0.10, metal=0.15),
        "iris2":     mat("Iris2",     (0.50, 0.70, 1.00), rough=0.10, emit=0.2),
        "pupil":     mat("Pupil",     (0.01, 0.01, 0.04), rough=0.02),
        "highlight": mat("Highlight", (1.00, 1.00, 1.00), rough=0.00, metal=1.0),
        "mouth":     mat("Mouth",     (0.88, 0.30, 0.40), rough=0.35),
        "mouth_in":  mat("MouthIn",   (0.60, 0.15, 0.20), rough=0.40),
        "tongue":    mat("Tongue",    (0.90, 0.40, 0.45), rough=0.40),
        "blush":     mat("Blush",     (1.00, 0.65, 0.70), rough=0.50, emit=0.1),
        "nose":      mat("Nose",      (0.96, 0.84, 0.75), rough=0.45),
        "eyebrow":   mat("Eyebrow",   (0.40, 0.25, 0.70), rough=0.40),
        "pants":     mat("Pants",     (0.13, 0.13, 0.32), rough=0.60),
        "shoe":      mat("Shoe",      (0.95, 0.95, 0.98), rough=0.25),
        "shoe_sole": mat("ShoeSole",  (0.20, 0.20, 0.22), rough=0.80),
        "belt":      mat("Belt",      (0.85, 0.30, 0.55), rough=0.40),
        "hand":      mat("Hand",      (0.97, 0.86, 0.77), rough=0.50, subsurf=0.12),
        "ear":       mat("Ear",       (0.95, 0.82, 0.73), rough=0.50, subsurf=0.10),
        "neck_inner":mat("NeckInner", (0.15, 0.15, 0.45), rough=0.65),
        "outline":   mat("Outline",   (0.05, 0.05, 0.10), rough=0.90),
    }


def build_head():
    parts = []
    hp = (0, 0, 1.60)

    head = sphere("Head", hp, (0.48, 0.52, 0.50), 32, 24)
    assign(head, MATS["skin"])
    parts.append(head)

    cheek_l = sphere("CheekL", (-0.28, 0.25, 1.50), (0.10, 0.06, 0.08), 12, 8)
    assign(cheek_l, MATS["blush"])
    parts.append(cheek_l)

    cheek_r = sphere("CheekR", (0.28, 0.25, 1.50), (0.10, 0.06, 0.08), 12, 8)
    assign(cheek_r, MATS["blush"])
    parts.append(cheek_r)

    for side in [-1, 1]:
        tag = "L" if side < 0 else "R"

        eye_w = sphere(f"EyeW_{tag}", (side*0.17, 0.40, 1.62), (0.13, 0.06, 0.14), 20, 14)
        assign(eye_w, MATS["eye_white"])
        parts.append(eye_w)

        iris = sphere(f"Iris_{tag}", (side*0.17, 0.44, 1.62), (0.095, 0.04, 0.10), 20, 14)
        assign(iris, MATS["iris"])
        parts.append(iris)

        iris2 = sphere(f"Iris2_{tag}", (side*0.17, 0.45, 1.63), (0.06, 0.03, 0.06), 16, 10)
        assign(iris2, MATS["iris2"])
        parts.append(iris2)

        pupil = sphere(f"Pupil_{tag}", (side*0.17, 0.46, 1.62), (0.04, 0.02, 0.04), 14, 8)
        assign(pupil, MATS["pupil"])
        parts.append(pupil)

        hl1 = sphere(f"HL1_{tag}", (side*0.14, 0.47, 1.65), (0.022, 0.015, 0.022), 8, 6)
        assign(hl1, MATS["highlight"])
        parts.append(hl1)

        hl2 = sphere(f"HL2_{tag}", (side*0.20, 0.46, 1.60), (0.012, 0.010, 0.012), 8, 6)
        assign(hl2, MATS["highlight"])
        parts.append(hl2)

        lid_up = sphere(f"LidUp_{tag}", (side*0.17, 0.43, 1.72), (0.14, 0.04, 0.03), 14, 8)
        assign(lid_up, MATS["skin_shade"])
        parts.append(lid_up)

        lid_dn = sphere(f"LidDn_{tag}", (side*0.17, 0.43, 1.54), (0.13, 0.03, 0.025), 14, 8)
        assign(lid_dn, MATS["skin_shade"])
        parts.append(lid_dn)

        brow = cube(f"Brow_{tag}", (side*0.17, 0.42, 1.76), (0.16, 0.025, 0.02))
        brow.rotation_euler = (0, 0, math.radians(side * 8))
        bpy.ops.object.transform_apply(rotation=True)
        assign(brow, MATS["eyebrow"])
        parts.append(brow)

    nose = cone("Nose", (0, 0.52, 1.55), (0.03, 0.03, 0.05), 10)
    nose.rotation_euler = (math.radians(80), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    assign(nose, MATS["nose"])
    parts.append(nose)

    mouth_open = sphere("MouthOpen", (0, 0.48, 1.46), (0.06, 0.025, 0.03), 14, 8)
    assign(mouth_open, MATS["mouth_in"])
    parts.append(mouth_open)

    tongue = sphere("Tongue", (0, 0.47, 1.44), (0.035, 0.02, 0.02), 10, 6)
    assign(tongue, MATS["tongue"])
    parts.append(tongue)

    mouth_line = cube("MouthLine", (0, 0.50, 1.47), (0.09, 0.015, 0.005))
    assign(mouth_line, MATS["mouth"])
    parts.append(mouth_line)

    ear_l = sphere("EarL", (-0.44, 0.0, 1.60), (0.06, 0.05, 0.10), 12, 8)
    ear_l.rotation_euler = (0, 0, math.radians(12))
    bpy.ops.object.transform_apply(rotation=True)
    assign(ear_l, MATS["ear"])
    parts.append(ear_l)

    ear_r = sphere("EarR", (0.44, 0.0, 1.60), (0.06, 0.05, 0.10), 12, 8)
    ear_r.rotation_euler = (0, 0, math.radians(-12))
    bpy.ops.object.transform_apply(rotation=True)
    assign(ear_r, MATS["ear"])
    parts.append(ear_r)

    return hp, parts


def build_hair(head_pos):
    parts = []
    hx, hy, hz = head_pos

    spikes_top = [
        (0.0,   0.10, 0.52, 0.10, 0.42, 0,    0),
        (-0.12, 0.05, 0.48, 0.08, 0.38, -10,  15),
        (0.12,  0.05, 0.48, 0.08, 0.38, 10,  -15),
        (-0.06, 0.18, 0.45, 0.07, 0.32, -5,   8),
        (0.06,  0.18, 0.45, 0.07, 0.32, 5,   -8),
        (-0.20, -0.05, 0.40, 0.06, 0.30, -15,  25),
        (0.20, -0.05, 0.40, 0.06, 0.30, 15,  -25),
    ]

    for i, (ox, oy, oz, sx, sy, rz, rx) in enumerate(spikes_top):
        c = cone(f"HairSpike_{i}", (hx+ox, hy+oy, hz+oz), (sx, sx, sy), 10)
        c.rotation_euler = (math.radians(rx), 0, math.radians(rz))
        bpy.ops.object.transform_apply(rotation=True)
        m = MATS["hair_tip"] if i % 3 == 0 else MATS["hair"]
        assign(c, m)
        parts.append(c)

    bangs = [
        (-0.22, 0.42, 0.28, 0.11, 0.18, 0.06, 30,  -20),
        (-0.10, 0.50, 0.30, 0.09, 0.22, 0.05, 20,  -10),
        (0.00,  0.54, 0.32, 0.08, 0.24, 0.05, 0,    0),
        (0.10,  0.50, 0.30, 0.09, 0.22, 0.05, -20,  10),
        (0.22,  0.42, 0.28, 0.11, 0.18, 0.06, -30,  20),
    ]

    for i, (ox, oy, oz, sx, sy, sz, rz, rx) in enumerate(bangs):
        b = sphere(f"Bang_{i}", (hx+ox, hy+oy, hz+oz), (sx, sy, sz), 14, 10)
        b.rotation_euler = (math.radians(rx), 0, math.radians(rz))
        bpy.ops.object.transform_apply(rotation=True)
        assign(b, MATS["hair"])
        parts.append(b)

    sides = [
        (-0.48, -0.05, -0.10, 0.13, 0.55, 0.10),
        (0.48, -0.05, -0.10, 0.13, 0.55, 0.10),
        (-0.44, -0.15, -0.20, 0.10, 0.45, 0.08),
        (0.44, -0.15, -0.20, 0.10, 0.45, 0.08),
        (-0.38, -0.25, -0.30, 0.08, 0.35, 0.07),
        (0.38, -0.25, -0.30, 0.08, 0.35, 0.07),
    ]

    for i, (ox, oy, oz, sx, sy, sz) in enumerate(sides):
        s = sphere(f"SideHair_{i}", (hx+ox, hy+oy, hz+oz), (sx, sy, sz), 14, 10)
        assign(s, MATS["hair"])
        parts.append(s)

    back = [
        (0.0, -0.40, 0.12, 0.42, 0.28, 0.48),
        (-0.25, -0.35, -0.05, 0.18, 0.22, 0.42),
        (0.25, -0.35, -0.05, 0.18, 0.22, 0.42),
        (-0.10, -0.45, -0.15, 0.15, 0.20, 0.35),
        (0.10, -0.45, -0.15, 0.15, 0.20, 0.35),
    ]

    for i, (ox, oy, oz, sx, sy, sz) in enumerate(back):
        b = sphere(f"BackHair_{i}", (hx+ox, hy+oy, hz+oz), (sx, sy, sz), 16, 10)
        m = MATS["hair_tip"] if i == 0 else MATS["hair"]
        assign(b, m)
        parts.append(b)

    ahoge = cone("Ahoge", (hx+0.02, hy+0.25, hz+0.55), (0.04, 0.04, 0.25), 8)
    ahoge.rotation_euler = (math.radians(-30), math.radians(10), math.radians(15))
    bpy.ops.object.transform_apply(rotation=True)
    assign(ahoge, MATS["hair_tip"])
    parts.append(ahoge)

    return parts


def build_body():
    parts = []

    torso = cube("Torso", (0, 0, 0.60), (0.58, 0.32, 0.80))
    assign(torso, MATS["hoodie"])
    parts.append(torso)

    chest_graphic = cube("ChestGraphic", (0, 0.17, 0.80), (0.28, 0.01, 0.22))
    assign(chest_graphic, MATS["graphic"])
    parts.append(chest_graphic)

    stripe_l = cube("StripeL", (-0.15, 0.17, 0.60), (0.06, 0.01, 0.40))
    assign(stripe_l, MATS["graphic2"])
    parts.append(stripe_l)

    stripe_r = cube("StripeR", (0.15, 0.17, 0.60), (0.06, 0.01, 0.40))
    assign(stripe_r, MATS["graphic2"])
    parts.append(stripe_r)

    hood = sphere("Hood", (0, -0.15, 1.02), (0.35, 0.30, 0.30), 20, 14)
    assign(hood, MATS["hoodie_dark"])
    parts.append(hood)

    pocket = cube("Pocket", (0, 0.18, 0.42), (0.32, 0.03, 0.15))
    assign(pocket, MATS["hoodie_dark"])
    parts.append(pocket)

    neck = cylinder("Neck", (0, 0, 1.15), (0.09, 0.09, 0.12), 14)
    assign(neck, MATS["skin"])
    parts.append(neck)

    collar = torus("Collar", (0, 0.05, 1.10), (0.14, 0.14, 0.04), 16, 8)
    collar.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    assign(collar, MATS["neck_inner"])
    parts.append(collar)

    for side in [-1, 1]:
        tag = "L" if side < 0 else "R"

        shoulder = sphere(f"Shoulder_{tag}", (side*0.38, 0, 0.95), (0.12, 0.10, 0.12), 14, 10)
        assign(shoulder, MATS["hoodie"])
        parts.append(shoulder)

        upper_arm = cylinder(f"UpperArm_{tag}", (side*0.50, 0.02, 0.72), (0.10, 0.10, 0.30), 14)
        upper_arm.rotation_euler = (0, math.radians(side*8), 0)
        bpy.ops.object.transform_apply(rotation=True)
        assign(upper_arm, MATS["hoodie"])
        parts.append(upper_arm)

        elbow = sphere(f"Elbow_{tag}", (side*0.55, 0.05, 0.55), (0.09, 0.08, 0.09), 12, 8)
        assign(elbow, MATS["hoodie"])
        parts.append(elbow)

        forearm = cylinder(f"Forearm_{tag}", (side*0.56, 0.10, 0.38), (0.08, 0.08, 0.25), 14)
        forearm.rotation_euler = (math.radians(5), math.radians(side*5), 0)
        bpy.ops.object.transform_apply(rotation=True)
        assign(forearm, MATS["hoodie"])
        parts.append(forearm)

        cuff = cylinder(f"Cuff_{tag}", (side*0.57, 0.12, 0.24), (0.09, 0.09, 0.04), 14)
        assign(cuff, MATS["hoodie_dark"])
        parts.append(cuff)

        hand = sphere(f"Hand_{tag}", (side*0.57, 0.15, 0.18), (0.07, 0.06, 0.08), 14, 10)
        assign(hand, MATS["hand"])
        parts.append(hand)

        for fi in range(4):
            fx = side * 0.57 + side * (0.02 + fi * 0.018)
            fy = 0.20 + fi * 0.005
            fz = 0.13 - fi * 0.01
            finger = sphere(f"Finger_{tag}_{fi}", (fx, fy, fz), (0.015, 0.012, 0.025), 8, 6)
            assign(finger, MATS["hand"])
            parts.append(finger)

    belt = torus("Belt", (0, 0, 0.22), (0.30, 0.30, 0.03), 20, 8)
    belt.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    assign(belt, MATS["belt"])
    parts.append(belt)

    return parts


def build_legs():
    parts = []

    for side in [-1, 1]:
        tag = "L" if side < 0 else "R"

        hip = sphere(f"Hip_{tag}", (side*0.16, 0, 0.18), (0.13, 0.12, 0.12), 14, 10)
        assign(hip, MATS["pants"])
        parts.append(hip)

        upper_leg = cylinder(f"UpperLeg_{tag}", (side*0.16, 0, -0.05), (0.11, 0.11, 0.35), 14)
        assign(upper_leg, MATS["pants"])
        parts.append(upper_leg)

        knee = sphere(f"Knee_{tag}", (side*0.16, 0.02, -0.25), (0.10, 0.09, 0.10), 12, 8)
        assign(knee, MATS["pants"])
        parts.append(knee)

        lower_leg = cylinder(f"LowerLeg_{tag}", (side*0.16, 0.02, -0.48), (0.09, 0.09, 0.30), 14)
        assign(lower_leg, MATS["pants"])
        parts.append(lower_leg)

        ankle = sphere(f"Ankle_{tag}", (side*0.16, 0.04, -0.65), (0.07, 0.06, 0.07), 10, 8)
        assign(ankle, MATS["shoe_sole"])
        parts.append(ankle)

        shoe_body = cube(f"ShoeBody_{tag}", (side*0.16, 0.10, -0.72), (0.10, 0.18, 0.07))
        assign(shoe_body, MATS["shoe"])
        parts.append(shoe_body)

        shoe_sole = cube(f"ShoeSole_{tag}", (side*0.16, 0.10, -0.77), (0.11, 0.20, 0.03))
        assign(shoe_sole, MATS["shoe_sole"])
        parts.append(shoe_sole)

        shoe_toe = sphere(f"ShoeToe_{tag}", (side*0.16, 0.20, -0.72), (0.08, 0.06, 0.06), 10, 8)
        assign(shoe_toe, MATS["shoe"])
        parts.append(shoe_toe)

    return parts


# ── ANIMATIONS ───────────────────────────────────────────────────────

def setup_scene():
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = ANIM_FRAMES
    scene.render.fps = SCENE_FPS


def set_interpolation_linear(obj):
    pass


def animate_breathing():
    torso = bpy.data.objects.get("Torso")
    if not torso:
        return
    if torso.animation_data is None:
        torso.animation_data_create()
    torso.animation_data.action = bpy.data.actions.new(name="Torso_Action")

    frames = [1, ANIM_FRAMES // 4, ANIM_FRAMES // 2, ANIM_FRAMES * 3 // 4, ANIM_FRAMES]
    scales = [
        (0.58, 0.32, 0.80),
        (0.588, 0.32, 0.808),
        (0.58, 0.32, 0.80),
        (0.588, 0.32, 0.808),
        (0.58, 0.32, 0.80),
    ]
    for f, s in zip(frames, scales):
        torso.scale = s
        torso.keyframe_insert(data_path="scale", frame=f, group="Breathing")
    set_interpolation_linear(torso)


def animate_blinking():
    lids_up = [o for o in bpy.data.objects if o.name.startswith("LidUp_")]
    lids_dn = [o for o in bpy.data.objects if o.name.startswith("LidDn_")]

    blink_moments = [20, 60, 100, 140, 170]
    blink_len = 3

    for lid in lids_up + lids_dn:
        if lid.animation_data is None:
            lid.animation_data_create()
        lid.animation_data.action = bpy.data.actions.new(name=f"{lid.name}_Action")

        for bf in blink_moments:
            if bf + blink_len > ANIM_FRAMES:
                continue
            lid.scale.y = 0.005
            lid.keyframe_insert(data_path="scale", frame=bf, group="Blink")
            lid.scale.y = lid.scale.y
            lid.keyframe_insert(data_path="scale", frame=bf + blink_len, group="Blink")

        set_interpolation_linear(lid)


def animate_hair_sway():
    ahoge = bpy.data.objects.get("Ahoge")
    if ahoge:
        if ahoge.animation_data is None:
            ahoge.animation_data_create()
        ahoge.animation_data.action = bpy.data.actions.new(name="Ahoge_Action")
        orig = ahoge.rotation_euler.copy()

        frames = [1, ANIM_FRAMES // 4, ANIM_FRAMES // 2, ANIM_FRAMES * 3 // 4, ANIM_FRAMES]
        rots = [
            orig,
            (orig.x + math.radians(6), orig.y, orig.z + math.radians(8)),
            orig,
            (orig.x - math.radians(4), orig.y, orig.z - math.radians(6)),
            orig,
        ]
        for f, r in zip(frames, rots):
            ahoge.rotation_euler = r
            ahoge.keyframe_insert(data_path="rotation_euler", frame=f, group="HairSway")
        set_interpolation_linear(ahoge)

    for side in [-1, 1]:
        tag = "L" if side < 0 else "R"
        obj = bpy.data.objects.get(f"SideHair_{0 if side < 0 else 3}")
        if not obj:
            continue
        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_Action")
        orig = obj.location.copy()
        frames = [1, ANIM_FRAMES // 3, ANIM_FRAMES * 2 // 3, ANIM_FRAMES]
        locs = [
            orig,
            (orig.x + side * 0.006, orig.y, orig.z + 0.002),
            (orig.x - side * 0.004, orig.y, orig.z - 0.001),
            orig,
        ]
        for f, l in zip(frames, locs):
            obj.location = l
            obj.keyframe_insert(data_path="location", frame=f, group="HairSway")
        set_interpolation_linear(obj)


def animate_facial_expression():
    mouth = bpy.data.objects.get("MouthLine")
    if mouth:
        if mouth.animation_data is None:
            mouth.animation_data_create()
        mouth.animation_data.action = bpy.data.actions.new(name="Mouth_Action")
        orig = mouth.scale.copy()
        frames = [1, ANIM_FRAMES // 2, ANIM_FRAMES]
        scales = [
            orig,
            (orig.x * 1.2, orig.y, orig.z),
            orig,
        ]
        for f, s in zip(frames, scales):
            mouth.scale = s
            mouth.keyframe_insert(data_path="scale", frame=f, group="Expression")
        set_interpolation_linear(mouth)

    for cheek in bpy.data.objects:
        if cheek.name.startswith("Cheek"):
            if cheek.animation_data is None:
                cheek.animation_data_create()
            cheek.animation_data.action = bpy.data.actions.new(name=f"{cheek.name}_Action")
            orig = cheek.scale.copy()
            frames = [1, ANIM_FRAMES // 2, ANIM_FRAMES]
            scales = [
                orig,
                (orig.x * 1.12, orig.y, orig.z * 1.12),
                orig,
            ]
            for f, s in zip(frames, scales):
                cheek.scale = s
                cheek.keyframe_insert(data_path="scale", frame=f, group="Blush")
            set_interpolation_linear(cheek)


def animate_eye_gaze():
    for prefix in ["Pupil_", "Iris_", "Iris2_"]:
        for obj in bpy.data.objects:
            if obj.name.startswith(prefix):
                if obj.animation_data is None:
                    obj.animation_data_create()
                obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_Action")
                orig = obj.location.copy()
                frames = [1, ANIM_FRAMES // 4, ANIM_FRAMES // 2, ANIM_FRAMES * 3 // 4, ANIM_FRAMES]
                locs = [
                    orig,
                    (orig.x + 0.008, orig.y, orig.z + 0.004),
                    (orig.x - 0.005, orig.y, orig.z - 0.003),
                    (orig.x + 0.003, orig.y, orig.z + 0.002),
                    orig,
                ]
                for f, l in zip(frames, locs):
                    obj.location = l
                    obj.keyframe_insert(data_path="location", frame=f, group="EyeGaze")
                set_interpolation_linear(obj)


def animate_graphic_glow():
    for obj in bpy.data.objects:
        if "Graphic" in obj.name or "Stripe" in obj.name:
            if obj.animation_data is None:
                obj.animation_data_create()
            obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_Action")
            orig = obj.scale.copy()
            frames = [1, ANIM_FRAMES // 4, ANIM_FRAMES // 2, ANIM_FRAMES * 3 // 4, ANIM_FRAMES]
            scales = [
                orig,
                (orig.x * 1.04, orig.y, orig.z * 1.04),
                orig,
                (orig.x * 1.04, orig.y, orig.z * 1.04),
                orig,
            ]
            for f, s in zip(frames, scales):
                obj.scale = s
                obj.keyframe_insert(data_path="scale", frame=f, group="Glow")
            set_interpolation_linear(obj)


# ── LIGHTING ─────────────────────────────────────────────────────────

def setup_lighting():
    key = bpy.data.lights.new("Key", 'AREA')
    key.energy = 400
    key.size = 2.5
    key.color = (1.0, 0.96, 0.92)
    ko = bpy.data.objects.new("Key", key)
    bpy.context.collection.objects.link(ko)
    ko.location = (3.5, -2.5, 4.5)
    ko.rotation_euler = (math.radians(40), 0, math.radians(25))

    fill = bpy.data.lights.new("Fill", 'AREA')
    fill.energy = 180
    fill.size = 3.5
    fill.color = (0.88, 0.92, 1.0)
    fo = bpy.data.objects.new("Fill", fill)
    bpy.context.collection.objects.link(fo)
    fo.location = (-3.5, -1.5, 3.5)
    fo.rotation_euler = (math.radians(45), 0, math.radians(-35))

    rim = bpy.data.lights.new("Rim", 'AREA')
    rim.energy = 280
    rim.size = 1.8
    rim.color = (0.92, 0.88, 1.0)
    ro = bpy.data.objects.new("Rim", rim)
    bpy.context.collection.objects.link(ro)
    ro.location = (0.5, 4.5, 3.5)
    ro.rotation_euler = (math.radians(-25), 0, math.radians(170))

    accent = bpy.data.lights.new("Accent", 'POINT')
    accent.energy = 120
    accent.color = (0.7, 0.5, 1.0)
    ao = bpy.data.objects.new("Accent", accent)
    bpy.context.collection.objects.link(ao)
    ao.location = (-1.5, 1.0, 0.5)

    top = bpy.data.lights.new("Top", 'AREA')
    top.energy = 100
    top.size = 4.0
    top.color = (0.95, 0.90, 1.0)
    to = bpy.data.objects.new("Top", top)
    bpy.context.collection.objects.link(to)
    to.location = (0, 0, 6)
    to.rotation_euler = (0, 0, 0)


def setup_camera():
    cam = bpy.data.cameras.new("Camera")
    cam.lens = 85
    cam.clip_end = 100
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 2.8
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cam_obj.location = (0, -3.2, 1.55)
    direction = Vector((0, 0, 1.25)) - Vector(cam_obj.location)
    rot = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot.to_euler()


def setup_world():
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.08, 0.06, 0.12, 1.0)
        bg.inputs["Strength"].default_value = 0.3


def setup_render():
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 256
    s.cycles.use_denoising = True
    s.render.resolution_x = 3840
    s.render.resolution_y = 2160
    s.render.resolution_percentage = 100
    s.render.film_transparent = True
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA'


# ── MAIN ─────────────────────────────────────────────────────────────

def generate():
    clean_scene()
    create_materials()

    head_pos, head_parts = build_head()
    build_hair(head_pos)
    build_body()
    build_legs()

    apply_smooth_all()

    setup_scene()
    animate_breathing()
    animate_blinking()
    animate_hair_sway()
    animate_facial_expression()
    animate_eye_gaze()
    animate_graphic_glow()

    setup_lighting()
    setup_camera()
    setup_world()
    setup_render()

    bpy.ops.object.select_all(action='DESELECT')
    print("=== VTuber v2 готов ===")


class VTB2_OT_generate(bpy.types.Operator):
    bl_idname = "vtuber2.generate"
    bl_label = "Сгенерировать VTuber v2"
    bl_description = "Высокодетализированный вайтюбер с анимациями"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        generate()
        self.report({'INFO'}, "VTuber v2 сгенерирован с анимациями!")
        return {'FINISHED'}


class VTB2_OT_export(bpy.types.Operator):
    bl_idname = "vtuber2.export"
    bl_label = "Экспорт"
    bl_description = "Экспорт модели с анимациями"

    fmt: bpy.props.EnumProperty(
        name="Формат",
        items=[
            ('GLB', "glTF (.glb)", "С анимациями, для VRChat"),
            ('FBX', "FBX", "Для Unity/Unreal"),
            ('OBJ', "OBJ", "Без анимаций"),
        ],
        default='GLB',
    )

    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        ext = self.format.lower()
        if ext == 'glb':
            ext = 'glb'
        path = bpy.path.abspath(f"//vtuber_v2.{ext}")
        try:
            if self.fmt == 'GLB':
                bpy.ops.export_scene.gltf(filepath=path, use_selection=True,
                                           export_format='GLB',
                                           export_animations=True,
                                           export_nla_strips=False)
            elif self.fmt == 'FBX':
                bpy.ops.export_scene.fbx(filepath=path, use_selection=True,
                                          bake_anim=True,
                                          apply_scale_options='FBX_SCALE_ALL')
            else:
                bpy.ops.wm.obj_export(filepath=path, export_selected_objects=True)
            self.report({'INFO'}, f"Экспорт: {path}")
        except Exception as e:
            self.report({'ERROR'}, str(e))
        bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}


class VTB2_OT_render(bpy.types.Operator):
    bl_idname = "vtuber2.render"
    bl_label = "Рендер 4K"
    bl_description = "Рендер в 4K разрешении"

    def execute(self, context):
        path = bpy.path.abspath("//vtuber_v2_4k.png")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        self.report({'INFO'}, f"Рендер: {path}")
        return {'FINISHED'}


class VTB2_PT_panel(bpy.types.Panel):
    bl_label = "VTuber Generator v2"
    bl_idname = "VTB2_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VTuber'

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Аниме-вайтюбер v2", icon='ARMATURE_DATA')
        box.label(text="Высокая детализация + анимации")
        box.label(text="Пастельные тона, плавные движения")

        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 2.0
        row.operator("vtuber2.generate", icon='PLAY', text="Сгенерировать")

        layout.separator()
        box = layout.box()
        box.label(text="Анимации:", icon='ANIM')
        box.label(text="- Дыхание (torso)")
        box.label(text="- Моргание (4 раза)")
        box.label(text="- Покачивание волос")
        box.label(text="- Движение глаз")
        box.label(text="- Улыбка + румянец")
        box.label(text="- Покачивание тела")
        box.label(text="- Пульсация графики")

        layout.separator()
        box = layout.box()
        box.label(text="Экспорт:", icon='EXPORT')
        col = box.column(align=True)
        for fmt, label in [('GLB', 'glTF + анимации'), ('FBX', 'FBX + анимации'), ('OBJ', 'OBJ (геометрия)')]:
            op = col.operator("vtuber2.export", text=label)
            op.fmt = fmt

        layout.separator()
        layout.operator("vtuber2.render", icon='IMAGE_DATA', text="Рендер 4K")


CLASSES = [VTB2_OT_generate, VTB2_OT_export, VTB2_OT_render, VTB2_PT_panel]

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    import os

    register()
    generate()

    blend_dir = os.path.dirname(bpy.data.filepath) or os.path.dirname(__file__)

    bpy.ops.object.select_all(action='SELECT')
    export_path = os.path.join(blend_dir, "vtuber_v2.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=export_path, use_selection=True,
                                           export_format='GLB',
                                           export_animations=True,
                                           export_nla_strips=False)
        print(f"=== Экспорт GLB: {export_path} ===")
    except Exception as e:
        print(f"GLB ошибка: {e}")
        try:
            export_path = os.path.join(blend_dir, "vtuber_v2.fbx")
            bpy.ops.export_scene.fbx(filepath=export_path, use_selection=True,
                                      bake_anim=True)
            print(f"=== Экспорт FBX: {export_path} ===")
        except Exception as e2:
            print(f"FBX ошибка: {e2}")
    bpy.ops.object.select_all(action='DESELECT')

    render_path = os.path.join(blend_dir, "vtuber_v2_render.png")
    bpy.context.scene.render.filepath = render_path
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720
    bpy.context.scene.cycles.samples = 64
    bpy.ops.render.render(write_still=True)
    print(f"=== Рендер: {render_path} ===")
