import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.3828125, 0.0, -0.25), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.2504111842105263, 0.0).lineTo(0.13116776315789475, 0.07154605263157895).lineTo(1.0135690789473686, 0.07154605263157895).lineTo(0.8824013157894738, 0.0).lineTo(1.1328125, 0.0).lineTo(1.1328125, 0.2504111842105263).lineTo(0.0, 0.2504111842105263).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.578125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.3828125, 0.0, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop1=wp_sketch1.moveTo(1.1328125, 0.0).lineTo(1.1328125, 0.15501644736842107).lineTo(0.9420230263157895, 0.3458059210526316).lineTo(0.2027138157894737, 0.3458059210526316).lineTo(0.0, 0.15501644736842107).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.15625)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(0.0546875, -0.359375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.10263157894736843, 0.0).circle(0.10263157894736843)
solid2=wp_sketch2.add(loop2).extrude(-0.6328125)
solid=solid.cut(solid2)
