import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.0078125, 0.0, -0.078125), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.007236842105263158, 0.0).lineTo(0.007236842105263158, 0.07870065789473685).lineTo(0.0859375, 0.07870065789473685).lineTo(0.0859375, 0.0859375).lineTo(0.0, 0.0859375).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
