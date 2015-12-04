from seqdiag import parser, builder, drawer

diagram_definition = open('diagram_definition.seqdiag', 'r').read()
tree = parser.parse_string(diagram_definition)
diagram = builder.ScreenNodeBuilder.build(tree)
draw = drawer.DiagramDraw('PNG', diagram, filename="diagram.png")
draw.draw()
draw.save()
