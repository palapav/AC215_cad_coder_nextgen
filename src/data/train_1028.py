import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.5234375, -0.75, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.09375, 0.0).lineTo(1.09375, 1.09375).lineTo(0.0, 1.09375).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.546875)
solid=solid0
