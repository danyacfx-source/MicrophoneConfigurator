import bpy
import bmesh
import math
from mathutils import Vector


def clean():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in bpy.data.meshes: bpy.data.meshes.remove(b)
    for b in bpy.data.materials: bpy.data.materials.remove(b)
    for b in bpy.data.cameras: bpy.data.cameras.remove(b)
    for b in bpy.data.lights: bpy.data.lights.remove(b)
    for b in bpy.data.worlds: bpy.data.worlds.remove(b)
    for b in bpy.data.actions: bpy.data.actions.remove(b)


def M(name, rgb, rough=0.5, emit=0.0, spec=0.5, subsurf=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Specular IOR Level"].default_value = spec
        if emit > 0:
            b.inputs["Emission Color"].default_value = (*rgb, 1)
            b.inputs["Emission Strength"].default_value = emit
        try:
            b.inputs["Subsurface Weight"].default_value = subsurf
        except: pass
    return m


def A(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)


def add_subsurf(obj, levels=2, render_levels=3):
    mod = obj.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = levels
    mod.render_levels = render_levels


def S(name, loc, scale, seg=24, ring=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, location=loc, radius=1)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    add_subsurf(o, 2, 3)
    bpy.ops.object.shade_smooth()
    return o

def B(name, loc, scale):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    add_subsurf(o, 2, 3)
    bpy.ops.object.shade_smooth()
    return o

def C(name, loc, scale, seg=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, location=loc, radius=1, depth=1)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    add_subsurf(o, 2, 3)
    bpy.ops.object.shade_smooth()
    return o

def K(name, loc, scale, seg=16):
    bpy.ops.mesh.primitive_cone_add(vertices=seg, location=loc, radius1=1, radius2=0, depth=1)
    o = bpy.context.active_object; o.name = name; o.scale = scale
    add_subsurf(o, 1, 2)
    bpy.ops.object.shade_smooth()
    return o


# ─── MATERIALS (пастельные тона) ──────────────────────────────────

MAT = {}

def make_materials():
    MAT["skin"]       = M("Skin",       (0.99, 0.90, 0.82), rough=0.45, subsurf=0.15)
    MAT["skin_shadow"]= M("SkinShade",  (0.90, 0.78, 0.70), rough=0.50)
    MAT["hair"]       = M("Hair",       (0.65, 0.40, 1.00), rough=0.30, emit=0.05)
    MAT["hair_light"] = M("HairLight",  (0.80, 0.60, 1.00), rough=0.25, emit=0.10)
    MAT["hoodie"]     = M("Hoodie",     (0.22, 0.22, 0.58), rough=0.65)
    MAT["hoodie_dark"]= M("HoodieDark", (0.15, 0.15, 0.42), rough=0.70)
    MAT["graphic"]    = M("Graphic",    (0.98, 0.40, 0.72), rough=0.25, emit=1.0)
    MAT["graphic2"]   = M("Graphic2",   (0.40, 0.82, 1.00), rough=0.25, emit=0.8)
    MAT["eye_white"]  = M("EyeWhite",   (1.00, 1.00, 1.00), rough=0.05, spec=0.8)
    MAT["iris"]       = M("Iris",       (0.30, 0.50, 1.00), rough=0.10, spec=0.9, emit=0.15)
    MAT["pupil"]      = M("Pupil",      (0.02, 0.02, 0.06), rough=0.02, spec=1.0)
    MAT["highlight"]  = M("Highlight",  (1.00, 1.00, 1.00), rough=0.00, spec=1.0)
    MAT["mouth"]      = M("Mouth",      (0.90, 0.35, 0.45), rough=0.35)
    MAT["mouth_in"]   = M("MouthIn",    (0.55, 0.12, 0.18), rough=0.40)
    MAT["blush"]      = M("Blush",      (1.00, 0.70, 0.75), rough=0.50, emit=0.15)
    MAT["eyebrow"]    = M("Eyebrow",    (0.50, 0.30, 0.80), rough=0.40)
    MAT["pants"]      = M("Pants",      (0.16, 0.16, 0.38), rough=0.55)
    MAT["shoe"]       = M("Shoe",       (0.96, 0.96, 1.00), rough=0.20)
    MAT["shoe_sole"]  = M("ShoeSole",   (0.25, 0.25, 0.28), rough=0.80)
    MAT["belt"]       = M("Belt",       (0.90, 0.35, 0.60), rough=0.35)
    MAT["hand"]       = M("Hand",       (0.97, 0.88, 0.80), rough=0.45, subsurf=0.12)


# ─── MODEL ──────────────────────────────────────────────────────────

def build_character():
    HP = (0, 0, 1.62)

    # ── HEAD ──
    head = S("Head", HP, (0.48, 0.54, 0.52), 32, 20)
    A(head, MAT["skin"])

    # ── CHEEKS (blush) ──
    cl = S("CheekL", (-0.28, 0.28, 1.50), (0.10, 0.04, 0.07), 12, 8)
    A(cl, MAT["blush"])
    cr = S("CheekR", (0.28, 0.28, 1.50), (0.10, 0.04, 0.07), 12, 8)
    A(cr, MAT["blush"])

    # ── EYES ──
    for side in [-1, 1]:
        t = "L" if side < 0 else "R"

        ew = S(f"EyeW_{t}", (side*0.17, 0.42, 1.63), (0.14, 0.06, 0.16), 20, 14)
        A(ew, MAT["eye_white"])

        ir = S(f"Iris_{t}", (side*0.17, 0.46, 1.63), (0.10, 0.035, 0.11), 20, 14)
        A(ir, MAT["iris"])

        pu = S(f"Pupil_{t}", (side*0.17, 0.48, 1.63), (0.045, 0.02, 0.05), 14, 8)
        A(pu, MAT["pupil"])

        h1 = S(f"HL1_{t}", (side*0.14, 0.49, 1.66), (0.025, 0.015, 0.025), 8, 6)
        A(h1, MAT["highlight"])
        h2 = S(f"HL2_{t}", (side*0.20, 0.48, 1.61), (0.013, 0.010, 0.013), 8, 6)
        A(h2, MAT["highlight"])

        lu = S(f"LidUp_{t}", (side*0.17, 0.44, 1.75), (0.15, 0.03, 0.025), 14, 8)
        A(lu, MAT["skin_shadow"])
        ld = S(f"LidDn_{t}", (side*0.17, 0.44, 1.52), (0.14, 0.025, 0.02), 14, 8)
        A(ld, MAT["skin_shadow"])

        br = B(f"Brow_{t}", (side*0.17, 0.43, 1.78), (0.17, 0.022, 0.018))
        br.rotation_euler = (0, 0, math.radians(side * 10))
        bpy.ops.object.transform_apply(rotation=True)
        A(br, MAT["eyebrow"])

    # ── NOSE ──
    nose = K("Nose", (0, 0.55, 1.55), (0.035, 0.035, 0.06), 10)
    nose.rotation_euler = (math.radians(80), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    A(nose, MAT["skin"])

    # ── MOUTH (cute open smile) ──
    mo = S("MouthOpen", (0, 0.50, 1.44), (0.07, 0.025, 0.035), 14, 8)
    A(mo, MAT["mouth_in"])
    ml = B("MouthLine", (0, 0.52, 1.46), (0.10, 0.012, 0.005))
    A(ml, MAT["mouth"])

    # ── EARS ──
    for side in [-1, 1]:
        tag = "L" if side < 0 else "R"
        ear = S(f"Ear_{tag}", (side*0.44, 0.0, 1.60), (0.055, 0.045, 0.10), 12, 8)
        ear.rotation_euler = (0, 0, math.radians(side * 12))
        bpy.ops.object.transform_apply(rotation=True)
        A(ear, MAT["skin"])

    # ── NECK ──
    neck = C("Neck", (0, 0, 1.15), (0.09, 0.09, 0.12), 14)
    A(neck, MAT["skin"])

    # ── HAIR ──
    hair_spikes = [
        (0.0,   0.12, 0.52, 0.10, 0.44, 0,    0),
        (-0.12, 0.05, 0.48, 0.085,0.40, -10,  15),
        (0.12,  0.05, 0.48, 0.085,0.40, 10,  -15),
        (-0.06, 0.20, 0.46, 0.075,0.34, -5,    8),
        (0.06,  0.20, 0.46, 0.075,0.34, 5,   -8),
        (-0.22, -0.05,0.42, 0.065,0.32, -15,  25),
        (0.22, -0.05, 0.42, 0.065,0.32, 15,  -25),
    ]
    for i, (ox,oy,oz,sx,sy,rz,rx) in enumerate(hair_spikes):
        c = K(f"HS{i}", (HP[0]+ox, HP[1]+oy, HP[2]+oz), (sx, sx, sy), 10)
        c.rotation_euler = (math.radians(rx), 0, math.radians(rz))
        bpy.ops.object.transform_apply(rotation=True)
        A(c, MAT["hair_light"] if i % 3 == 0 else MAT["hair"])

    bangs = [
        (-0.24, 0.44, 0.28, 0.12, 0.20, 0.05, 30,  -22),
        (-0.11, 0.52, 0.31, 0.10, 0.24, 0.05, 20,  -12),
        (0.00,  0.56, 0.33, 0.09, 0.26, 0.05, 0,    0),
        (0.11,  0.52, 0.31, 0.10, 0.24, 0.05, -20,  12),
        (0.24,  0.44, 0.28, 0.12, 0.20, 0.05, -30,  22),
    ]
    for i,(ox,oy,oz,sx,sy,sz,rz,rx) in enumerate(bangs):
        b = S(f"Bang{i}", (HP[0]+ox, HP[1]+oy, HP[2]+oz), (sx, sy, sz), 14, 10)
        b.rotation_euler = (math.radians(rx), 0, math.radians(rz))
        bpy.ops.object.transform_apply(rotation=True)
        A(b, MAT["hair"])

    side_h = [
        (-0.50, -0.05, -0.08, 0.14, 0.58, 0.10),
        (0.50, -0.05, -0.08, 0.14, 0.58, 0.10),
        (-0.44, -0.18, -0.22, 0.11, 0.48, 0.08),
        (0.44, -0.18, -0.22, 0.11, 0.48, 0.08),
    ]
    for i,(ox,oy,oz,sx,sy,sz) in enumerate(side_h):
        sh = S(f"SideH{i}", (HP[0]+ox, HP[1]+oy, HP[2]+oz), (sx, sy, sz), 14, 10)
        A(sh, MAT["hair"])

    back_h = [
        (0.0,  -0.42, 0.14, 0.44, 0.30, 0.50),
        (-0.28,-0.36, -0.05, 0.20, 0.24, 0.44),
        (0.28, -0.36, -0.05, 0.20, 0.24, 0.44),
        (-0.10,-0.48, -0.15, 0.16, 0.22, 0.36),
        (0.10, -0.48, -0.15, 0.16, 0.22, 0.36),
    ]
    for i,(ox,oy,oz,sx,sy,sz) in enumerate(back_h):
        bh = S(f"BackH{i}", (HP[0]+ox, HP[1]+oy, HP[2]+oz), (sx, sy, sz), 16, 10)
        A(bh, MAT["hair_light"] if i == 0 else MAT["hair"])

    ahoge = K("Ahoge", (HP[0]+0.02, HP[1]+0.28, HP[2]+0.56), (0.04, 0.04, 0.28), 8)
    ahoge.rotation_euler = (math.radians(-30), math.radians(10), math.radians(15))
    bpy.ops.object.transform_apply(rotation=True)
    A(ahoge, MAT["hair_light"])

    # ── BODY (HOODIE) ──
    torso = B("Torso", (0, 0, 0.60), (0.60, 0.34, 0.82))
    A(torso, MAT["hoodie"])

    cg = B("ChestGraphic", (0, 0.18, 0.82), (0.30, 0.008, 0.24))
    A(cg, MAT["graphic"])
    sl = B("StripeL", (-0.16, 0.18, 0.58), (0.055, 0.008, 0.42))
    A(sl, MAT["graphic2"])
    sr = B("StripeR", (0.16, 0.18, 0.58), (0.055, 0.008, 0.42))
    A(sr, MAT["graphic2"])

    hood = S("Hood", (0, -0.16, 1.04), (0.36, 0.32, 0.32), 20, 14)
    A(hood, MAT["hoodie_dark"])

    pocket = B("Pocket", (0, 0.19, 0.42), (0.34, 0.025, 0.16))
    A(pocket, MAT["hoodie_dark"])

    # ── ARMS ──
    for side in [-1, 1]:
        t = "L" if side < 0 else "R"
        sh = S(f"Sho{t}", (side*0.40, 0, 0.96), (0.12, 0.11, 0.13), 14, 10)
        A(sh, MAT["hoodie"])
        ua = C(f"UA{t}", (side*0.52, 0.02, 0.72), (0.10, 0.10, 0.32), 14)
        ua.rotation_euler = (0, math.radians(side*8), 0)
        bpy.ops.object.transform_apply(rotation=True)
        A(ua, MAT["hoodie"])
        el = S(f"El{t}", (side*0.57, 0.05, 0.54), (0.09, 0.08, 0.09), 12, 8)
        A(el, MAT["hoodie"])
        fa = C(f"FA{t}", (side*0.58, 0.10, 0.36), (0.085, 0.085, 0.26), 14)
        fa.rotation_euler = (math.radians(5), math.radians(side*5), 0)
        bpy.ops.object.transform_apply(rotation=True)
        A(fa, MAT["hoodie"])
        cu = C(f"Cu{t}", (side*0.59, 0.12, 0.22), (0.095, 0.095, 0.04), 14)
        A(cu, MAT["hoodie_dark"])
        ha = S(f"Ha{t}", (side*0.59, 0.16, 0.16), (0.075, 0.06, 0.085), 14, 10)
        A(ha, MAT["hand"])

    # ── BELT ──
    be = C("Belt", (0, 0, 0.22), (0.32, 0.32, 0.03), 20)
    be.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    A(be, MAT["belt"])

    # ── LEGS ──
    for side in [-1, 1]:
        t = "L" if side < 0 else "R"
        hi = S(f"Hi{t}", (side*0.17, 0, 0.18), (0.13, 0.12, 0.13), 14, 10)
        A(hi, MAT["pants"])
        ul = C(f"UL{t}", (side*0.17, 0, -0.06), (0.11, 0.11, 0.36), 14)
        A(ul, MAT["pants"])
        kn = S(f"Kn{t}", (side*0.17, 0.02, -0.26), (0.10, 0.09, 0.10), 12, 8)
        A(kn, MAT["pants"])
        ll = C(f"LL{t}", (side*0.17, 0.02, -0.50), (0.095, 0.095, 0.32), 14)
        A(ll, MAT["pants"])
        an = S(f"An{t}", (side*0.17, 0.04, -0.68), (0.075, 0.065, 0.075), 10, 8)
        A(an, MAT["shoe_sole"])
        sb = B(f"SB{t}", (side*0.17, 0.10, -0.74), (0.105, 0.19, 0.07))
        A(sb, MAT["shoe"])
        ss = B(f"SS{t}", (side*0.17, 0.10, -0.79), (0.115, 0.21, 0.03))
        A(ss, MAT["shoe_sole"])
        st = S(f"ST{t}", (side*0.17, 0.21, -0.74), (0.085, 0.06, 0.06), 10, 8)
        A(st, MAT["shoe"])

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT')


# ─── OUTLINE (anime toon effect) ──────────────────────────────────

def add_outline():
    outline_mat = M("Outline", (0.02, 0.02, 0.05), rough=1.0)
    outline_mat.use_backface_culling = True

    bpy.ops.object.select_all(action='SELECT')
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
        mod = obj.modifiers.new("Outline", 'SOLIDIFY')
        mod.thickness = 0.015
        mod.offset = -1
        mod.use_flip_normals = True
        mod.use_rim = False
        obj.data.materials.append(outline_mat)
        mod.material_offset = len(obj.data.materials) - 1
    bpy.ops.object.select_all(action='DESELECT')


# ─── LIGHTING ──────────────────────────────────────────────────────

def setup_lighting():
    lights = [
        ("Key",    600, 2.5, (1.0, 0.96, 0.92), (3.5, -3, 5)),
        ("Fill",   300, 3.5, (0.88, 0.92, 1.0), (-3.5, -2, 4)),
        ("Rim",    400, 2.0, (0.92, 0.88, 1.0), (0.5, 5, 4)),
        ("Accent", 150, 1.5, (0.75, 0.55, 1.0), (-2, 1, 0.5)),
        ("Top",    200, 4.0, (0.95, 0.90, 1.0), (0, 0, 7)),
    ]
    for name, energy, sz, color, loc in lights:
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = energy; l.size = sz; l.color = color
        o = bpy.data.objects.new(name, l)
        bpy.context.collection.objects.link(o)
        o.location = loc


def setup_camera():
    cam = bpy.data.cameras.new("Camera")
    cam.lens = 85
    cam.clip_end = 100
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 2.8
    co = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(co)
    bpy.context.scene.camera = co
    co.location = (0, -3.5, 1.55)
    d = Vector((0, 0, 1.2)) - Vector(co.location)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def setup_world():
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.10, 0.08, 0.15, 1)
        bg.inputs["Strength"].default_value = 0.8


def setup_render():
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    try:
        s.eevee.use_bloom = True
        s.eevee.bloom_threshold = 0.8
        s.eevee.bloom_intensity = 0.3
    except: pass
    try:
        s.eevee.use_ssr = True
    except: pass
    s.render.resolution_x = 3840
    s.render.resolution_y = 2160
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA'


# ─── ANIMATION ─────────────────────────────────────────────────────

def setup_animation():
    s = bpy.context.scene
    s.frame_start = 1
    s.frame_end = 72
    s.render.fps = 24

    torso = bpy.data.objects.get("Torso")
    if torso:
        if torso.animation_data is None: torso.animation_data_create()
        torso.animation_data.action = bpy.data.actions.new("Torso_A")
        for f, sc in [(1,(0.60,0.34,0.82)), (18,(0.609,0.34,0.829)),
                       (36,(0.60,0.34,0.82)), (54,(0.609,0.34,0.829)),
                       (72,(0.60,0.34,0.82))]:
            torso.scale = sc
            torso.keyframe_insert(data_path="scale", frame=f)

    ahoge = bpy.data.objects.get("Ahoge")
    if ahoge:
        if ahoge.animation_data is None: ahoge.animation_data_create()
        ahoge.animation_data.action = bpy.data.actions.new("Ahoge_A")
        orig = ahoge.rotation_euler.copy()
        for f, r in [(1, orig),
                      (18, (orig.x+math.radians(7), orig.y, orig.z+math.radians(10))),
                      (36, orig),
                      (54, (orig.x-math.radians(5), orig.y, orig.z-math.radians(8))),
                      (72, orig)]:
            ahoge.rotation_euler = r
            ahoge.keyframe_insert(data_path="rotation_euler", frame=f)

    for side in [-1, 1]:
        t = "L" if side < 0 else "R"
        obj = bpy.data.objects.get(f"SideH{0 if side < 0 else 3}")
        if obj:
            if obj.animation_data is None: obj.animation_data_create()
            obj.animation_data.action = bpy.data.actions.new(f"{obj.name}_A")
            orig = obj.location.copy()
            for f, l in [(1, orig),
                          (24, (orig.x+side*0.007, orig.y, orig.z+0.003)),
                          (48, (orig.x-side*0.005, orig.y, orig.z-0.002)),
                          (72, orig)]:
                obj.location = l
                obj.keyframe_insert(data_path="location", frame=f)

    for obj in bpy.data.objects:
        if obj.name.startswith("Iris_") or obj.name.startswith("Pupil_"):
            if obj.animation_data is None: obj.animation_data_create()
            obj.animation_data.action = bpy.data.actions.new(f"{obj.name}_A")
            orig = obj.location.copy()
            for f, l in [(1, orig),
                          (18, (orig.x+0.008, orig.y, orig.z+0.004)),
                          (36, (orig.x-0.005, orig.y, orig.z-0.003)),
                          (54, (orig.x+0.003, orig.y, orig.z+0.002)),
                          (72, orig)]:
                obj.location = l
                obj.keyframe_insert(data_path="location", frame=f)

    for obj in bpy.data.objects:
        if "Graphic" in obj.name or "Stripe" in obj.name:
            if obj.animation_data is None: obj.animation_data_create()
            obj.animation_data.action = bpy.data.actions.new(f"{obj.name}_A")
            orig = obj.scale.copy()
            for f, sc in [(1, orig),
                           (18, (orig.x*1.05, orig.y, orig.z*1.05)),
                           (36, orig),
                           (54, (orig.x*1.05, orig.y, orig.z*1.05)),
                           (72, orig)]:
                obj.scale = sc
                obj.keyframe_insert(data_path="scale", frame=f)


# ─── MAIN ──────────────────────────────────────────────────────────

def run():
    import os

    clean()
    make_materials()
    build_character()
    add_outline()
    setup_lighting()
    setup_camera()
    setup_world()
    setup_render()
    setup_animation()

    bpy.context.scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')

    blend_dir = os.path.dirname(bpy.data.filepath) or r"C:\Users\Admin\Documents\Default Project"

    rp = os.path.join(blend_dir, "vtuber_preset.png")
    bpy.context.scene.render.filepath = rp
    bpy.ops.render.render(write_still=True)
    print(f"=== RENDER 4K: {rp} ===")

    bpy.ops.object.select_all(action='SELECT')
    glb = os.path.join(blend_dir, "vtuber_preset.glb")
    try:
        bpy.ops.export_scene.gltf(filepath=glb, use_selection=True,
                                   export_format='GLB', export_animations=True,
                                   export_nla_strips=False)
        print(f"=== GLB: {glb} ===")
    except Exception as e:
        print(f"GLB error: {e}")

    bpy.ops.object.select_all(action='DESELECT')
    print("=== DONE ===")


if __name__ == "__main__":
    run()
