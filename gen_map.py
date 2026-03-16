import os

width = 200
height = 40

background_csv = []
for y in range(height):
    row = []
    for x in range(width):
        row.append('12' if (x+y)%3==0 else '11')
    background_csv.append(','.join(row) + ',')

walls_csv = []
for y in range(height):
    row = []
    for x in range(width):
        if y >= 36:
            row.append('24') # Ground lowered to give more screen
        elif y == 31 and 20 <= x <= 25:
            row.append('24') # Platform 1
        elif y == 27 and 30 <= x <= 35:
            row.append('24') # Platform 2
        elif y >= 34 and x == 60:
            row.append('24') # Small Obstacle
        else:
            row.append('0')
    walls_csv.append(','.join(row) + ',')

bg_data = chr(10).join(background_csv)[:-1]
walls_data = chr(10).join(walls_csv)[:-1]

map_xml = f'''<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<map version=\"1.10\" tiledversion=\"1.11.2\" orientation=\"orthogonal\" renderorder=\"right-down\" width=\"{width}\" height=\"{height}\" tilewidth=\"16\" tileheight=\"16\" infinite=\"0\" nextlayerid=\"4\" nextobjectid=\"2\">
 <tileset firstgid=\"1\" name=\"Swampset\" tilewidth=\"16\" tileheight=\"16\" tilecount=\"25\" columns=\"5\">
  <image source=\"Swampset.png\" width=\"80\" height=\"80\"/>
  <tile id=\"0\">
   <properties>
    <property name=\"solid\" type=\"bool\" value=\"true\"/>
    <property name=\"collidable\" type=\"bool\" value=\"true\"/>
   </properties>
  </tile>
  <tile id=\"1\">
   <properties>
    <property name=\"solid\" type=\"bool\" value=\"true\"/>
    <property name=\"collidable\" type=\"bool\" value=\"true\"/>
   </properties>
  </tile>
  <tile id=\"2\">
   <properties>
    <property name=\"solid\" type=\"bool\" value=\"true\"/>
    <property name=\"collidable\" type=\"bool\" value=\"true\"/>
   </properties>
  </tile>
  <tile id=\"3\">
   <properties>
    <property name=\"solid\" type=\"bool\" value=\"true\"/>
    <property name=\"collidable\" type=\"bool\" value=\"true\"/>
   </properties>
  </tile>
  <tile id=\"4\">
   <properties>
    <property name=\"solid\" type=\"bool\" value=\"true\"/>
    <property name=\"collidable\" type=\"bool\" value=\"true\"/>
   </properties>
  </tile>
  <tile id=\"23\">
   <properties>
    <property name=\"solid\" type=\"bool\" value=\"true\"/>
    <property name=\"collidable\" type=\"bool\" value=\"true\"/>
   </properties>
  </tile>
 </tileset>
 <layer id=\"1\" name=\"background\" width=\"{width}\" height=\"{height}\">
  <data encoding=\"csv\">
{bg_data}
  </data>
 </layer>
 <layer id=\"2\" name=\"walls\" width=\"{width}\" height=\"{height}\">
  <data encoding=\"csv\">
{walls_data}
  </data>
 </layer>
 <objectgroup id=\"3\" name=\"objects\">
  <object id=\"1\" name=\"boss_trigger\" x=\"2400\" y=\"160\" width=\"32\" height=\"320\"/>
 </objectgroup>
</map>
'''

with open('assets/map.tmx', 'w', encoding='utf-8') as f:
    f.write(map_xml)
