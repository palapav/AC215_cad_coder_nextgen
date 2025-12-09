import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.671875, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.035526315789473684, 0.0).circle(0.035526315789473684)
loop1=wp_sketch0.moveTo(0.035526315789473684, 0.0).circle(0.024424342105263157)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.015625)
solid=solid0
