import re


def read_input_file(file_name):
    out_lines = []
    with open(file_name) as source_file:
        for line in source_file:
            match = re.match(r"^\s*#include\s+\"(.*)\"", line)
            if match:
                out_lines.extend(read_input_file(match.group(1)))
            else:
                out_lines.append(line)
    return out_lines


def find_combos(source: [str], shader_name: str):
    static_combos = []
    dynamic_combos = []
    static_defs = {}
    for i, line in enumerate(source):
        if re.search(r"^\s*$", line):
            continue
        if "[XBOX]" in line:
            # print("Skipping XBOX combos.")
            source[i] = ""
            continue
        match = re.match(r".*_ps(\d+\w?)$", shader_name)
        if match and re.match(r".*\[ps\d+\w?]", line.lower()) and not "[ps{}]".format(match.group(1)) in line.lower():
            # print("Skipping combos for wrong PS Version.")
            source[i] = ""
            continue
        match = re.match(r".*_vs(\d+\w?)$", shader_name)
        if match and re.match(r".*\[vs\d+\w?]", line.lower()) and not "[vs{}]".format(match.group(1)) in line.lower():
            # print("Skipping combos for wrong VS Version.")
            source[i] = ""
            continue
        match = re.match(r".*\[=([^]]+)]", line.lower())
        initial_value = ""
        if match:
            initial_value = match.group(1)

        source[i] = line = re.sub(r"\[[^\[\]]*]", "", line)

        match = re.match(r"^\s*//\s*STATIC\s*:\s*\"(.*)\"\s+\"(\d+)\.\.(\d+)\"", line)
        if match:
            static_combos.append({
                'name': match.group(1),
                'min': match.group(2),
                'max': match.group(3)
            })
            static_defs[match.group(1)] = initial_value

        match = re.match(r"^\s*//\s*DYNAMIC\s*:\s*\"(.*)\"\s+\"(\d+)\.\.(\d+)\"", line)
        if match:
            dynamic_combos.append({
                'name': match.group(1),
                'min': match.group(2),
                'max': match.group(3)
            })
    return static_combos, dynamic_combos, static_defs


def find_skips(source: [str]):
    skip_code = ""
    skips = []
    for line in source:
        match = re.match(r"^\s*//\s*SKIP\s*:\s*(.*)$", line)
        if match:
            skip_code += "(" + match.group(1).strip() + ")||"
            skips.append(match.group(1).strip())
    skip_code += "0"
    return skip_code, skips


def find_centroids(source: [str]):
    centroid_mask = 0
    for line in source:
        match = re.match(r"^\s*//\s*CENTROID\s*:\s*TEXCOORD(\d+)$", line)
        if match:
            centroid_mask += 1 << int(match.group(1))
    return centroid_mask


def _write_variable_func_int(name, min_val, max_val):
    var_name = "m_n" + name
    bool_name = "m_b" + name
    out_string = "\tvoid Set" + name + "( int i )\n\t{\n"
    out_string += "\t\tAssert( i >= " + min_val + " && i <= " + max_val + " );\n"
    out_string += "\t\t" + var_name + " = i;\n"
    out_string += "#ifdef _DEBUG\n"
    out_string += "\t\t" + bool_name + " = true;\n"
    out_string += "#endif\t// _DEBUG\n"
    out_string += "\t}\n\n"
    out_string += "\tvoid Set" + name + "( bool i )\n\t{\n"
    out_string += "\t\t" + var_name + " = i ? 1 : 0;\n"
    out_string += "#ifdef _DEBUG\n"
    out_string += "\t\t" + bool_name + " = true;\n"
    out_string += "#endif\t// _DEBUG\n"
    out_string += "\t}\n\n"
    return out_string


def get_shader_type(shader_name):
    if "ps30" in shader_name:
        return "ps_3_0"
    elif "ps2b" in shader_name:
        return "ps_2_b"
    elif "ps20" in shader_name:
        return "ps_2_0"
    elif "ps14" in shader_name:
        return "ps_1_4"
    elif "ps11" in shader_name:
        return "ps_1_1"
    elif "vs30" in shader_name:
        return "vs_3_0"
    elif "vs2b" in shader_name:
        return "vs_2_b"
    elif "vs20" in shader_name:
        return "vs_2_0"
    elif "vs14" in shader_name:
        return "vs_1_1"
    elif "vs11" in shader_name:
        return "vs_1_1"
    else:
        print("Invalid Shader Suffix: " + shader_name)
        exit(1)


def write_static_classes(shader_name, static_combos, static_defs, dynamic_combos, skips: [str]):
    class_name = shader_name + "_Static_Index"
    out_string = "#include \"shaderlib/cshader.h\"\n\n"

    # A define
    out_string += "#define shaderStaticTest_" + shader_name + " ("
    prefix = "vsh_" if "vs" in get_shader_type(shader_name) else "psh_"

    for combo in static_combos:
        if static_defs[combo['name']] == "":
            out_string += prefix + "forgot_to_set_static_" + combo['name'] + " + "

    out_string += "0)\n"

    # Start Class Definition
    out_string += "\nclass " + class_name + "\n{\n"
    out_string += "public:\n"

    # Constructor
    out_string += "\t" + class_name + "( void )\n\t{\n"
    for combo in static_combos:
        var_name = "m_n" + combo['name']
        if static_defs[combo['name']] != "":
            out_string += "\t\t" + var_name + " = " + static_defs[combo['name']] + ";\n"
        else:
            out_string += "\t\t" + var_name + " = 0;\n"
    out_string += "#ifdef _DEBUG\n"
    for combo in static_combos:
        bool_name = "m_b" + combo['name']
        if static_defs[combo['name']] != "":
            out_string += "\t\t" + bool_name + " = true;\n"
        else:
            out_string += "\t\t" + bool_name + " = false;\n"
    out_string += "#endif\t// _DEBUG\n"
    out_string += "\t}\n\n"

    # An Engine-Internal Function
    out_string += "\tint GetIndex( void )\n\t{\n"
    out_string += "\t\t// Asserts to make sure that we aren't using any skipped combinations.\n"
    for skip in skips:
        c_skip = skip.replace("$", "")
        # out_string += "\t\tAssert( !(" + c_skip + ") );\n"
    out_string += "\n#ifdef _DEBUG\n"
    out_string += "\t\t// Asserts to make sure that we are setting all of the combination vars.\n"
    if len(static_combos) > 0:
        combined = ""
        operator = False
        for combo in static_combos:
            if operator:
                combined += " && "
            combined += "m_b" + combo['name']
            operator = True
        out_string += "\t\tbool bAllStaticVarsDefined = " + combined + ";\n"
        out_string += "\t\tAssert( bAllStaticVarsDefined );\n"
    out_string += "#endif\t// _DEBUG\n"
    out_string += "\n\t\treturn "
    if len(static_combos) > 0:
        scale = 1
        for combo in dynamic_combos:
            scale *= int(combo['max']) - int(combo['min']) + 1
        for combo in static_combos:
            var_name = "m_n" + combo['name']
            out_string += "( " + hex(scale).upper().replace("X", "x") + " * m_n" + combo['name'] + " ) + "
            scale *= int(combo['max']) - int(combo['min']) + 1
    out_string += "0;\n\t}\n\n"

    # Setters
    for combo in static_combos:
        out_string += _write_variable_func_int(combo['name'], combo['min'], combo['max'])

    out_string += "private:\n"

    # Member Vars
    for combo in static_combos:
        out_string += "\t int m_n" + combo['name'] + ";\n"
    out_string += "#ifdef _DEBUG\n"
    for combo in static_combos:
        out_string += "\t bool m_b" + combo['name'] + ";\n"
    out_string += "#endif\t// _DEBUG\n"

    out_string += "};\n"

    return out_string


def write_dynamic_classes(shader_name, dynamic_combos, skips: [str]):
    class_name = shader_name + "_Dynamic_Index"
    out_string = ""

    # A define
    out_string += "#define shaderDynamicTest_" + shader_name + " ("
    prefix = "vsh_" if "vs" in get_shader_type(shader_name) else "psh_"

    for combo in dynamic_combos:
        out_string += prefix + "forgot_to_set_dynamic_" + combo['name'] + " + "

    out_string += "0)\n"

    # Start Class Definition
    out_string += "\nclass " + class_name + "\n{\n"
    out_string += "public:\n"

    # Constructor
    out_string += "\t" + class_name + "( void )\n\t{\n"
    for combo in dynamic_combos:
        var_name = "m_n" + combo['name']
        out_string += "\t\t" + var_name + " = 0;\n"
    out_string += "#ifdef _DEBUG\n"
    for combo in dynamic_combos:
        bool_name = "m_b" + combo['name']
        out_string += "\t\t" + bool_name + " = false;\n"
    out_string += "#endif\t// _DEBUG\n"
    out_string += "\t}\n\n"

    # An Engine-Internal Function
    out_string += "\tint GetIndex( void )\n\t{\n"
    out_string += "\t\t// Asserts to make sure that we aren't using any skipped combinations.\n"
    for skip in skips:
        c_skip = skip.replace("$", "")
        # out_string += "\t\tAssert( !(" + c_skip + ") );\n"
    out_string += "\n#ifdef _DEBUG\n"
    out_string += "\t\t// Asserts to make sure that we are setting all of the combination vars.\n"
    if len(dynamic_combos) > 0:
        combined = ""
        operator = False
        for combo in dynamic_combos:
            if operator:
                combined += " && "
            combined += "m_b" + combo['name']
            operator = True
        out_string += "\t\tbool bAllDynamicVarsDefined = " + combined + ";\n"
        out_string += "\t\tAssert( bAllDynamicVarsDefined );\n"
    out_string += "#endif\t// _DEBUG\n"
    out_string += "\n\t\treturn "
    if len(dynamic_combos) > 0:
        scale = 1
        for combo in dynamic_combos:
            out_string += "( " + hex(scale).upper().replace("X", "x") + " * m_n" + combo['name'] + " ) + "
            scale *= int(combo['max']) - int(combo['min']) + 1
    out_string += "0;\n\t}\n\n"

    # Setters
    for combo in dynamic_combos:
        out_string += _write_variable_func_int(combo['name'], combo['min'], combo['max'])

    out_string += "private:\n"

    # Member Vars
    for combo in dynamic_combos:
        out_string += "\t int m_n" + combo['name'] + ";\n"
    out_string += "#ifdef _DEBUG\n"
    for combo in dynamic_combos:
        out_string += "\t bool m_b" + combo['name'] + ";\n"
    out_string += "#endif\t// _DEBUG\n"

    out_string += "};\n"

    return out_string


def _num_combos(static_combos, dynamic_combos):
    scale = 1
    for combo in dynamic_combos:
        scale *= int(combo['max']) - int(combo['min']) + 1
    for combo in static_combos:
        scale *= int(combo['max']) - int(combo['min']) + 1
    return scale


def _num_dynamic_combos(dynamic_combos):
    scale = 1
    for combo in dynamic_combos:
        scale *= int(combo['max']) - int(combo['min']) + 1
    return scale


def dump_file_list(shader_name, file_name, static_combos, dynamic_combos, skip_code, centroid_mask):
    with open("./compile_temp/filelist.txt", "a") as file_list:
        file_list.write("#BEGIN " + shader_name + "\n")
        file_list.write(file_name + "\n")
        file_list.write("#DEFINES-D:\n")
        for combo in dynamic_combos:
            file_list.write(combo['name'] + "=" + combo['min'] + ".." + combo['max'] + "\n")
        file_list.write("#DEFINES-S:\n")
        for combo in static_combos:
            file_list.write(combo['name'] + "=" + combo['min'] + ".." + combo['max'] + "\n")
        file_list.write("#SKIPS:\n" + skip_code + "\n")
        file_list.write("#COMMAND:\n")
        file_list.write("fxc.exe ")
        file_list.write("/DTOTALSHADERCOMBOS=" + str(_num_combos(static_combos, dynamic_combos)) + " ")
        file_list.write("/DCENTROIDMASK=" + str(centroid_mask) + " ")
        file_list.write("/DNUMDYNAMICCOMBOS=" + str(_num_dynamic_combos(dynamic_combos)) + " ")
        file_list.write("/DFLAGS=0x0")
        file_list.write("\n")
        file_list.write("/Dmain=main /Emain /T" + get_shader_type(shader_name) + " ")
        file_list.write("/DSHADER_MODEL_" + get_shader_type(shader_name).upper() + "=1 ")
        file_list.write("/nologo ")
        file_list.write("/Foshader.o ")
        file_list.write(file_name)
        file_list.write(">output.txt 2>&1 \n")
        file_list.write("#END\n")
