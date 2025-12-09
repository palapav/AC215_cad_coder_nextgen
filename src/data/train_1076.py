import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.75).lineTo(0.0, 0.75).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.1953125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.171875, 0.640625, 0.0), cq.Vector(0.9993977281025862, 0.024541228522912326, 0.024533837163709046), cq.Vector(0.024541228522912326, 0.0, -0.9996988186962042)))
loop1=wp_sketch1.moveTo(0.055263157894736833, 0.0).circle(0.055263157894736833)
solid1=wp_sketch1.add(loop1).extrude(-0.359375)
solid=solid.cut(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.1796875, 0.328125, 0.0), cq.Vector(0.9993977281025862, 0.024541228522912326, 0.024533837163709046), cq.Vector(0.024541228522912326, 0.0, -0.9996988186962042)))
loop2=wp_sketch2.moveTo(0.08289473684210526, 0.0).circle(0.08116776315789473)
solid2=wp_sketch2.add(loop2).extrude(-0.359375)
solid=solid.cut(solid2)
# Generating a workplane for sketch 3
wp_sketch3 = cq.Workplane(cq.Plane(cq.Vector(-0.515625, 0.6484375, 0.0), cq.Vector(0.9993977281025862, 0.024541228522912326, 0.024533837163709046), cq.Vector(0.024541228522912326, 0.0, -0.9996988186962042)))
loop3=wp_sketch3.moveTo(0.1328125, 0.0).lineTo(0.1328125, 0.07689144736842106).lineTo(0.0, 0.07689144736842106).lineTo(0.0, 0.0).close()
solid3=wp_sketch3.add(loop3).extrude(-0.359375)
solid=solid.cut(solid3)
