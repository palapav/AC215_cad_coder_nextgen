import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.4296875, 0.0, -0.234375), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.4342105263157895, 0.0).lineTo(0.859375, 0.0).lineTo(0.859375, 0.23519736842105265).lineTo(0.859375, 0.4613486842105263).lineTo(0.4342105263157895, 0.4613486842105263).lineTo(0.0, 0.4613486842105263).lineTo(0.0, 0.23519736842105265).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.4342105263157895, 0.2532894736842105).circle(0.11759868421052633)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(-0.109375)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.4296875, 0.0, -0.3359375), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop2=wp_sketch1.moveTo(0.859375, 0.0).lineTo(0.859375, 0.10855263157894737).lineTo(0.4342105263157895, 0.10855263157894737).lineTo(0.0, 0.10855263157894737).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop2).extrude(-0.75)
solid=solid.union(solid1)
