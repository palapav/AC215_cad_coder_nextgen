import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.1328125, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.13026315789473686, 0.0).circle(0.13026315789473686)
solid0=wp_sketch0.add(loop0).extrude(0.6171875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.0390625, 0.0, 0.6171875), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.035526315789473684, 0.0).circle(0.035526315789473684)
solid1=wp_sketch1.add(loop1).extrude(0.0234375)
solid=solid.union(solid1)
