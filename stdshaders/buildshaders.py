"""Replaces buildshaders.bat"""
import argparse
import multiprocessing
import os
import shutil
import sys

import shadercompile_utils.shader_type

test_args = [
    '-shaders', 'stdshader_dx9_30',
    '-game', 'D:\\SteamLibrary\\SteamApps\\common\\Half-Life 2\\hl2',
    '-source', '..\\..',
    '-bin_dir', 'D:\\SteamLibrary\\SteamApps\\common\\Source SDK Base 2013 Singleplayer\\bin\\',
    '-dx9_30',
    '-force30'
]

parser = argparse.ArgumentParser(description="Build a shader project.")
parser.add_argument("-shaders", help="Name of a text file listing shaders to compile.")
parser.add_argument('-game', help="gameinfo.txt directory")
parser.add_argument('-source', help="Root SDK directory. Required if -game is specified")
parser.add_argument('-bin_dir', help="Bin directory")
parser.add_argument('-dx9_30', help="Use shader model 3.0", action='store_true')
parser.add_argument('-force30', help="Force shader model 3.0", action='store_true')
parser.add_argument('-dynamic', help="Only generate .inc files", action='store_true')


def setup_dirs():
    if not os.path.isdir("./compile_temp"):
        os.mkdir("./compile_temp")

    if not os.path.isdir("./compile_temp/shaders"):
        os.mkdir("./compile_temp/shaders")

    if not os.path.isdir("./compile_temp/shaders/fxc"):
        os.mkdir("./compile_temp/shaders/fxc")

    if not os.path.isdir("./compile_temp/shaders/vsh"):
        os.mkdir("./compile_temp/shaders/vsh")

    if not os.path.isdir("./compile_temp/shaders/psh"):
        os.mkdir("./compile_temp/shaders/psh")

    if not os.path.isdir("./include"):
        os.mkdir("./include")

    if os.path.isfile("./compile_temp/filelist.txt"):
        os.remove("./compile_temp/filelist.txt")


if __name__ == '__main__':
    # DirectX Options
    directx_sdk_version = "pc09.00"
    directx_sdk_bin_dir = "/dx9sdk/utilities".replace("/", os.sep)
    directx_force30 = False

    # Parse arguments and process them
    args = parser.parse_args(sys.argv[1:])

    if args.dx9_30:
        directx_sdk_version = "pc09.30"
        directx_sdk_bin_dir = "/dx10sdk/utilities/dx9_30".replace("/", os.sep)
    directx_force30 = args.force30

    # Check for gameinfo.txt

    setup_dirs()
    bin_dir = os.path.abspath(args.bin_dir).rstrip(os.path.sep)
    game_dir = os.path.abspath(args.game).rstrip(os.path.sep)
    source_dir = os.path.abspath(args.source).rstrip(os.path.sep)
    shader_list = shadercompile_utils.update_shaders(args.shaders, source_dir, directx_force30, args.dynamic)

    files_to_copy = {}
    for shader in shader_list:
        shader.prep(args.dynamic)
        if shader.compile_vcs and not args.dynamic:
            files_to_copy[shader.file_path + shader.file_name] = 1
            for dep in shader.dependencies:
                files_to_copy[dep] = 1

    if args.dynamic or not os.path.isfile("./compile_temp/filelist.txt"):
        exit(0)

    with open("./compile_temp/uniquefilestocopy.txt", "w") as unique_txt:
        for file in files_to_copy:
            clean_file = os.path.basename(file)
            unique_txt.write(clean_file + "\n")
            shutil.copyfile(file, "compile_temp/".replace("/", os.sep) + clean_file)
        if args.dx9_30:
            unique_txt.write(source_dir + "/devtools/bin/d3dx9_33.dll\n".replace("/", os.sep))
            unique_txt.write(source_dir + directx_sdk_bin_dir + "/dx_proxy.dll\n".replace("/", os.sep))
            unique_txt.write(bin_dir + "/shadercompile.exe\n".replace("/", os.sep))
            unique_txt.write(bin_dir + "/shadercompile_dll.dll\n".replace("/", os.sep))
            unique_txt.write(bin_dir + "/vstdlib.dll\n".replace("/", os.sep))
            unique_txt.write(bin_dir + "/tier0.dll\n".replace("/", os.sep))

    shader_path = os.path.abspath("./compile_temp/".replace("/", os.sep))

    os.chdir(bin_dir)

    thread_count = max(1, multiprocessing.cpu_count() - 2)

    shader_list.clear()  # Free some memory

    print(
        "shadercompile.exe "
        "-nompi -nop4 -allowdebug "
        "-shaderpath \"{}\" "
        "-game \"{}\" "
        "-threads {}"
        "".format(shader_path, game_dir, thread_count)
    )
    
    os.system(
        "\""
        "shadercompile.exe "
        "-nompi -nop4 -allowdebug "
        "-shaderpath \"{}\" "
        "-game \"{}\" "
        "-threads {}"
        "\"".format(shader_path, game_dir, thread_count)
    )

    os.chdir(shader_path)
    publish_dir = game_dir + "/shaders".replace("/", os.sep)
    shutil.copytree("./shaders".replace("/", os.sep), publish_dir,  dirs_exist_ok=True)
