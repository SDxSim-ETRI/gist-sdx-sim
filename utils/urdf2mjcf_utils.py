"""Defines utility functions."""

import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator, Optional, Tuple, Union
from xml.dom import minidom


def iter_meshes(
    urdf_path: Path,
    no_collision_mesh: bool = False,
) -> Iterator[
    Tuple[Union[Tuple[ET.Element, Path], Tuple[None, None]], Union[Tuple[ET.Element, Path], Tuple[None, None]]]
]:
    urdf_tree = ET.parse(urdf_path)

    def get_mesh(visual_or_collision: Optional[ET.Element]) -> Union[Tuple[ET.Element, Path], Tuple[None, None]]:
        if visual_or_collision is None:
            return (None, None)
        if (geometry := visual_or_collision.find("geometry")) is None:
            return (None, None)
        if (mesh := geometry.find("mesh")) is None:
            return (None, None)
        return mesh, (urdf_path.parent / mesh.attrib["filename"]).resolve()

    for link in urdf_tree.iter("link"):
        visual_link = link.find("visual")
        collision_link = link.find("collision")

        if no_collision_mesh:
            if collision_link is not None:
                raise ValueError("Collision links should not exist.")
            visual_mesh = get_mesh(visual_link)
            yield visual_mesh, (None, None)

        else:
            if visual_link is None or collision_link is None:
                if visual_link is not None or collision_link is not None:
                    raise ValueError("Visual and collision links must be present together.")
                continue
            visual_mesh = get_mesh(visual_link)
            collision_mesh = get_mesh(collision_link)

            if visual_mesh is None or collision_mesh is None:
                if visual_mesh is not None or collision_mesh is not None:
                    raise ValueError("Visual and collision meshes must be present together.")
                continue

            yield visual_mesh, collision_mesh


def save_xml(path: Union[str, Path, io.StringIO], tree: Union[ET.ElementTree, ET.Element]) -> None:
    if isinstance(tree, ET.ElementTree):
        tree = tree.getroot()
    xmlstr = minidom.parseString(ET.tostring(tree)).toprettyxml(indent="  ")
    xmlstr = re.sub(r"\n\s*\n", "\n", xmlstr)

    # Add newlines between second-level nodes
    root = ET.fromstring(xmlstr)
    for child in root[:-1]:
        child.tail = "\n\n  "
    xmlstr = ET.tostring(root, encoding="unicode")

    if isinstance(path, io.StringIO):
        path.write(xmlstr)
    else:
        with open(path, "w") as f:
            f.write(xmlstr)