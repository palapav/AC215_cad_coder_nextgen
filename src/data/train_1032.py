import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.328125, 0.0, -0.1015625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.12631578947368421, 0.0).lineTo(0.12631578947368421, 0.12631578947368421).lineTo(0.3736842105263158, 0.12631578947368421).lineTo(0.3736842105263158, 0.0).lineTo(0.5, 0.0).lineTo(0.5, 0.3736842105263158).lineTo(0.0, 0.3736842105263158).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.328125, -0.625, 0.2734375), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.5, 0.0).lineTo(0.5, 0.5).lineTo(0.0, 0.5).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(-0.125)
solid=solid.cut(solid1)
