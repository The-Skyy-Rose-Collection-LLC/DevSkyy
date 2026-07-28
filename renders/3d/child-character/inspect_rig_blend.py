import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "child-character-rig.blend"))
for o in bpy.data.objects:
    print(o.name, o.type)
