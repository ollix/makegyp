import imp
import os
import subprocess

import makegyp


def build_target(dirname, library_name, target_name=None):
    if target_name is None:
        target_name = library_name

    curdir = os.path.abspath(os.path.curdir)
    target_id = '%s::%s' % (library_name, target_name)

    print "* Build target: %s" % target_id
    library_dir = os.path.join(os.path.abspath(dirname), library_name)
    os.chdir(os.path.join(os.path.abspath(dirname), library_name))

    gyp_command = 'gyp --depth=. -f ninja %s.gyp' % library_name
    print '* Run %r' % gyp_command
    if subprocess.call(gyp_command, shell=True) != 0:
        exit(1)

    # Compiles:
    ninja_command = 'ninja -C out/Debug/ %s' % target_name
    print '* Run %r' % ninja_command
    if subprocess.call(ninja_command, shell=True) != 0:
        exit(1)

    print "Target built successfully: %s" % target_id
    os.chdir(curdir)

    product_name = target_name
    if target_name.startswith('lib'):
        product_name = '%s.a' % product_name

    return os.path.join(library_dir, 'out', 'Debug', product_name)

def get_formula(library_name, dest_dir):
    formula_module = import_module(library_name, [get_formula_root()])
    formula_class = getattr(formula_module, library_name.title())
    return formula_class(dest_dir)

def get_formula_root():
    return os.path.join(get_package_root(), 'formula')

def get_package_root():
    return os.path.dirname(makegyp.__file__)

def import_module(module_name, search_paths):
    try:
        results = imp.find_module(module_name, search_paths)
    except ImportError:
        print 'No matched module found: %r' % module
        exit(1)

    for result in results:
        if isinstance(result, str) and result.endswith('.py'):
            module = imp.load_source('module', result)
            return module

    class_ = getattr(module, library_name.title())
    instance = class_(dest_dir)
    instance.install()


def install_formula(library_name, dest_dir, installed_formulas=None):
    if installed_formulas is None:
        installed_formulas = set()

    if library_name in installed_formulas:
        return

    formula = get_formula(library_name, dest_dir)
    if formula.dependencies:
        for depencency in formula.dependencies:
            install_formula(depencency, dest_dir, installed_formulas)

    formula.install()
    print '#' * 3
    return installed_formulas
