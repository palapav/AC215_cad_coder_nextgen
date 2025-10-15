import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.375, -0.375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.75, 0.0).lineTo(0.75, 0.75).lineTo(0.0, 0.75).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.37894736842105264, 0.37894736842105264).circle(0.13421052631578947)
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.75)
solid=solid0
