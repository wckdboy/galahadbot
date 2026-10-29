"""Galahad material library.

Palette taken from the six reference views: warm ivory printed shells, midnight
navy service plates, graphite DYNAMIXEL housings, brushed brass fittings and
near-black silicone treads.
"""
import bpy


def _srgb(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgba(hex_string, alpha=1.0):
    h = hex_string.lstrip("#")
    return tuple(_srgb(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + (alpha,)


def material(name, color, metallic=0.0, roughness=0.5, emission=None,
             emission_strength=0.0, coat=0.0, subsurface=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    elif "Clearcoat" in bsdf.inputs:
        bsdf.inputs["Clearcoat"].default_value = coat
    if subsurface and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if emission:
        bsdf.inputs["Emission Color"].default_value = rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = rgba(color)
    return mat


def build_library():
    """Create (or refresh) every Galahad material and return them by key."""
    mats = {}
    mats["ivory"] = material("GLD_Ivory", "#EDE4D1", roughness=0.46, coat=0.12)
    mats["ivory_warm"] = material("GLD_IvoryWarm", "#E4D8C0", roughness=0.55)
    mats["navy"] = material("GLD_Navy", "#2A3346", roughness=0.42, coat=0.15)
    mats["navy_dark"] = material("GLD_NavyDeep", "#1D2433", roughness=0.45)
    mats["graphite"] = material("GLD_Graphite", "#22252B", roughness=0.38)
    mats["rubber"] = material("GLD_TreadRubber", "#141518", roughness=0.82)
    mats["brass"] = material("GLD_Brass", "#C9A050", metallic=1.0, roughness=0.26)
    mats["brass_dark"] = material("GLD_BrassAged", "#9A7A3A", metallic=1.0, roughness=0.38)
    mats["steel"] = material("GLD_Steel", "#8E949C", metallic=1.0, roughness=0.32)
    mats["pcb"] = material("GLD_PCB", "#2E6B45", roughness=0.5)
    mats["pcb_dark"] = material("GLD_PCBDark", "#1F4A31", roughness=0.55)
    mats["orange"] = material("GLD_LatchOrange", "#D96A17", roughness=0.5)
    mats["glass"] = material("GLD_LensGlass", "#0B0E14", roughness=0.08, coat=0.6)
    mats["led"] = material("GLD_LEDBlue", "#2E7BFF", emission="#2E7BFF", emission_strength=12.0,
                           roughness=0.3)
    mats["screen"] = material("GLD_Screen", "#0A1424", roughness=0.15, coat=0.4,
                              emission="#1E4FA8", emission_strength=1.2)
    mats["wire_red"] = material("GLD_WireRed", "#B4322A", roughness=0.6)
    mats["wire_yellow"] = material("GLD_WireYellow", "#C9A227", roughness=0.6)
    mats["wire_black"] = material("GLD_WireBlack", "#17181B", roughness=0.65)
    mats["floor"] = material("GLD_Floor", "#8E9195", roughness=0.75)
    return mats
