# tiled2hva
# A CLI tool to convert Tiled .tmx files to Godot .tscn for High Velocity Arena 

# Copyright (c) 2023 Caleb North

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sellcccccc
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

###############
### IMPORTS ###
###############
import xml.etree.ElementTree as element_tree
import argparse
import colorama

from os.path import join, split, normpath, exists, abspath
from os import makedirs, listdir, remove
from sys import exit

from shutil import copy
from termcolor import cprint

###############
### TILEMAP ###
###############
class Tilemap:

    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.file_name = split(self.filepath)[1]

        # Check if file exists
        if not self._valid:
            throw("Tileset file cannot be found")
        # Check filetype
        if not self.filepath.endswith('.tmx'):
            throw("Tileset file must be .tmx format")
            
        # Parse filepath
        self.filepath = split(self.filepath)

        # Load file
        self.tree = element_tree.parse(filepath)
        self.root = self.tree.getroot()
        self.root_attrib = self.root.attrib
        
        # Trim out editor settings
        if self.root[0].tag == "editorsettings":
            self.root = self.root[1:]

        # Grab tile size
        self.tile_size = ( int(self.root_attrib["tilewidth"]), int(self.root_attrib["tileheight"]) )

        # Grab properties
        self.name = None
        self.mode = None

        if self.root[0].tag == "properties":
            properties = [property.attrib for property in self.root[0]]
            for property in properties:
                match property.get("name"):
                    case "hva:name":
                        self.name = property["value"]
                    case "hva:mode":
                        self.mode = property["value"]
                    case _:
                        pass

        if self.name == None:
            throw(f"Property hva:name not provided in Tilemap \"{self.filepath[1]}\"")

        if self.mode == None:
            throw(f"Property hva:mode not provided in Tilemap \"{self.filepath[1]}\"")

        tag_index = 1

        # Grab tilesets
        self.tileset_list = {}
        while self.root[tag_index].tag == "tileset": 
            tilemap_set = self.root[tag_index]

            # Create Tileset
            try:
                tileset = Tileset(join(self.filepath[0], tilemap_set.attrib["source"]))
            
            except FileNotFoundError as error:
                throw(f"Tileset file \"{split(error.args[0])[1]}\" in Tilemap \"{self.file_name}\" cannot be found")

            except FileTypeError as error:
                throw(f"Tileset file \"{split(error.args[0])[1]}\" in Tilemap \"{self.file_name}\" must be .tsx format")
                
            tileset_data = (tileset, int(tilemap_set.attrib["firstgid"]))
            self.tileset_list[tag_index] = tileset_data

            tag_index += 1

        # Grab layers
        self.layers = []
        while tag_index < len(self.root) and self.root[tag_index].tag == "layer":
            layer = self.root[tag_index]

            # Convert each tile to an int
            layer_data = []

            # Strip out all unnecessary tags
            while layer[0].tag != "data":
                layer[0:] = layer[1:]

            if layer[0].attrib.get("encoding") != "csv":
                throw("Tilemaps must be encoded in csv format!")

            # For each row in the layer
            for row in layer[0].text.strip().split("\n"):
                row_data = []
                # For each tile in the layer
                for tile in row.split(","):
                    try:
                        tile = int(tile)
                    except:
                        continue

                    # Convert to byte
                    tile_byte = (32 - len( f"{tile:b}" )) * "0" + f"{tile:b}"

                    # Extract rotation flag
                    tiled_to_godot_flags = {"000":"000", "101":"-011", "110":"011", "011":"-010", "100":"001", "111":"-001", "010":"010", "001":"-100"}
                    rotation_value = int( tiled_to_godot_flags[tile_byte[0:3]] + "0" * 29, 2 )

                    # Extract tile value
                    tile_value = int( tile_byte[3:], 2)

                    # For each tileset in the layer
                    for tileset_id, tileset in self.tileset_list.items():
                        # Grab global starting tile ID
                        first_gid = sum([self.tileset_list[set_id][0].tile_count for set_id in self.tileset_list if set_id < tileset_id])

                        # Check if tile is in id range
                        if tile_value in range( tileset[1], tileset[1] + tileset[0].tile_count ):
                            # Tile ID, offset by global starting ID, offset by original tileset tile ID
                            global_tile = rotation_value + 1 + tile_value + first_gid - tileset[1]
                            break
                        else:
                            # Blank tile / tile not included in the set
                            global_tile = 0

                    row_data.append(global_tile)
                layer_data.append(row_data)

            self.layers.append((layer.attrib['name'], layer_data))

            tag_index += 1
    
    def _generate(self) -> tuple:
        # Generate tres first
        tres = Tileset._generate_tres([tileset[0] for tileset in self.tileset_list.values()])

        # Generate tscn
        tscn = "[gd_scene load_steps=2 format=2]\n\n"

        # Save image path
        tscn += f'[ext_resource path="{self.mode.lower() + "_" + self.name.lower()+".tres"}" type="TileSet" id=1]\n\n'

        # Create parent node
        tscn += f'[node name="{self.mode + "_" + self.name.lower()}" type="Node2D"]\nscale = Vector2( 0.25, 0.25 )\n\n'

        # Write each layer
        for layer in self.layers:
            tscn += f'[node name="{layer[0]}" type="TileMap" parent="."]\ntile_set = ExtResource( 1 )\n'
            tscn += f'cell_size = Vector2( {self.tile_size[0]}, {self.tile_size[1]} )\ncell_custom_transform = Transform2D( 16, 0, 0, 16, 0, 0 )\nformat = 1\ntile_data = PoolIntArray('
            flat_layer = []
            
            # Flatten layer array
            row_id = 0
            while row_id < len(layer[1]):
                row = layer[1][row_id]
                tile_id = 0
                while tile_id < len(row):
                    tile = row[tile_id]
                    if tile != 0:
                        flat_layer.append(f"{ tile_id + (row_id * 65536) }, {tile}, 0")
                    
                    tile_id += 1
                row_id += 1
            
            # Write to tres
            tscn += ", ".join(flat_layer)+")"
                    

        #print(tscn)

        # Write tscn
        return tscn, tres, [self.tileset_list[set][0].full_image_path for set in self.tileset_list]

    @property
    def _valid(self) -> bool:
        return exists(self.filepath)

###############
### TILESET ###
###############
class Tileset:

    def __init__(self, filepath:str) -> None:
        self.filepath = filepath

        # Check if file exists
        if not self._valid:
            raise FileNotFoundError(filepath)

        # Check filetype
        if not self.filepath.endswith('.tsx'):
            raise FileTypeError(filepath)

        # Load file
        self.tree = element_tree.parse(filepath)
        self.root = self.tree.getroot()
        self.root_attrib = self.root.attrib
        self.name = self.root_attrib["name"]

        # Trim out editor settings
        if self.root[0].tag == "editorsettings":
            self.root = self.root[1:]

        # Trim out grid? what is this even
        if self.root[0].tag == "grid":
            self.root[0:] = self.root[1:]

        # Grab tile size
        self.tile_size = ( int(self.root_attrib["tilewidth"]), int(self.root_attrib["tileheight"]) )
        
        # Grab columns
        self.columns = int(self.root_attrib["columns"])

        # Grab properties
        self.tile_count = None

        if self.root[0].tag == "properties":
            properties = [property.attrib for property in self.root[0]]
            for property in properties:
                match property.get("name"):
                    case "hva:tiles":
                        try:
                            self.tile_count = int(property["value"])
                        except ValueError:
                            throw(f"Property hva:tiles in Tileset \"{self.name}\" must be type int")
                    case _:
                        pass

        if self.tile_count == None:
            cprint(f"[/] Property hva:name not provided in Tileset \"{self.name}\", defaulting to Tiled value", "yellow")
            self.tile_count = int(self.root_attrib["tilecount"])
            
        self.root[0:] = self.root[1:]
                        

        # Grab image
        self.full_image_path = normpath(self.root[0].attrib["source"])
        self.image_path = normpath(split(self.root[0].attrib["source"])[1])

        self.root[0:] = self.root[1:]

        # Grab shapes
        self.shapes = []
        self.object_id = 0
        for tile in self.root[0:]:
            # TODO deal with concave objects
            if tile[0].tag != "objectgroup":
                continue

            for object in tile[0]:
                points = []
                self.object_id += 1

                # Check if square or not
                if "width" in object.attrib:
                    x = object.attrib["x"]
                    y = object.attrib["y"]
                    width = object.attrib["width"]
                    height = object.attrib["height"]
                    points = [ (x, y), (x, width), (height, width), (height, y) ]
                    self.shapes.append((
                        int(tile.attrib["id"]), self.object_id, points
                    ))

                elif len(object) > 0:
                    # Grab point
                    for point in object[0].attrib["points"].split(" "):
                        x = max(0, min(int(point.split(",")[0]) + int(object.attrib["x"]), self.tile_size[0]))
                        y = max(0, min(int(point.split(",")[1]) + int(object.attrib["y"]), self.tile_size[1]))
                        points.append((x, y))
                    self.shapes.append((
                        int(tile.attrib["id"]), self.object_id, points
                    ))

    @property
    def _valid(self) -> bool:
        return exists(self.filepath)
    
    @staticmethod
    def _generate_tres(sets) -> str:
        tres = ""

        tile_objects = {}
        ext_resource_id = 0
        sub_resource_id = 0

        for set_id in range(0, len(sets)):
            set = sets[set_id]
            # Check passed object type
            if type(set) != Tileset:
                raise TypeError("Cannot pass anything other than a Tileset")

            # Add set image to tres
            ext_resource_id += 1
            tres += f"[ext_resource path=\"{set.image_path}\" type=\"Texture\" id={ext_resource_id}]\n\n"

            # Object collision step
            for shapes in set.shapes:
                sub_resource_id += 1
                points_list = []

                for points in shapes[2]:
                    points_list.append(str(points[0]))
                    points_list.append(str(points[1]))
                tres += f"[sub_resource type=\"ConvexPolygonShape2D\" id={sub_resource_id}]\n"
                tres += f"points = PoolVector2Array( { ', '.join(points_list) } )\n\n"
                
                if tile_objects.get(shapes[0]) != None:
                    tile_objects[(set_id, shapes[0])].append(sub_resource_id)
                else:
                    tile_objects[(set_id, shapes[0])] = [sub_resource_id]

        # Tile step
        total_tiles = 0
        tres += "[resource]\n"
        for set_id in range(0, len(sets)):
            set = sets[set_id]
            for set_tile_id in range(0, set.tile_count+1):
                tile_id = total_tiles + 1

                # Grab tile region
                tile_width = set.tile_size[0]
                tile_height = set.tile_size[1]
                x = (set_tile_id) % set.columns
                y = (set_tile_id) // set.columns

                # Check if tile has collision
                tile_object_key = (set_id, set_tile_id)
                has_collision = False
                tile_shapes = ""
                if tile_objects.get(tile_object_key) != None:
                    has_collision = True
                    for shape in tile_objects.get(tile_object_key):
                        tile_shapes += "{\n"+\
                            '"autotile_coord": Vector2( 0, 0 ),\n'+\
                            '"one_way": false,\n'+\
                            '"one_way_margin": 1.0,\n'+\
                           f'"shape":SubResource( {shape} ),\n'+\
                            '"shape_transform": Transform2D( 1, 0, 0, 1, 0, 0 )}, \n'
                s = f"{tile_id}/"
                tres += \
                    f"{s}name = \"{tile_id}\"\n"+\
                    f"{s}texture = ExtResource( {set_id + 1} )\n"+\
                    f"{s}tex_offset = Vector2( 0, 0 )\n"+\
                    f"{s}modulate = Color( 1, 1, 1, 1 )\n"+\
                    f"{s}region = Rect2( {x * tile_width}, {y * tile_height}, {tile_width}, {tile_height})\n"+\
                    f"{s}tile_mode = 0\n"+\
                    f"{s}occluder_offset = Vector2( 0, 0 )\n"+\
                    f"{s}navigation_offset = Vector2( 0, 0)\n"+\
                    f"{s}shape_offset = Vector2( 0, 0 )\n"+\
                    f"{s}shape_transform = Transform2D( 1, 0, 0, 1, 0, 0 )\n"+\
                    (f"{s}shape = SubResource( {tile_objects[tile_object_key][0]} )\n" if has_collision else "")+\
                    f"{s}shape_one_way = false\n"+\
                    f"{s}shape_one_way_margin = 0.0\n"+\
                    f"{s}shapes = [ {tile_shapes} ]\n"+\
                    f"{s}z_index = 0\n"

                total_tiles += 1

        tres = f"[gd_resource type=\"TileSet\" load_steps={ext_resource_id+sub_resource_id+1} format=2]\n\n" + tres

        return tres

###########
### RUN ###
###########
def main():
    colorama.init()
    # Create argument parser
    parser = argparse.ArgumentParser(
        prog = "tiled2hva",
        description =  "Converts Tiled .tmx files to Godot .tscn for High Velocity Arena",
    )
    parser.add_argument('filepath', type=str)
    args = parser.parse_args()

    # Grab filepath
    tscn_filepath = abspath(normpath(args.filepath))

    # Create Tilemap
    tilemap = Tilemap(tscn_filepath)
    map = tilemap._generate()

    # Filepath / name combinations
    map_name = tilemap.mode + "_" + tilemap.name
    folder_path = split(tscn_filepath)[0]
    full_folder_path = join(folder_path, map_name)

    # Try to make folder at location
    if not exists(full_folder_path):
        makedirs(full_folder_path)
        cprint(f"[+] Created {map_name} folder at {folder_path}", "green")
    # Folder exists, try wiping
    else:
        cprint(f"[?] The destination subfolder /{map_name} already exists. Wipe all contents to proceed? (y/n)", "light_yellow", end="")
        response = input(" ") 
        if response != "y":
            throw()

        # Gut folder
        for file in listdir(full_folder_path):
            remove(join(full_folder_path, file))

    copied_files = 0
    # Move images
    for image in map[2]:
        copy(join(folder_path, image), full_folder_path)
        copied_files += 1

    # Write .tres
    with open(join(full_folder_path, f"{map_name}.tres"), "w") as file:
        file.write(map[1])

    with open(join(full_folder_path, f"{map_name}.tscn"), "w") as file:
        file.write(map[0])

    cprint(f"[+] Map {map_name} written to {full_folder_path}", "green")


##############
### ERRORS ###
##############
class FileTypeError(Exception):
    "Raised when file type differs from expected"
    pass

###############
### LOGGING ###
###############
def log(msg):
    print(msg)

############
### KILL ###
############
def throw(msg:str=None) -> None:
    if msg == None:
        cprint("[-] Process killed", "red")
    else:
        cprint(f"[-] {msg}", "red")
    exit(1)

###########
### RUN ###
###########
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        throw()
    exit(0)