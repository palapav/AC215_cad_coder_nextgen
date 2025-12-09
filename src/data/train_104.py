import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(0.0078125, 0.0, -0.09375), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.5390625, 0.046875).lineTo(0.6953125, 0.046875).threePointArc((0.7284581303681195, 0.06060436963188054), (0.7421875, 0.09375)).threePointArc((0.7284581303681195, 0.12689563036811946), (0.6953125, 0.140625)).lineTo(0.5390625, 0.140625).lineTo(0.0, 0.1875).threePointArc((-0.10217023932807223, 0.09375), (0.0, 0.0)).close()
loop1=wp_sketch0.moveTo(-0.0078125, 0.09375).circle(0.03125)
loop2=wp_sketch0.moveTo(0.65625, 0.09375).circle(0.015625)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).extrude(0.046875)
solid=solid0
