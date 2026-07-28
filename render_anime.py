import bpy, math, os
from mathutils import Vector


def clean():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in bpy.data.meshes: bpy.data.meshes.remove(b)
    for b in bpy.data.materials: bpy.data.materials.remove(b)
    for b in bpy.data.cameras: bpy.data.cameras.remove(b)
    for b in bpy.data.lights: bpy.data.lights.remove(b)
    for b in bpy.data.worlds: bpy.data.worlds.remove(b)


def run():
    clean()

    # ── IMPORT MODEL ──
    bpy.ops.import_scene.gltf(filepath=r'C:\Users\Admin\Documents\Default Project\source\AnimeCharacter.glb')

    obj = None
    for o in bpy.data.objects:
        if o.type == 'MESH':
            obj = o
            break
    if not obj:
        print("ERROR: no mesh found")
        return

    # ── FIND BOUNDS ──
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
    print(f'Bounds: center=({cx:.2f},{cy:.2f},{cz:.2f}) size={sz:.2f}')

    # ── MODIFY MATERIAL: pastel anime style ──
    for mat in obj.data.materials:
        if not (mat and mat.use_nodes):
            continue

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF") or nodes.get("Принципиальный BSDF")
        if not bsdf:
            continue

        # Find the base color texture node
        tex_node = None
        for n in nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                # First texture is base color
                if tex_node is None:
                    tex_node = n
                    break

        # Create color grading nodes
        # Hue/Saturation for pastel palette
        hue_sat = nodes.new('ShaderNodeHueSaturation')
        hue_sat.location = (-400, 300)
        hue_sat.inputs['Hue'].default_value = 0.55
        hue_sat.inputs['Saturation'].default_value = 1.3
        hue_sat.inputs['Value'].default_value = 1.15

        # RGB Curves for brightness/contrast
        curves = nodes.new('ShaderNodeRGBCurve')
        curves.location = (-250, 300)
        curve = curves.mapping.curves[0]
        curve.points.new(0.25, 0.35)
        curve.points.new(0.75, 0.80)

        # ColorRamp for emission mask (glow on hoodie graphics)
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.location = (-400, -100)
        ramp.color_ramp.elements[0].position = 0.6
        ramp.color_ramp.elements[1].position = 0.9
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

        # Math node to boost emission
        emit_mult = nodes.new('ShaderNodeMath')
        emit_mult.location = (-200, -100)
        emit_mult.operation = 'MULTIPLY'
        emit_mult.inputs[1].default_value = 2.0

        # Pastel tint node
        tint = nodes.new('ShaderNodeMix')
        tint.data_type = 'RGBA'
        tint.location = (-150, 300)
        tint.inputs[6].default_value = (0.70, 0.55, 1.0, 1)  # Pastel purple tint
        tint.inputs[7].default_value = (0.45, 0.85, 1.0, 1)  # Pastel blue tint
        tint.blend_type = 'OVERLAY'
        tint.inputs[0].default_value = 0.15

        # Emission color - neon pink + cyan
        emit_color = nodes.new('ShaderNodeMix')
        emit_color.data_type = 'RGBA'
        emit_color.location = (-200, -250)
        emit_color.inputs[6].default_value = (0.98, 0.30, 0.70, 1)  # Neon pink
        emit_color.inputs[7].default_value = (0.30, 0.80, 1.0, 1)   # Cyan
        emit_color.blend_type = 'OVERLAY'
        emit_color.inputs[0].default_value = 0.5

        # Wire everything up
        # Disconnect old links to BSDF Base Color
        for link in links:
            if link.to_node == bsdf and link.to_socket.name in ('Base Color', 'Base Color'):
                links.remove(link)

        # Base Color: Texture -> HueSat -> Curves -> Tint -> BSDF
        if tex_node:
            links.new(tex_node.outputs['Color'], hue_sat.inputs['Color'])
        links.new(hue_sat.outputs['Color'], curves.inputs['Color'])
        links.new(curves.outputs['Color'], tint.inputs[2])
        links.new(tint.outputs[2], bsdf.inputs['Base Color'])

        # Emission: Texture -> Ramp -> Math * 2 -> BSDF Emission Strength
        if tex_node:
            links.new(tex_node.outputs['Color'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], emit_mult.inputs[0])
        links.new(emit_mult.outputs[0], bsdf.inputs['Emission Strength'])

        # Emission Color
        links.new(emit_color.outputs[2], bsdf.inputs['Emission Color'])

        # Boost specular for anime look
        try:
            bsdf.inputs['Specular IOR Level'].default_value = 0.6
        except:
            try:
                bsdf.inputs['Specular'].default_value = 0.6
            except:
                pass

        # Reduce roughness slightly for shinier anime look
        try:
            bsdf.inputs['Roughness'].default_value = 0.35
        except:
            pass

        print(f'Material modified: {mat.name}')

    # ── CAMERA: portrait 85mm, front view ──
    cam = bpy.data.cameras.new('Camera')
    cam.lens = 85
    cam.clip_end = 200
    cam.dof.use_dof = True
    cam.dof.aperture_fstop = 2.8
    cam_obj = bpy.data.objects.new('Camera', cam)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    cam_dist = sz * 1.5
    cam_obj.location = (cx, cy - cam_dist, cz + sz * 0.15)
    direction = (Vector((cx, cy, cz + sz * 0.08)) - Vector(cam_obj.location)).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    # ── LIGHTING: soft pastel studio ──
    lights_def = [
        ('Key',       900,  sz*0.9, (1.00, 0.97, 0.94), (cx+sz*1.3, cy-sz*1.8, cz+sz*1.6)),
        ('Fill',      450,  sz*1.4, (0.90, 0.94, 1.00), (cx-sz*1.6, cy-sz*1.0, cz+sz*1.0)),
        ('Rim',       700,  sz*0.7, (0.94, 0.90, 1.00), (cx+sz*0.4, cy+sz*1.8, cz+sz*1.1)),
        ('HairLight', 350,  sz*0.5, (0.80, 0.60, 1.00), (cx+sz*0.8, cy+sz*1.0, cz+sz*2.0)),
        ('Accent',    200,  sz*0.4, (1.00, 0.70, 0.90), (cx-sz*1.0, cy+sz*0.5, cz-sz*0.2)),
        ('Top',       250,  sz*1.8, (0.95, 0.92, 1.00), (cx, cy, cz+sz*3.5)),
    ]
    for name, energy, szl, color, loc in lights_def:
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = energy
        l.size = szl
        l.color = color
        o = bpy.data.objects.new(name, l)
        bpy.context.collection.objects.link(o)
        o.location = loc

    # ── WORLD: dark pastel background ──
    w = bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    bg = w.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.08, 0.06, 0.14, 1)
        bg.inputs['Strength'].default_value = 0.6

    # ── RENDER: 4K EEVEE with bloom ──
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    try:
        s.eevee.use_bloom = True
        s.eevee.bloom_threshold = 0.6
        s.eevee.bloom_intensity = 0.4
        s.eevee.bloom_radius = 6.5
    except:
        pass
    try:
        s.eevee.use_ssr = True
    except:
        pass

    s.render.resolution_x = 3840
    s.render.resolution_y = 2160
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA'

    # ── RENDER ──
    bpy.ops.object.select_all(action='DESELECT')
    rp = r'C:\Users\Admin\Documents\Default Project\anime_vtuber_4k.png'
    s.render.filepath = rp
    bpy.ops.render.render(write_still=True)
    print(f'=== 4K RENDER: {rp} ===')

    # ── Also render a 1080p version ──
    s.render.resolution_x = 1920
    s.render.resolution_y = 1080
    rp2 = r'C:\Users\Admin\Documents\Default Project\anime_vtuber_1080.png'
    s.render.filepath = rp2
    bpy.ops.render.render(write_still=True)
    print(f'=== 1080p RENDER: {rp2} ===')

    print('=== ALL DONE ===')


if __name__ == "__main__":
    run()
