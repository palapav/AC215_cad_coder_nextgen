import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.1015625, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.10263157894736843, 0.0).circle(0.10049342105263158)
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
