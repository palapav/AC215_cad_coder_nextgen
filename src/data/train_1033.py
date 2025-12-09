import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, -0.75, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(1.5, 0.0).lineTo(1.5, 1.5).lineTo(0.0, 1.5).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.015625)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.734375, -0.75, 0.015625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(1.46875, 0.0).lineTo(1.46875, 0.015460526315789473).lineTo(0.0, 0.015460526315789473).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop1).extrude(0.296875)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.75, -0.75, 0.015625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop2=wp_sketch2.moveTo(0.015789473684210527, 0.0).lineTo(0.015789473684210527, 0.015789473684210527).lineTo(0.015789473684210527, 1.4842105263157894).lineTo(0.015789473684210527, 1.5).lineTo(0.0, 1.5).lineTo(0.0, 0.0).close()
solid2=wp_sketch2.add(loop2).extrude(0.296875)
solid=solid.union(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(0.734375, -0.75, 0.015625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop3=wp_sketch3.moveTo(0.015789473684210527, 0.0).lineTo(0.015789473684210527, 1.5).lineTo(0.0, 1.5).lineTo(0.0, 1.4842105263157894).lineTo(0.0, 0.015789473684210527).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(0.296875)
solid=solid.union(solid3)
# Generating a workplane for sketch 4
wp_sketch4 = cq.Workplane(cq.Plane(cq.Vector(-0.734375, 0.734375, 0.015625), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop4=wp_sketch4.moveTo(1.46875, 0.0).lineTo(1.46875, 0.015460526315789473).lineTo(0.0, 0.015460526315789473).lineTo(0.0, 0.0).close()
solid4=wp_sketch4.add(loop4).extrude(0.296875)
solid=solid.union(solid4)
