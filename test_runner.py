# -*- coding: utf-8 -*-
import shlex, subprocess
import os
import tarfile
import sys
import platform

if sys.version_info[0] < 3:
    import urllib
    urlretrieve = urllib.urlretrieve
else:
    import urllib.request
    urlretrieve = urllib.request.urlretrieve

boost_dir = os.environ.get("BOOST_PATH")
if not boost_dir:
    boost_dir = 'D:\\boost_1_60_0'

LUA_VERSIONS = ["lua-5.3.3", "lua-5.2.4", "lua-5.1.5", "luajit"]
MAIJOR_TEST_LUA_VERSIONS = ["lua-5.3.3"]

TEST_MSVC_VERS = [("msvc2015", "Visual Studio 14 2015", "", True),
                  ("msvc2015win64", "Visual Studio 14 2015 Win64", "", True),
                  ("msvc2013", "Visual Studio 12 2013", "", False),
                  ("msvc2013win64", "Visual Studio 12 2013 Win64", "", False),
                  ("msvc2015", "Visual Studio 14 2015", "", True)]

TEST_COMPILERS = [
    ('gcc-4.7', 'g++-4.7', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('gcc-4.8', 'g++-4.8', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('gcc-4.9', 'g++-4.9', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('gcc-5', 'g++-5', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('gcc-6', 'g++-6', '-DCMAKE_CXX_FLAGS=-std=c++03', False),
    ('gcc-6', 'g++-6', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('gcc-6', 'g++-6', '-DCMAKE_CXX_FLAGS=-std=c++14', False),
    ('gcc', 'g++', '-DCMAKE_CXX_FLAGS=-std=c++11', True),
    ('clang', 'clang++', '-DCMAKE_CXX_FLAGS=-std=c++11', True),
    ('clang-3.5', 'clang++-3.5', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('clang-3.6', 'clang++-3.6', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('clang-3.7', 'clang++-3.7', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('clang-3.8', 'clang++-3.8', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('clang-3.9', 'clang++-3.9', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('clang-4.0', 'clang++-4.0', '-DCMAKE_CXX_FLAGS=-std=c++11', False),
    ('clang-3.8', 'clang++-3.8', '-DCMAKE_CXX_FLAGS=-std=c++14', False),
    ('clang-3.9', 'clang++-3.9', '-DCMAKE_CXX_FLAGS=-std=c++14', False), (
        'clang-4.0', 'clang++-4.0', '-DCMAKE_CXX_FLAGS=-std=c++14', False)
]


def build_and_exec_test(compiler, lua_version, build_type, dir_opt):
    ccompiler = compiler[0]
    cxxcompiler = compiler[1]
    addopt = compiler[2]
    if os.system(cxxcompiler + ' -v 2> /dev/null') != 0: return

    buildpath = "_build/" + compiler[
        0] + "_" + lua_version + "_" + build_type + "_" + dir_opt
    if not os.path.exists(buildpath):
        os.makedirs(buildpath)
    os.chdir(buildpath)
    ret = os.system('CC=' + ccompiler + ' CXX=' + cxxcompiler +
                    ' cmake ../../  ' + addopt + ' -DLOCAL_LUA_DIRECTORY=' +
                    "_build/" + lua_version + ' -DCMAKE_BUILD_TYPE=' +
                    build_type)
    if ret != 0:  #pass through cmake failed. e.g. not found lua
        if lua_version in MAIJOR_TEST_LUA_VERSIONS:
            raise Exception("cmake error at" + buildpath)
        os.chdir("../../")
        return
    ret = os.system('make -j 2')
    if ret != 0:
        raise Exception("build error at" + buildpath)

    testcommand = 'ctest --output-on-failure'
    if platform.system() == 'Linux':
        testcommand += ' -T memcheck'
    ret = os.system(testcommand)
    if ret != 0:
        raise Exception("test error at" + buildpath)
    os.chdir("../../")


def build_with_target_compiler(lua_version):
    for i, compiler in enumerate(TEST_COMPILERS):
        if not compiler[3] and lua_version not in MAIJOR_TEST_LUA_VERSIONS:
            continue
        build_and_exec_test(compiler, lua_version, "Debug", str(i))
        if compiler[3]:
            build_and_exec_test(compiler, lua_version, "Release", str(i))


def build_msvc_and_exec_test(msvcver, lua_version, build_type):
    buildpath = '_build/' + msvcver[0] + '_' + lua_version
    if not os.path.exists(buildpath):
        os.makedirs(buildpath)
    os.chdir(buildpath)
    ret = os.system('cmake ../../ -DLOCAL_LUA_DIRECTORY=' + "_build/" +
                    lua_version + ' -G "' + msvcver[1] + '" ' + msvcver[2])
    if ret != 0:  #pass through cmake failed. e.g. not found lua
        if lua_version in MAIJOR_TEST_LUA_VERSIONS:
            raise Exception("cmake error at" + buildpath)
        os.chdir("../../")
        return
    ret = os.system('cmake --build . --config ' + build_type)
    if ret != 0:
        raise Exception("build error at" + buildpath)
    ret = os.system('ctest --output-on-failure -C ' + build_type)
    if ret != 0:
        raise Exception("test error at" + buildpath)
    os.chdir("../../")


def build_with_msvc_ver(lua_version):
    for msvcver in TEST_MSVC_VERS:
        if not msvcver[3] and lua_version not in MAIJOR_TEST_LUA_VERSIONS:
            continue
        build_msvc_and_exec_test(msvcver, lua_version, 'Debug')
        if msvcver[3]:
            build_msvc_and_exec_test(msvcver, lua_version, 'Release')

if __name__ == '__main__':
    for i, luaversion in enumerate(LUA_VERSIONS):
        if not os.path.exists("_build/"):
            os.makedirs("_build/")
        if not os.path.exists("_build/" + luaversion) and luaversion != 'luajit':
            if not os.path.exists(luaversion + ".tar.gz"):
                lua_url = "https://www.lua.org/ftp/" + luaversion + ".tar.gz"
                urlretrieve(lua_url, "_build/" + luaversion + ".tar.gz")
            tf = tarfile.open("_build/" + luaversion + ".tar.gz", 'r')
            tf.extractall("_build/")

        if os.name == 'nt':
            build_with_msvc_ver(luaversion, )
        else:
            build_with_target_compiler(luaversion)
