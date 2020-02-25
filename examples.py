
RGTerminals = "0 1"
RGStartSymbol = "A"
RGNonTerminals = "B C"
RGAliases = """zero 0 0
one 1 1"""
RGProductions = """A %= zero + B | one
B %= zero + A | one + C
C %= one
"""

AritmethicTerminals = "num - + * / ( )  "
AritmethicStartSymbol = "E"
AritmethicNonTerminalsLR = "T F"
AritmethicAliases = """plus + [+]
minus - [-]
star * [*]
div / [/]
opar ( [(]
cpar ) [)]
num num -?[1-9][0-9]*"""
AritmethicProductionsLR = """E %= E + plus + T | E + minus + T | T 
T %= T + star + F | T + div + F | F
F %= num | opar + E + cpar"""

AritmethicNonTerminalsLL = "T F X Y"
AritmethicProductionsLL = """E %= T + X
X %= plus + T + X | minus + T + X | G.Epsilon
T %= F + Y
Y %= star + F + | div + F + Y | G.Epsilon
F %= num | opar + E + cpar"""

EqualityTerminals = "num + ="
EqualityStartSymbol = "E"
EqualityNonTerminalsLR = "A"
EqualityAliases = """num num -?[1-9][0-9]*
equal = =
plus + [+]"""
EqualityProductions = """E %=  A + equal + A | num
A %= num + plus + A | num"""
