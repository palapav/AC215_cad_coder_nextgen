import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.734375, -0.28125, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.9894736842105263, 0.0).lineTo(0.9894736842105263, -0.24736842105263157).lineTo(1.46875, -0.24736842105263157).lineTo(1.46875, 0.5565789473684211).lineTo(0.47927631578947366, 0.5565789473684211).lineTo(0.47927631578947366, 0.8039473684210526).lineTo(0.0, 0.8039473684210526).lineTo(0.0, 0.0).close()
solid0=wp_sketch0.add(loop0).extrude(0.75)
solid=solid0
