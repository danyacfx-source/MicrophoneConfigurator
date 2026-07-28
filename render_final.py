import bpy, math, os
from mathutils import Vector


def run():
    # ── CLEAN ──
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in bpy.data.meshes: bpy.data.meshes.remove(b)
    for b in bpy.data.materials: bpy.data.materials.remove(b)
    for b in bpy.data.cameras: bpy.data.cameras.remove(b)
    for b in bpy.data.lights: bpy.data.lights.remove(b)
    for b in bpy.data.worlds: bpy.data.worlds.remove(b)

    # ── IMPORT ──
    bpy.ops.import_scene.gltf(filepath=r'C:\Users\Admin\Documents\Default Project\source\AnimeCharacter.glb')
    obj = None
    for o in bpy.data.objects:
        if o.type == 'MESH':
            obj = o
            break

    # ── BOUNDS ──
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    for v in obj.data.vertices:
        w = obj.matrix_world @ v.co
        min_x = min(min_x, w.x); max_x = max(max_x, w.x)
        min_y = min(min_y, w.y); max_y = max(max_y, w.y)
        min_z = min(min_z, w.z); max_z = max(max_z, w.z)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    cz = (min_z + max_z) / 2
    sz = max(max_x - min_x, max_y - min_y, max_z - min_z)

    # ── MATERIAL: full anime rework ──
    for mat in obj.data.materials:
        if not (mat and mat.use_nodes):
            continue

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Remove all existing links
        for link in list(mat.node_tree.links):
            links.remove(link)

        bsdf = nodes.get("Principled BSDF") or nodes.get("Принципиальный BSDF")
        output = nodes.get("Material Output") or nodes.get("Вывод материала")

        # Find texture nodes
        tex_color = None
        tex_mr = None
        tex_normal = None
        for n in nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                if tex_color is None:
                    tex_color = n
                elif tex_mr is None:
                    tex_mr = n
                elif tex_normal is None:
                    tex_normal = n

        # ── NEW NODE TREE for anime look ──

        # 1) Hue/Saturation: push toward pastel + bright
        hue = nodes.new('ShaderNodeHueSaturation')
        hue.location = (-1200, 400)
        hue.inputs['Hue'].default_value = 0.53
        hue.inputs['Saturation'].default_value = 1.5
        hue.inputs['Value'].default_value = 1.2

        # 2) Brightness/Contrast
        bc = nodes.new('ShaderNodeBrightContrast')
        bc.location = (-1000, 400)
        bc.inputs['Bright'].default_value = 0.08
        bc.inputs['Contrast'].default_value = 15

        # 3) Separate RGB to isolate color channels for masking
        sep = nodes.new('ShaderNodeSeparateColor')
        sep.location = (-1000, 100)

        # 4) Math: create a mask for dark areas (clothing)
        math_dark = nodes.new('ShaderNodeMath')
        math_dark.location = (-800, 0)
        math_dark.operation = 'LESS_THAN'
        math_dark.inputs[1].default_value = 0.35

        # 5) Math: create a mask for bright areas (skin, light parts)
        math_bright = nodes.new('ShaderNodeMath')
        math_bright.location = (-800, 150)
        math_bright.operation = 'GREATER_THAN'
        math_bright.inputs[1].default_value = 0.55

        # 6) Mix dark mask: clothing becomes dark blue/purple
        mix_dark = nodes.new('ShaderNodeMix')
        mix_dark.data_type = 'RGBA'
        mix_dark.location = (-600, 200)
        mix_dark.blend_type = 'MIX'
        mix_dark.inputs[6].default_value = (0.18, 0.18, 0.48, 1)   # Dark blue hoodie
        mix_dark.inputs[7].default_value = (0.0, 0.0, 0.0, 1)      # passthrough

        # 7) Color ramp for emission (neon graphics on hoodie)
        emit_ramp = nodes.new('ShaderNodeValToRGB')
        emit_ramp.location = (-800, -200)
        emit_ramp.color_ramp.elements[0].position = 0.55
        emit_ramp.color_ramp.elements[1].position = 0.85
        emit_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        emit_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

        # 8) Emission color mixer: neon pink + cyan
        emit_col = nodes.new('ShaderNodeMix')
        emit_col.data_type = 'RGBA'
        emit_col.location = (-500, -300)
        emit_col.blend_type = 'OVERLAY'
        emit_col.inputs[0].default_value = 0.5
        emit_col.inputs[6].default_value = (0.98, 0.35, 0.72, 1)   # Neon pink
        emit_col.inputs[7].default_value = (0.35, 0.82, 1.00, 1)   # Cyan

        # 9) Emission strength multiply
        emit_str = nodes.new('ShaderNodeMath')
        emit_str.location = (-300, -250)
        emit_str.operation = 'MULTIPLY'
        emit_str.inputs[1].default_value = 3.0

        # 10) Fresnel for rim light effect
        fresnel = nodes.new('ShaderNodeFresnel')
        fresnel.location = (-500, -450)
        fresnel.inputs['IOR'].default_value = 1.45

        # 11) Mix for rim tint
        rim_mix = nodes.new('ShaderNodeMix')
        rim_mix.data_type = 'RGBA'
        rim_mix.location = (-300, -450)
        rim_mix.blend_type = 'ADD'
        rim_mix.inputs[0].default_value = 0.3
        rim_mix.inputs[6].default_value = (0.70, 0.55, 1.00, 1)    # Purple rim
        rim_mix.inputs[7].default_value = (0.0, 0.0, 0.0, 1)

        # ── WIRE IT ALL UP ──

        # Texture -> HueSat -> BrightContrast -> SepRGB
        if tex_color:
            links.new(tex_color.outputs['Color'], hue.inputs['Color'])
        links.new(hue.outputs['Color'], bc.inputs['Color'])
        links.new(bc.outputs['Color'], sep.inputs[0])

        # Luminance mask from Red channel
        links.new(sep.outputs[0], math_dark.inputs[0])
        links.new(sep.outputs[0], math_bright.inputs[0])

        # Dark mask controls clothing color overlay
        links.new(math_dark.outputs[0], mix_dark.inputs[0])

        # Final base color: original (through BC) mixed with dark blue for clothing
        links.new(bc.outputs['Color'], mix_dark.inputs[2])

        # Base Color -> BSDF
        links.new(mix_dark.outputs[2], bsdf.inputs['Base Color'])

        # Normal map
        if tex_normal:
            norm = nodes.new('ShaderNodeNormalMap')
            norm.location = (-800, -550)
            links.new(tex_normal.outputs['Color'], norm.inputs['Color'])
            links.new(norm.outputs['Normal'], bsdf.inputs['Normal'])

        # Roughness from MR texture
        if tex_mr:
            sep_mr = nodes.new('ShaderNodeSeparateColor')
            sep_mr.location = (-1000, -400)
            links.new(tex_mr.outputs['Color'], sep_mr.inputs[0])
            # Green = roughness, reduce it for shinier look
            rough_math = nodes.new('ShaderNodeMath')
            rough_math.location = (-800, -350)
            rough_math.operation = 'MULTIPLY'
            rough_math.inputs[1].default_value = 0.7
            links.new(sep_mr.outputs[0], rough_math.inputs[0])
            links.new(rough_math.outputs[0], bsdf.inputs['Roughness'])

        # Emission: texture -> ramp -> multiply -> BSDF
        if tex_color:
            links.new(tex_color.outputs['Color'], emit_ramp.inputs['Fac'])
        links.new(emit_ramp.outputs['Color'], emit_str.inputs[0])
        links.new(emit_str.outputs[0], bsdf.inputs['Emission Strength'])
        links.new(emit_col.outputs[2], bsdf.inputs['Emission Color'])

        # Fresnel rim
        links.new(fresnel.outputs['Fac'], rim_mix.inputs[0])
        links.new(rim_mix.outputs[2], bsdf.inputs['Emission Color'])

        # Specular
        try:
            bsdf.inputs['Specular IOR Level'].default_value = 0.5
        except:
            try:
                bsdf.inputs['Specular'].default_value = 0.5
            except:
                pass

        # Subsurface for skin translucency
        try:
            bsdf.inputs['Subsurface Weight'].default_value = 0.05
            bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.2, 0.1)
        except:
            pass

        print(f'Material reworked: {mat.name}')

    # ── CAMERA ──
    cam = bpy.data.cameras.new('Camera')
    cam.lens = 85
    cam.clip_end = 200
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 2.0
    cam_obj = bpy.data.objects.new('Camera', cam)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    dist = sz * 1.5
    cam_obj.location = (cx, cy - dist, cz + sz * 0.15)
    d = (Vector((cx, cy, cz + sz * 0.08)) - Vector(cam_obj.location)).normalized()
    cam_obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

    # ── LIGHTING: soft pastel studio (7 lights) ──
    for name, energy, szl, color, loc in [
        ('Key',        1000, sz*1.0, (1.00, 0.97, 0.93), (cx+sz*1.5, cy-sz*2.0, cz+sz*1.8)),
        ('Fill',       500,  sz*1.5, (0.88, 0.93, 1.00), (cx-sz*1.8, cy-sz*1.2, cz+sz*1.2)),
        ('Rim',        800,  sz*0.8, (0.93, 0.88, 1.00), (cx+sz*0.5, cy+sz*2.0, cz+sz*1.2)),
        ('HairRim',    400,  sz*0.5, (0.75, 0.55, 1.00), (cx+sz*1.0, cy+sz*1.2, cz+sz*2.2)),
        ('BottomFill', 250,  sz*2.0, (0.95, 0.90, 1.00), (cx, cy-sz*0.5, cz-sz*1.5)),
        ('Accent',     200,  sz*0.4, (1.00, 0.70, 0.90), (cx-sz*1.2, cy+sz*0.5, cz-sz*0.3)),
        ('Top',        300,  sz*2.0, (0.95, 0.92, 1.00), (cx, cy, cz+sz*4.0)),
    ]:
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = energy; l.size = szl; l.color = color
        o = bpy.data.objects.new(name, l)
        bpy.context.collection.objects.link(o)
        o.location = loc

    # ── WORLD ──
    w = bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.06, 0.04, 0.10, 1)
        bg.inputs['Strength'].default_value = 0.4

    # ── RENDER: CYCLES (path tracer like Octane) ──
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 256
    s.cycles.use_denoising = True
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.01
    s.render.resolution_x = 3840
    s.render.resolution_y = 2160
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.render.image_settings.file_format = 'PNG'

    bpy.ops.object.select_all(action='DESELECT')

    # ── RENDER 4K ──
    rp = r'C:\Users\Admin\Documents\Default Project\anime_vtuber_final_4k.png'
    s.render.filepath = rp
    bpy.ops.render.render(write_still=True)
    print(f'=== 4K: {rp} ===')

    print('=== DONE ===')


if __name__ == "__main__":
    run()
