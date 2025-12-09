import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.2578125, -0.2578125), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.027138157894736843, -0.027138157894736843).lineTo(0.2578125, 0.20353618421052633).lineTo(0.2578125, 0.2578125).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.1171875)
solid=solid0
