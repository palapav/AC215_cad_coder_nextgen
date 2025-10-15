import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0, -0.75, -0.75), cq.Vector(3.749399456654644e-33, 1.0, -6.123233995736766e-17), cq.Vector(1.0, 0.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(1.5, 0.0).lineTo(1.5, 1.5).lineTo(0.0, 1.5).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.7578947368421053, 0.5368421052631579).circle(0.14210526315789473)
loop2=wp_sketch0.moveTo(0.7578947368421053, 0.9315789473684211).circle(0.14210526315789473)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).extrude(0.03125)
solid=solid0
