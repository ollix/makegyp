import exceptions
import os
import re
import subprocess

from makegyp.core import argparser
from makegyp.core import gyp


class Parser(object):

    def __init__(self, *args, **kwargs):
        super(Parser, self).__init__(*args, **kwargs)
        self.current_directory = '.'

    def get_config_files(self, configure_output):
        class_name = self.__class__.__name__
        raise exceptions.NotImplementedError(
            '%s::get_config_files is not implemented.' % class_name)

    def get_targets(self, make_output):
        class_name = self.__class__.__name__
        raise exceptions.NotImplementedError(
            '%s::get_targets is not implemented.' % class_name)


class MakeParser(Parser):
    # Regular expression patterns:
    compile_re = '^\s+CC\s+(\w+)'
    # For extracting generated config files
    config_file_re = re.compile(r'config.status:\screating\s(.*config\.h)')
    # End make: looks like "make[3]: Nothing to be done for `all-am'"
    end_make_re = re.compile(r'^make\[\d\]:\sNothing to be done')
    link_re = re.compile(r'^\s+CCLD\s+(\w+)')
    # Make mode: for example, all-am, all-recursive
    make_mode_re = re.compile(r'^.+?/make\s+([a-z\-]+)$')
    # Start make: looks like "Making all in something"
    start_make_re = re.compile(r'^Making all in ([\.\/\w]+)')

    def __replace_expressions(self, args):
        # Remembers the current directory for later resotred:
        original_directory = os.path.abspath(os.path.curdir)
        # Changes to the working directory:
        working_directory = os.path.join(original_directory,
                                         self.current_directory)
        original_directory = os.path.abspath(original_directory)
        os.chdir(original_directory)

        # Replaces each expression:
        replaces = dict()
        for expression in re.finditer(r'`(.*?)`', args):
            output = subprocess.check_output(expression.group(1),
                                             shell=True)
            replaces[expression.group(0)] = output.strip()
        for expression, value in replaces.items():
            args = args.replace(expression, value)

        # Chanages the directory back:
        os.chdir(original_directory)

        return args

    def _get_arg_type(self, args):
        """Accept a single-line args and returns the corresponded type."""

        # Start make:
        if re.match(self.start_make_re, args):
            return 'start_make'
        # End make:
        elif re.match(self.end_make_re, args):
            return 'end_make'
        # Make mode:
        elif re.match(self.make_mode_re, args):
            return 'make_mode'

    def _handle_end_make_args(self, args):
        self.current_directory = os.path.relpath(
            os.path.join(self.current_directory, '..'))

    def _handle_make_mode_args(self, args):
        self.make_mode = re.sub(self.make_mode_re, r'\1', args)

    def _handle_start_make_args(self, args):
        directory_name = re.sub(self.start_make_re, r'\1', args)
        path = os.path.join(self.current_directory, directory_name)
        if not os.path.isdir(path):
            path = os.path.join(self.current_directory, '..', directory_name)
        self.current_directory = os.path.relpath(path)

    def _handle_unknown_args(self, args):
        pass

    def get_config_files(self, configure_output):
        config_files = list()

        for line in configure_output.split('\n'):
            if not self.config_file_re.match(line):
                continue

            config_file = re.sub(self.config_file_re, r'\1', line)
            if config_file:
                config_files.append(config_file)

        return config_files

    def get_targets(self, make_output):
        """Parse the make output and returns a list of targets."""
        self.current_directory = '.'
        self.make_mode = None
        self.previous_arg_type = None
        self.targets = list()
        self.compiled_objects = dict()

        for line in make_output.split('\n'):
            arg_type = self._get_arg_type(line)
            if arg_type == 'start_make':
                self._handle_start_make_args(line)
            elif arg_type == 'end_make':
                self._handle_end_make_args(line)
            elif arg_type == 'make_mode':
                self._handle_make_mode_args(line)
            else:
                line = self.__replace_expressions(line)
                self._handle_unknown_args(line)

            self.previous_arg_type = arg_type

        return self.targets


class CmakeParser(Parser):
    target_directories_path = os.path.join('CMakeFiles',
                                           'TargetDirectories.txt')

    # Regular expression patterns:
    source_re = re.compile(r'^CMakeFiles/\w+\.dir/(.*)\.\w+\s?$')
    cmake_set_start_re = re.compile(r'^SET\((\w+)\s*$')
    cmake_set_end_re = re.compile(r'^\s*\)\s*$')
    cmake_target_path_re = re.compile(r'^(.+?/CMakeFiles/\w+\.dir).*?$')

    def __init__(self, *args, **kwargs):
        super(CmakeParser, self).__init__(*args, **kwargs)
        self.targets = list()  # caches targets generated by __get_target()

    def __get_root_target_path(self, path):
        if not re.match(self.cmake_target_path_re, path):
            return None

        return re.sub(self.cmake_target_path_re, r'\1', path)

    def __get_target(self, target_directory):
        for target in self.targets:
            if target.target_directory == target_directory:
                return target

        # Determines the target name and create the Target object:
        target_link_info = self.__get_target_link_info(target_directory)
        if not target_link_info:
            return None

        target = gyp.Target(target_link_info['product_name'])
        self.targets.append(target)
        # Sets target path for searching in self.targets:
        target.target_directory = target_directory
        # Sets sources:
        target.sources.update(target_link_info['sources'])
        # Sets defines:
        defines = self.__get_target_defines(target_directory)
        target.defines = target.defines.union(defines)
        # Finds include directories and dependencies:
        depend_info_path = os.path.join(target_directory, 'DependInfo.cmake')
        self.__merge_target_depend_info(target, depend_info_path)

        return target

    def __get_target_defines(self, target_path):
        defines = set()
        flag_file = file(os.path.join(target_path, 'flags.make'))
        for line in flag_file:
            if line.startswith('#'):
                continue

            for match in re.finditer(r'-D(\w+)', line):
                define = match.group(1)
                defines.add(define)
        flag_file.close()
        return defines


    def __merge_target_depend_info(self, target, depend_info_path):
        depend_info_file = file(depend_info_path)
        iterates_variable_values = False

        for line in depend_info_file:
            # Skips comments
            if line.startswith('#'):
                continue
            # Matches CMake SET start:
            elif re.match(self.cmake_set_start_re, line):
                variable_name = re.sub(self.cmake_set_start_re, r'\1', line)
                iterates_variable_values = True
            # Matches CMake SET end:
            elif re.match(self.cmake_set_end_re, line):
                variable_name = None
                iterates_variable_values = False
            # Processes variable values:
            elif iterates_variable_values:
                value = line.strip().split('"')[1]
                # Depedencies:
                if variable_name == 'CMAKE_TARGET_LINKED_INFO_FILES':
                    # Adds target name to dependencies:
                    target_path = self.__get_root_target_path(value)
                    dependency = self.__get_target(target_path)
                    if dependency is not None:
                        target.dependencies.add(dependency.name)
                    # Adds dependencies recursively:
                    self.__merge_target_depend_info(target, value)
                # Include directories:
                elif variable_name == 'CMAKE_C_TARGET_INCLUDE_PATH':
                    target.include_dirs.add(value)

        depend_info_file.close()

    def __get_target_link_info(self, target_path):
        path = self.__get_root_target_path(target_path)
        if path is None:
            return None

        link_file = file(os.path.join(path, 'link.txt'))
        arguments = link_file.readline().split()
        link_file.close()

        sources = list()
        for source in arguments[3:]:
            source = re.sub(self.source_re, r'\1', source)
            sources.append(source)

        return dict(product_name=arguments[2], sources=sources)

    def get_config_files(self, configure_output):
        return list()

    def get_targets(self, make_output):
        targets = list()

        # Determines target directories:
        target_directories_file = file(self.target_directories_path)
        target_directories = target_directories_file.read()
        target_directories_file.close()

        # Iterates each target directory to gather target info:
        for target_directory in target_directories.split('\n'):
            if not target_directory:
                continue
            target = self.__get_target(target_directory)
            targets.append(target)

        return targets


class GccParser(MakeParser):
    gcc_argument_parser = argparser.GccArgumentParser()

    # Regular expression patterns:
    compile_re = re.compile(r'(.*?--mode=compile\s)?gcc\s(.*?)')
    link_re = re.compile(r'^.*?libtool\s(.*?\s--mode=link\sgcc)?(.*)')

    def _add_compiled_object(self, parsed_args):
        # Determines the current directory by checking if the source exists:
        source = parsed_args.sources[0]
        current_directory = self.current_directory
        while True:
            source_path = os.path.join(current_directory, source)
            if os.path.isfile(source_path):
                self.current_directory = current_directory
                break
            else:
                current_directory = os.path.join(current_directory, '..')
                current_directory = os.path.relpath(current_directory)
                if current_directory == '..':
                    print "Couldn't find object: %r" % source_path
                    exit(1)

        dirname = os.path.join(current_directory, parsed_args.output)
        dirname = os.path.relpath(os.path.dirname(dirname))

        if dirname in self.compiled_objects:
            compiled_objects = self.compiled_objects[dirname]
        else:
            compiled_objects = dict()
            self.compiled_objects[dirname] = compiled_objects

        object_basename = os.path.basename(parsed_args.output)
        compiled_objects[object_basename] = parsed_args

    def _add_target(self, parsed_args):
        target_object_name = os.path.basename(parsed_args.output)
        target = gyp.Target(target_object_name)
        target.object_name = target_object_name

        for source_path in parsed_args.sources:
            # If the source path represents a dependency, find the corresponded
            # target instance and get the target name:
            source_is_dependency = False
            basename = os.path.basename(source_path)
            for cached_target in self.targets:
                if cached_target.object_name == basename:
                    source_is_dependency = True
                    target.dependencies.add(cached_target)
                    break
            if source_is_dependency:
                continue

            # Retrieves the parsed arguments of the source by checking
            # the dictionary of compiled objects:
            dirname = os.path.join(self.current_directory,
                                   os.path.dirname(source_path))
            dirname = os.path.relpath(dirname)
            compiled_objects = self.compiled_objects[dirname]
            source_name = os.path.basename(source_path)
            source_args = compiled_objects[source_name]
            # Adds source path:
            source_path = os.path.join(dirname, source_args.sources[0])
            source_path = os.path.relpath(source_path)
            target.sources.add(source_path)
            # Adds include dirs:
            if source_args.include_dirs is not None:
                for include_dir in source_args.include_dirs:
                    include_dir = os.path.join(dirname, include_dir)
                    include_dir = os.path.relpath(include_dir)
                    target.include_dirs.add(include_dir)
            # Adds defines:
            if source_args.defines is not None:
                target.defines = target.defines.union(source_args.defines)

        self.targets.append(target)

    def _handle_unknown_args(self, args):
        # Determines the argument type and generates parsed arguments:
        if re.match(self.compile_re, args):
            gcc_args = re.sub(self.compile_re, r'\2', args)
            parsed_args = self.gcc_argument_parser.parse_args(gcc_args)
            if parsed_args.library_dirs:
                arg_type = 'link'
            else:
                arg_type = 'compile'
        elif re.match(self.link_re, args):
            gcc_args = re.sub(self.link_re, r'\2', args)
            parsed_args = self.gcc_argument_parser.parse_args(gcc_args)
            arg_type = 'link'
        else:
            return  # unknown type

        if arg_type == 'compile':
            self._add_compiled_object(parsed_args)
        elif arg_type == 'link':
            self._add_target(parsed_args)


class LibtoolParser(GccParser):
    compile_re = re.compile(r'^libtool: compile:\s+gcc\s+?(.+?)$')
    link_re = re.compile(r'^.+?libtool\s.*?\s--mode=link\s+?gcc\s+?(.*?)$')

    def _handle_unknown_args(self, args):
        # Compile:
        if re.match(self.compile_re, args):
            gcc_args = re.sub(self.compile_re, r'\1', args)
            parsed_args = self.gcc_argument_parser.parse_args(gcc_args)
            parsed_args.output = parsed_args.MT
            self._add_compiled_object(parsed_args)
        # Link:
        elif re.match(self.link_re, args):
            gcc_args = re.sub(self.link_re, r'\1', args)
            parsed_args = self.gcc_argument_parser.parse_args(gcc_args)
            self._add_target(parsed_args)
