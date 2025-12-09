import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.1953125, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.17730263157894738, 0.0).lineTo(0.17730263157894738, 0.38281250000000006).lineTo(0.0, 0.38281250000000006).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.3046875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.1796875, -0.109375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.3782072368421052, 0.0).lineTo(0.5703125, 0.1140625).lineTo(0.3782072368421052, 0.22212171052631577).lineTo(0.0, 0.22212171052631577).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.1796875)
solid=solid.union(solid1)
