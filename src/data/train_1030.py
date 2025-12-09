import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
loop0=wp_sketch0.moveTo(0.7578947368421053, 0.0).circle(0.7578947368421053)
loop1=wp_sketch0.moveTo(0.15789473684210525, 0.0).circle(0.06315789473684211)
loop2=wp_sketch0.moveTo(0.7578947368421053, 0.0).circle(0.4421052631578948)
loop3=wp_sketch0.moveTo(0.7578947368421053, -0.5842105263157895).circle(0.06315789473684211)
loop4=wp_sketch0.moveTo(0.7578947368421053, 0.5842105263157895).circle(0.06315789473684211)
loop5=wp_sketch0.moveTo(1.3421052631578947, 0.0).circle(0.06315789473684211)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).add(loop3).add(loop4).add(loop5).extrude(0.25)
solid=solid0
