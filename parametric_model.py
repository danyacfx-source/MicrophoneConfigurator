import bpy
import bmesh
import math
from mathutils import Vector, Matrix


bl_info = {
    "name": "Parametric Model Generator",
    "author": "opencode",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > ParamGen",
    "description": "Генератор параметрических 3D-моделей",
    "category": "Mesh",
}


class PARAMGEN_Properties(bpy.types.PropertyGroup):
    model_type: bpy.props.EnumProperty(
        name="Тип модели",
        items=[
            ('VASE', "Ваза", "Тело вращения"),
            ('GEAR', "Шестерня", "Зубчатое колесо"),
            ('BRIDGE', "Мост", "Арочный мост"),
            ('TOWER', "Башня", "Параметрическая башня"),
        ],
        default='VASE',
    )
    height: bpy.props.FloatProperty(name="Высота", default=2.0, min=0.1, max=20.0)
    radius: bpy.props.FloatProperty(name="Радиус", default=0.5, min=0.05, max=10.0)
    segments: bpy.props.IntProperty(name="Сегменты", default=32, min=4, max=256)
    thickness: bpy.props.FloatProperty(name="Толщина", default=0.1, min=0.01, max=5.0)
    detail: bpy.props.IntProperty(name="Детализация", default=16, min=4, max=128)
    seed: bpy.props.IntProperty(name="Зерно (seed)", default=0, min=0, max=9999)
    export_format: bpy.props.EnumProperty(
        name="Экспорт",
        items=[
            ('NONE', "—", "Не экспортировать"),
            ('STL', "STL", "Формат для 3D-печати"),
            ('OBJ', "OBJ", "Wavefront OBJ"),
            ('GLTF', "glTF", "glTF 2.0"),
        ],
        default='NONE',
    )


def _rand(seed, i):
    x = (seed * 1103515245 + 12345 + i * 7919) & 0x7FFFFFFF
    return (x / 0x7FFFFFFF) * 2.0 - 1.0


def create_vase(props):
    verts = []
    faces = []
    n = props.segments
    h = props.height
    r = props.radius
    detail = props.detail

    for j in range(detail + 1):
        t = j / detail
        y = t * h
        profile_r = r * (
            0.3
            + 0.7 * math.sin(t * math.pi)
            + 0.15 * math.sin(t * math.pi * 3 + props.seed * 0.1)
        )
        profile_r = max(profile_r, 0.02)
        for i in range(n):
            angle = 2.0 * math.pi * i / n
            verts.append((
                profile_r * math.cos(angle),
                profile_r * math.sin(angle),
                y,
            ))

    for j in range(detail):
        for i in range(n):
            i0 = j * n + i
            i1 = j * n + (i + 1) % n
            i2 = (j + 1) * n + (i + 1) % n
            i3 = (j + 1) * n + i
            faces.append((i0, i1, i2, i3))

    mesh = bpy.data.meshes.new("Vase")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def create_gear(props):
    verts = []
    faces = []
    n_teeth = max(props.segments, 8)
    r = props.radius
    h = props.thickness
    tooth_h = r * 0.2
    tooth_w = 2 * math.pi / n_teeth * 0.4

    for z_off in [0, h]:
        center = len(verts)
        verts.append((0, 0, z_off))
        for i in range(n_teeth):
            a0 = 2 * math.pi * i / n_teeth
            a1 = a0 + tooth_w
            a2 = a0 + tooth_w * 2
            a3 = a0 + 2 * math.pi / n_teeth
            r_inner = r - tooth_h * 0.5
            r_outer = r + tooth_h * 0.5
            verts.append((r_inner * math.cos(a0), r_inner * math.sin(a0), z_off))
            verts.append((r_outer * math.cos(a1), r_outer * math.sin(a1), z_off))
            verts.append((r_outer * math.cos(a2), r_outer * math.sin(a2), z_off))
            verts.append((r_inner * math.cos(a3), r_inner * math.sin(a3), z_off))
            base = center + 1 + i * 4
            faces.append((center, base, base + 1, base + 2, base + 3))

    n_ring = n_teeth * 4 + 1
    for i in range(n_ring - 1):
        b0 = i + 1
        b1 = (i + 1) % (n_ring - 1) + 1
        faces.append((b0, b1, b1 + n_ring, b0 + n_ring))

    mesh = bpy.data.meshes.new("Gear")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def create_bridge(props):
    verts = []
    faces = []
    n = props.segments
    span = props.height
    rise = props.radius
    thick = props.thickness
    width = props.radius * 0.8
    arch_n = props.detail

    for side in [-1, 1]:
        base_idx = len(verts)
        for i in range(arch_n + 1):
            t = i / arch_n
            x = t * span
            y_top = rise * math.sin(t * math.pi)
            y_bot = y_top - thick
            verts.append((x, y_bot * side, 0))
            verts.append((x, y_top * side, 0))

        for i in range(arch_n):
            bi = base_idx + i * 2
            faces.append((bi, bi + 1, bi + 3, bi + 2))

    n_verts_side = (arch_n + 1) * 2
    for i in range(arch_n + 1):
        vi = i * 2
        vi2 = vi + 1
        vi2n = vi2 + n_verts_side
        vin = vi + n_verts_side
        faces.append((vi2, vi, vin, vi2n))

    mesh = bpy.data.meshes.new("Bridge")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def create_tower(props):
    verts = []
    faces = []
    floors = props.detail
    n = props.segments
    r = props.radius
    h = props.height
    floor_h = h / floors

    for j in range(floors + 1):
        y = j * floor_h
        shrink = 1.0 - 0.3 * (j / floors)
        cr = r * shrink
        jitter = _rand(props.seed, j) * 0.1 * r
        for i in range(n):
            angle = 2 * math.pi * i / n
            jr = cr + jitter * math.sin(angle * 3)
            verts.append((
                jr * math.cos(angle),
                jr * math.sin(angle),
                y,
            ))

    for j in range(floors):
        for i in range(n):
            i0 = j * n + i
            i1 = j * n + (i + 1) % n
            i2 = (j + 1) * n + (i + 1) % n
            i3 = (j + 1) * n + i
            faces.append((i0, i1, i2, i3))

    mesh = bpy.data.meshes.new("Tower")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


BUILDERS = {
    'VASE': create_vase,
    'GEAR': create_gear,
    'BRIDGE': create_bridge,
    'TOWER': create_tower,
}


class PARAMGEN_OT_generate(bpy.types.Operator):
    bl_idname = "paramgen.generate"
    bl_label = "Сгенерировать модель"
    bl_description = "Создать параметрическую модель"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.paramgen_props
        builder = BUILDERS.get(props.model_type)
        if not builder:
            self.report({'ERROR'}, "Неизвестный тип модели")
            return {'CANCELLED'}

        mesh = builder(props)
        obj = bpy.data.objects.new(mesh.name, mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        if obj.type == 'MESH' and not obj.data.polygons:
            self.report({'WARNING'}, "Модель пустая (0 полигонов)")

        if props.export_format != 'NONE':
            path = bpy.path.abspath("//")
            if path:
                ext = props.export_format.lower()
                if ext == 'gltf':
                    ext = 'glb'
                filepath = bpy.path.join(path, f"parametric_model.{ext}")
                if props.export_format == 'STL':
                    bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
                elif props.export_format == 'OBJ':
                    bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
                elif props.export_format == 'GLTF':
                    bpy.ops.export_scene.glb(filepath=filepath, use_selection=True)
                self.report({'INFO'}, f"Экспортировано: {filepath}")

        self.report({'INFO'}, f"Создано: {mesh.name}")
        return {'FINISHED'}


class PARAMGEN_OT_add_material(bpy.types.Operator):
    bl_idname = "paramgen.add_material"
    bl_label = "Добавить материал"
    bl_description = "Назначить случайный материал активному объекту"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Выберите меш-объект")
            return {'CANCELLED'}

        mat = bpy.data.materials.new(name="ParamGen_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            import random
            r = random.random()
            g = random.random()
            b = random.random()
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            bsdf.inputs["Metallic"].default_value = random.random() * 0.3
            bsdf.inputs["Roughness"].default_value = random.random() * 0.5 + 0.2

        obj.data.materials.clear()
        obj.data.materials.append(mat)
        self.report({'INFO'}, "Материал добавлен")
        return {'FINISHED'}


class PARAMGEN_PT_panel(bpy.types.Panel):
    bl_label = "Параметрический генератор"
    bl_idname = "PARAMGEN_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ParamGen'

    def draw(self, context):
        layout = self.layout
        props = context.scene.paramgen_props

        layout.prop(props, "model_type")
        layout.separator()

        col = layout.column(align=True)
        col.prop(props, "height")
        col.prop(props, "radius")
        col.prop(props, "segments")
        col.prop(props, "thickness")
        col.prop(props, "detail")
        col.prop(props, "seed")

        layout.separator()
        layout.prop(props, "export_format")

        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("paramgen.generate", icon='MESH_DATA')

        layout.separator()
        layout.operator("paramgen.add_material", icon='MATERIAL')


CLASSES = [
    PARAMGEN_Properties,
    PARAMGEN_OT_generate,
    PARAMGEN_OT_add_material,
    PARAMGEN_PT_panel,
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.paramgen_props = bpy.props.PointerProperty(type=PARAMGEN_Properties)


def unregister():
    del bpy.types.Scene.paramgen_props
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
