import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.0078125, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.007894736842105263, 0.0).circle(0.007894736842105263)
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
