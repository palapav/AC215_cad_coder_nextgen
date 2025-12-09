import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.0078125, 0.0, -0.015625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.005427631578947368, -0.014802631578947368).lineTo(0.010197368421052632, -0.014802631578947368).lineTo(0.015625, 0.0).lineTo(0.015625, 0.0013157894736842105).lineTo(0.0, 0.0013157894736842105).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
