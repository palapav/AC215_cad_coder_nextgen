import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.4140625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.5546875, 0.0).lineTo(0.5546875, 0.41455592105263156).lineTo(0.0, 0.41455592105263156).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.0078125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.4140625, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.75, 0.0).lineTo(0.75, 0.41842105263157897).lineTo(0.0, 0.41842105263157897).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(-0.0078125)
solid=solid.union(solid1)
