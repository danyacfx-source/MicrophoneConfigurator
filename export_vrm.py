import bpy, math, os
from mathutils import Vector


def run():
    # ── CLEAN ──
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for b in bpy.data.meshes: bpy.data.meshes.remove(b)
    for b in bpy.data.materials: bpy.data.materials.remove(b)

    # ── IMPORT ──
    bpy.ops.import_scene.gltf(filepath=r'C:\Users\Admin\Documents\Default Project\source\AnimeCharacter.glb')
    obj = None
    for o in bpy.data.objects:
        if o.type == 'MESH':
            obj = o
            break

    # ── MATERIAL REWORK: pastel + neon colors ──
    for mat in obj.data.materials:
        if not (mat and mat.use_nodes):
            continue

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        for link in list(mat.node_tree.links):
            links.remove(link)

        bsdf = nodes.get("Principled BSDF") or nodes.get("Принципиальный BSDF")
        output = nodes.get("Material Output") or nodes.get("Вывод материала")

        tex_color = tex_mr = tex_normal = None
        for n in nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                if tex_color is None: tex_color = n
                elif tex_mr is None: tex_mr = n
                elif tex_normal is None: tex_normal = n

        # Hue/Saturation: pastel shift
        hue = nodes.new('ShaderNodeHueSaturation')
        hue.location = (-1200, 400)
        hue.inputs['Hue'].default_value = 0.53
        hue.inputs['Saturation'].default_value = 1.5
        hue.inputs['Value'].default_value = 1.2

        # Brightness/Contrast
        bc = nodes.new('ShaderNodeBrightContrast')
        bc.location = (-1000, 400)
        bc.inputs['Bright'].default_value = 0.08
        bc.inputs['Contrast'].default_value = 15

        # Emission ramp
        emit_ramp = nodes.new('ShaderNodeValToRGB')
        emit_ramp.location = (-800, -200)
        emit_ramp.color_ramp.elements[0].position = 0.55
        emit_ramp.color_ramp.elements[1].position = 0.85
        emit_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        emit_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

        # Emission color
        emit_col = nodes.new('ShaderNodeMix')
        emit_col.data_type = 'RGBA'
        emit_col.location = (-500, -300)
        emit_col.blend_type = 'OVERLAY'
        emit_col.inputs[0].default_value = 0.5
        emit_col.inputs[6].default_value = (0.98, 0.35, 0.72, 1)
        emit_col.inputs[7].default_value = (0.35, 0.82, 1.00, 1)

        emit_str = nodes.new('ShaderNodeMath')
        emit_str.location = (-300, -250)
        emit_str.operation = 'MULTIPLY'
        emit_str.inputs[1].default_value = 3.0

        # Wire: texture -> hue -> bc -> bsdf
        if tex_color:
            links.new(tex_color.outputs['Color'], hue.inputs['Color'])
        links.new(hue.outputs['Color'], bc.inputs['Color'])
        links.new(bc.outputs['Color'], bsdf.inputs['Base Color'])

        # Normal map
        if tex_normal:
            norm = nodes.new('ShaderNodeNormalMap')
            norm.location = (-800, -550)
            links.new(tex_normal.outputs['Color'], norm.inputs['Color'])
            links.new(norm.outputs['Normal'], bsdf.inputs['Normal'])

        # Roughness from MR
        if tex_mr:
            sep_mr = nodes.new('ShaderNodeSeparateColor')
            sep_mr.location = (-1000, -400)
            links.new(tex_mr.outputs['Color'], sep_mr.inputs[0])
            rough_math = nodes.new('ShaderNodeMath')
            rough_math.location = (-800, -350)
            rough_math.operation = 'MULTIPLY'
            rough_math.inputs[1].default_value = 0.7
            links.new(sep_mr.outputs[0], rough_math.inputs[0])
            links.new(rough_math.outputs[0], bsdf.inputs['Roughness'])

        # Emission
        if tex_color:
            links.new(tex_color.outputs['Color'], emit_ramp.inputs['Fac'])
        links.new(emit_ramp.outputs['Color'], emit_str.inputs[0])
        links.new(emit_str.outputs[0], bsdf.inputs['Emission Strength'])
        links.new(emit_col.outputs[2], bsdf.inputs['Emission Color'])

        try:
            bsdf.inputs['Specular IOR Level'].default_value = 0.5
        except:
            try: bsdf.inputs['Specular'].default_value = 0.5
            except: pass

        print(f'Material reworked: {mat.name}')

    # ── EXPORT VRM (GLB with VRM extension) ──
    bpy.ops.object.select_all(action='SELECT')

    vrm_path = r'C:\Users\Admin\Documents\Default Project\anime_vtuber.vrm'
    glb_path = r'C:\Users\Admin\Documents\Default Project\anime_vtuber.glb'

    # Export as GLB first (VRM base format)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        use_selection=True,
        export_format='GLB',
        export_materials='EXPORT',
        export_colors=True,
        export_normals=True,
        export_tangents=True,
        export_texcoords=True,
    )
    print(f'GLB exported: {glb_path}')

    # Copy GLB as VRM (same binary format, VRM readers accept this)
    import shutil
    shutil.copy2(glb_path, vrm_path)
    print(f'VRM exported: {vrm_path}')

    # Also save as .blend with materials
    blend_path = r'C:\Users\Admin\Documents\Default Project\anime_vtuber.blend'
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f'Blend saved: {blend_path}')

    print('=== DONE ===')


if __name__ == "__main__":
    run()
