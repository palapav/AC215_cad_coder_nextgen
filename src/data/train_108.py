import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.159375, 0.0).lineTo(0.159375, 0.3984375).lineTo(0.0, 0.3984375).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.3984375)
solid=solid0
