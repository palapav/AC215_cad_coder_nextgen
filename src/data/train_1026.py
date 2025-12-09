import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.4609375, 0.0, -0.234375), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.45, 0.0).lineTo(0.45, 0.5684210526315789).lineTo(0.5210526315789474, 0.5684210526315789).lineTo(0.5210526315789474, 0.0).lineTo(0.75, 0.2210526315789474).lineTo(0.6710526315789473, 0.2210526315789474).lineTo(0.6710526315789473, 0.45).lineTo(0.75, 0.45).lineTo(0.75, 0.75).lineTo(0.0, 0.75).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.15, 0.6).circle(0.1105263157894737)
loop2=wp_sketch0.moveTo(0.15, 0.15).circle(0.07894736842105263)
loop3=wp_sketch0.moveTo(0.3, 0.37894736842105264).circle(0.1105263157894737)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).add(loop3).extrude(0.75)
solid=solid0
