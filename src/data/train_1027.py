import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, -0.140625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(1.390625, 0.0).lineTo(1.390625, 0.16101973684210527).lineTo(1.1564144736842106, 0.16101973684210527).threePointArc((1.0736085479926283, 0.19531907430841763), (1.0393092105263158, 0.278125)).lineTo(1.0393092105263158, 0.5269736842105264).lineTo(0.35131578947368425, 0.5269736842105264).lineTo(0.35131578947368425, 0.278125).threePointArc((0.3170164520073719, 0.19531907430841763), (0.23421052631578948, 0.16101973684210527)).lineTo(0.0, 0.16101973684210527).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.6953125)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(0.4765625, -0.3515625, 0.0234375), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop1=wp_sketch1.moveTo(0.04736842105263158, 0.0).circle(0.04736842105263158)
solid1=wp_sketch1.add(loop1).extrude(-0.234375)
solid=solid.cut(solid1)
