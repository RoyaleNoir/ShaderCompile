"""updateshaders.pl"""
# TODO: Make pythonic
import re

from .shader_type import DX9Shader
from .shader_type import LegacyPixelShader
from .shader_type import LegacyVertexShader


def _get_shader_type(name):
    if ".fxc" in name:
        return "fxc"
    elif ".vsh" in name:
        return "vsh"
    elif ".psh" in name:
        return "psh"
    else:
        return ""


def _get_shader_base(name):
    return name.replace("." + _get_shader_type(name), "")


def _load_shader_list(project_name, force30):
    shader_list = []
    with open(project_name + ".txt") as shader_list_file:
        for line in shader_list_file:
            clean_line = re.sub(r"//.*$", "", line).strip().lower()
            if any(ext in clean_line for ext in ['.fxc', '.vsh', '.psh']):
                shader_base = _get_shader_base(clean_line)
                shader_type = _get_shader_type(clean_line)
                if force30:
                    shader_base = shader_base.replace("_ps2x", "_ps30")
                    shader_base = shader_base.replace("_ps20b", "_ps30")
                    shader_base = shader_base.replace("_ps20", "_ps30")
                    shader_base = shader_base.replace("_vs20", "_vs30")
                    shader_base = shader_base.replace("_vsxx", "_vs30")
                    shader_list.append({
                        'file': clean_line,
                        'name': shader_base,
                        'type': shader_type
                    })
                else:
                    if "_ps2x" in clean_line:
                        shader_list.append({
                            'file': clean_line,
                            'name': shader_base.replace("_ps2x", "_ps20"),
                            'type': shader_type
                        })
                        shader_list.append({
                            'file': clean_line,
                            'name': shader_base.replace("_ps2x", "_ps20b"),
                            'type': shader_type
                        })
                    elif "_vsxx" in clean_line:
                        shader_list.append({
                            'file': clean_line,
                            'name': shader_base.replace("_vsxx", "_vs11"),
                            'type': shader_type
                        })
                        shader_list.append({
                            'file': clean_line,
                            'name': shader_base.replace("_vsxx", "_vs20"),
                            'type': shader_type
                        })
                    else:
                        shader_list.append({
                            'file': clean_line,
                            'name': shader_base,
                            'type': shader_type
                        })

    return shader_list


def update_shaders(project_name, source, force30=False, dynamic=False):
    name_list = _load_shader_list(project_name, force30)
    shader_list = []
    for shader in name_list:
        if shader['type'] == 'fxc':
            shader_list.append(DX9Shader(shader['file'], shader['name'], not dynamic))
        elif shader['type'] == 'vsh':
            shader_list.append(LegacyVertexShader(shader['file'], shader['name']))
        else:
            shader_list.append(LegacyPixelShader(shader['file'], shader['name']))

    return shader_list
