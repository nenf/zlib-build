#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from shlex import split as arg_split
from shutil import copy2, rmtree
from subprocess import Popen, PIPE, STDOUT
from sys import stderr
from os import path, chdir, makedirs

parser = ArgumentParser(description="Script for build zlib project with static runtime")
parser.add_argument("-o", "--out", help="Output directory", type=str, required=True)
parser.add_argument("-r", "--revision", help="Commit id or tag", type=str, required=True)
args = parser.parse_args()


def die(text, exit_code=1):
    stderr.write("ERROR: {0}\n".format(text))
    exit(exit_code)


def console(command, stream=False):
    ret = None
    out = None
    print(command)
    try:
        process = Popen(arg_split(command), stdout=PIPE, stderr=STDOUT)
        if stream:
            for line in iter(process.stdout.readline, b''):
                print line.rstrip()
        process.wait()
    except Exception as e:
        ret = e.args[0]
        out = e
    else:
        ret = process.returncode
        out = process.stdout.read()
    finally:
        return {"code": ret, "message": out}


class GitUtils:
    def __init__(self, project_name, repository):
        self.repository = repository
        self.project_name = project_name

    def clone(self):
        if path.exists(self.project_name):
            return {"code": 0, "message": "{0} exist".format(self.project_name)}

        command = "git clone {0}".format(self.repository)
        res = console(command, True)
        if res["code"] != 0:
            die(res["message"], res["code"])

    def fetch(self):
        command = "git -C {0} fetch origin".format(self.project_name)
        res = console(command, True)
        if res["code"] != 0:
            die(res["message"], res["code"])

    def pull(self):
        command = "git -C {0} pull".format(self.project_name)
        res = console(command, True)
        if res["code"] != 0:
            die(res["message"], res["code"])

    def checkout(self, commit_id):
        command = "git -C '{0}' checkout {1}".format(self.project_name, commit_id)
        res = console(command, True)
        if res["code"] != 0:
            die(res["message"], res["code"])


class ZlibBuild:
    def __init__(self, zlib_folder, out_folder):
        self.zlib_folder = zlib_folder
        self.out_folder = out_folder
        self.lib_path_out = path.join(self.out_folder, "lib")
        self.include_path_out = path.join(self.out_folder, "include")

    @staticmethod
    def __replace_in_file(file_path, search_string, replace_string):
        with open(file_path, "r") as f:
            file_data = f.read()

        file_data = file_data.replace(search_string, replace_string)

        with open(file_path, "w") as f:
            f.write(file_data)

    def __makefile_patch(self):
        path_flags = [
            ["-MD", "-MT"],
            [" -02", ""],
            ["-Oy-", "-Ox"],
            [" -coff", ""],
            [" -Zi", ""],
            ["-debug", "-release"]
        ]
        for old_flag, new_flag in path_flags:
            self.__replace_in_file("win32/Makefile.msc", old_flag, new_flag)

    def __clean(self):
        if path.exists(self.out_folder):
            rmtree(self.out_folder)
        res = console("nmake /f win32/Makefile.msc clean", True)
        if res["code"] != 0:
            message = "You should call vcvars.bat : {0}".format(res["message"])
            die(message, res["code"])

    def build(self):
        chdir(self.zlib_folder)
        self.__makefile_patch()
        self.__clean()
        res = console("nmake /f win32/Makefile.msc", True)
        if res["code"] != 0:
            message = "You should call vcvars.bat : {0}".format(res["message"])
            die(message, res["code"])

        self.__post_build()

    def __post_build(self):
        makedirs(self.lib_path_out)
        makedirs(self.include_path_out)
        copy2("zlib.lib", self.lib_path_out)
        copy2("zlib.h", self.include_path_out)
        copy2("zconf.h", self.include_path_out)
        copy2("configure", self.include_path_out)

zlib_folder = "zlib"

git = GitUtils(zlib_folder, "https://github.com/madler/zlib.git")
git.clone()
git.checkout("-- .")
git.checkout(args.revision)
git.fetch()
git.pull()

zlib = ZlibBuild(zlib_folder, args.out)
zlib.build()
