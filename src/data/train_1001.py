import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.4140625, -0.0546875), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.12631578947368421).lineTo(0.25263157894736843, 0.25263157894736843).lineTo(0.25263157894736843, 0.37894736842105264).lineTo(0.0, 0.37894736842105264).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
