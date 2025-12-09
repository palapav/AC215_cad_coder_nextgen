import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.171875, -0.75, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.3315789473684211, 0.0).lineTo(0.3315789473684211, 1.5).lineTo(0.0, 1.5).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.26842105263157895, 0.06315789473684211).lineTo(0.26842105263157895, 1.436842105263158).lineTo(0.06315789473684211, 1.436842105263158).lineTo(0.06315789473684211, 0.06315789473684211).close()
solid0=wp_sketch0.add(loop0).add(loop1).extrude(0.0390625)
solid=solid0
