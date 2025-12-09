import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, 0.0, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.6328125, 0.0).lineTo(0.6328125, 0.019983552631578947).lineTo(0.0, 0.019983552631578947).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.3203125, -0.6328125, 0.015625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.003947368421052632, 0.0).circle(0.003947368421052632)
solid1=wp_sketch1.add(loop1).extrude(-0.015625)
solid=solid.cut(solid1)
