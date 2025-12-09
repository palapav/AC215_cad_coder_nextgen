import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.0390625, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.2644736842105263, 0.0).circle(0.2644736842105263)
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.03125, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.20131578947368423, 0.0).circle(0.20131578947368423)
solid1=wp_sketch1.add(loop1).extrude(0.671875)
solid=solid.cut(solid1)
