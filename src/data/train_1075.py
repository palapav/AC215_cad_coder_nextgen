import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.3984375, 0.34375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.625, 0.19736842105263158).lineTo(0.0, 0.39473684210526316).threePointArc((-0.26956176457540487, 0.19736842105263158), (0.0, 0.0)).close()
solid0=wp_sketch0.add(loop0).extrude(0.34375)
solid=solid0
