import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.3046875), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(1.15625, 0.0).lineTo(1.15625, 0.09736842105263158).lineTo(0.912828947368421, 0.09736842105263158).lineTo(0.912828947368421, 0.34078947368421053).lineTo(0.8154605263157895, 0.34078947368421053).threePointArc((0.578125, 0.10345394736842105), (0.34078947368421053, 0.34078947368421053)).lineTo(0.24342105263157893, 0.34078947368421053).lineTo(0.24342105263157893, 0.09736842105263158).lineTo(0.0, 0.09736842105263158).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.4375)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.2421875, -0.21875, 0.3984375), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.04736842105263158, 0.0).circle(0.04736842105263158)
solid1=wp_sketch1.add(loop1).extrude(-0.09375)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.6796875, -0.21875, 0.3984375), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.04736842105263158, 0.0).circle(0.04736842105263158)
solid2=wp_sketch2.add(loop2).extrude(-0.09375)
solid=solid.cut(solid2)
