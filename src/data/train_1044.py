import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.6796875, -0.375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.4296875, 0.0).lineTo(1.4296875, 0.4665296052631579).lineTo(0.0, 0.4665296052631579).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.0390625)
solid=solid0
