import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.4609375, -0.390625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.2109375, 0.0).lineTo(1.2109375, 0.8030427631578947).lineTo(0.0, 0.8030427631578947).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.03125)
solid=solid0
