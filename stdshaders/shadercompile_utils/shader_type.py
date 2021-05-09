import os.path
import re

from . import fxc_file


class BaseShader:
    """
    The generic shader type, extended for .fxc, .vsh, and .psh shaders.
    """

    def __init__(self, file_name, shader_name, compile_vcs=True):
        """
        :param file_name: Source File name
        :param shader_name: Output shader name
        :param compile_vcs: Whether to actually compile shader
        """
        self.file_name = os.path.basename(file_name)
        self.file_path = os.path.dirname(file_name)
        if self.file_path != "":
            self.file_path += "/".replace("/", os.sep)
        self.shader_name = os.path.basename(shader_name)
        self.type = ""

        self.dependencies = []
        self.get_dependencies()

        self.static_combos = []
        self.dynamic_combos = []
        self.static_defs = {}
        self.skip_code = ""
        self.skips = []
        self.centroid_mask = 0

        self.inc_file = False
        self.compile_vcs = compile_vcs

    def __str__(self):
        return "{} ({})".format(self.shader_name, self.file_name)

    def _get_dependencies_r(self, path):
        with open(path) as source_file:
            for line in source_file:
                match = re.match(r"^\s*#include\s+\"(.*)\"", line)
                if match:
                    if match.group(1) not in self.dependencies:
                        dep_path = match.group(1)
                        if os.path.exists(self.file_path + dep_path):
                            dep_path = self.file_path + dep_path
                        self.dependencies.append(dep_path)
                        self._get_dependencies_r(dep_path)

    def get_dependencies(self):
        """Find all ``#include`` statements in the source file."""
        self._get_dependencies_r(self.file_path + self.file_name)
        pass

    def prep(self, dynamic):
        """Prepare the shader for compilation, and create ``.inc`` files if applicable"""
        pass


class DX9Shader(BaseShader):
    def __init__(self, file_name, shader_name, compile_vcs=True):
        super(DX9Shader, self).__init__(file_name, shader_name, compile_vcs)
        self.inc_file = True
        self.type = "fxc"

    def prep(self, dynamic):
        full_code = fxc_file.read_input_file(self.file_path + self.file_name)
        self.static_combos, self.dynamic_combos, self.static_defs = \
            fxc_file.find_combos(full_code, self.shader_name)
        self.skip_code, self.skips = fxc_file.find_skips(full_code)
        self.centroid_mask = fxc_file.find_centroids(full_code)
        if self.compile_vcs and not dynamic:
            fxc_file.dump_file_list(
                self.shader_name,
                self.file_name,
                self.static_combos,
                self.dynamic_combos,
                self.skip_code,
                self.centroid_mask
            )
        if self.inc_file:
            with open("include/{}.inc".format(self.shader_name), "w") as out_file:
                header_code = fxc_file.write_static_classes(
                    self.shader_name,
                    self.static_combos,
                    self.static_defs,
                    self.dynamic_combos,
                    self.skips
                ) + "\n\n"
                header_code += fxc_file.write_dynamic_classes(
                    self.shader_name,
                    self.dynamic_combos,
                    self.skips
                )
                out_file.write(header_code)


class LegacyVertexShader(BaseShader):
    def __init__(self, file_name, shader_name, compile_vcs=True):
        super(LegacyVertexShader, self).__init__(file_name, shader_name, compile_vcs)
        self.inc_file = True
        self.type = "vsh"


class LegacyPixelShader(BaseShader):
    def __init__(self, file_name, shader_name, compile_vcs=True):
        super(LegacyPixelShader, self).__init__(file_name, shader_name, compile_vcs)
        self.inc_file = False
        self.type = "psh"
