import cadquery as cq
# Generating a workplane for sketch 0
wp_sketch0 = cq.Workplane(cq.Plane(cq.Vector(-0.4296875, 0.0, -0.453125), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop0=wp_sketch0.moveTo(0.856578947368421, 0.0).lineTo(0.856578947368421, 0.8749999999999999).lineTo(0.0, 0.8749999999999999).lineTo(0.0, 0.0).close()
loop1=wp_sketch0.moveTo(0.12894736842105262, 0.14736842105263157).circle(0.055263157894736833)
loop2=wp_sketch0.moveTo(0.12894736842105262, 0.7460526315789473).circle(0.055263157894736833)
loop3=wp_sketch0.moveTo(0.4236842105263158, 0.45131578947368417).circle(0.2763157894736842)
loop4=wp_sketch0.moveTo(0.7276315789473684, 0.14736842105263157).circle(0.055263157894736833)
loop5=wp_sketch0.moveTo(0.7276315789473684, 0.7460526315789473).circle(0.055263157894736833)
solid0=wp_sketch0.add(loop0).add(loop1).add(loop2).add(loop3).add(loop4).add(loop5).extrude(0.4296875)
solid=solid0
# Generating a workplane for sketch 1
wp_sketch1 = cq.Workplane(cq.Plane(cq.Vector(-0.75, 0.0, -0.6640625), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop6=wp_sketch1.moveTo(1.5, 0.0).lineTo(1.5, 0.2210526315789474).lineTo(1.1842105263157896, 0.2210526315789474).lineTo(0.3157894736842105, 0.2210526315789474).lineTo(0.0, 0.2210526315789474).lineTo(0.0, 0.0).close()
solid1=wp_sketch1.add(loop6).extrude(0.4296875)
solid=solid.union(solid1)
# Generating a workplane for sketch 2
wp_sketch2 = cq.Workplane(cq.Plane(cq.Vector(-0.3203125, -0.4296875, 0.0), cq.Vector(1.0, 6.123233995736766e-17, -6.123233995736766e-17), cq.Vector(6.123233995736766e-17, -1.0, 6.123233995736766e-17)))
loop7=wp_sketch2.moveTo(0.3236842105263158, 0.0).circle(0.3236842105263158)
loop8=wp_sketch2.moveTo(0.3236842105263158, 0.0).circle(0.27648026315789476)
solid2=wp_sketch2.add(loop7).add(loop8).extrude(-0.296875)
solid=solid.cut(solid2)
