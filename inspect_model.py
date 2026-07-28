import bpy, os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for b in bpy.data.meshes: bpy.data.meshes.remove(b)
for b in bpy.data.materials: bpy.data.materials.remove(b)
for b in bpy.data.images: bpy.data.images.remove(b)

bpy.ops.import_scene.gltf(filepath=r'C:\Users\Admin\Documents\Default Project\source\AnimeCharacter.glb')

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        for m in obj.data.materials:
            if m and m.use_nodes:
                print(f'Material: {m.name}')
                for n in m.node_tree.nodes:
                    print(f'  Node: {n.name} ({n.type})')
                    if n.type == 'TEX_IMAGE':
                        img = n.image
                        if img:
                            print(f'    Image: {img.name} {img.size[0]}x{img.size[1]}')
                print('Links:')
                for link in m.node_tree.links:
                    print(f'  {link.from_node.name}.{link.from_socket.name} -> {link.to_node.name}.{link.to_socket.name}')
