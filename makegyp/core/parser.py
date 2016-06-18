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
    # For removing bash conditional expression.
    trim_re = re.compile(r'^(if\s+)?(.*?)(\s*(;|>|&&).*)?$')
    # For extracting generated config files
    config_creating_re = re.compile(r'^config.status:\screating\s+(.*\.h)\s*$')
    config_linking_re = re.compile(
        r'^config.status:\slinking\s+(.*?)\s+to\s+(.*?)\s*$')
    # End make: looks like "make[3]: Nothing to be done for `all-am'"
    end_make_re = re.compile(r'^make\[\d\]:\sNothing to be done')
    link_re = re.compile(r'^\s+CCLD\s+(\w+)')
    # Make mode: for example, all-am, all-recursive
    make_mode_re = re.compile(r'^.+?/make\s+([a-z\-]+)$')
    # Object key:
    object_key_re = re.compile(r'^/?(.+?/)*(.+?)\.(o|lo)\s*$')
    # Start make: looks like "Making all in something"
    start_make_re = re.compile(r'^[Mm]aking \w+ in ([\.\/\w]+?)\.*$')

    object_filename_exts = ('o', 'lo')

    def __init__(self, ignored_objects=None, *args, **kwargs):
        """Initializes the parser for make build tool.

        ignored_objects: a list of tuple contains found compiled object to
            ignore. Currently only used in _add_compiled_object().
        """
        self.ignored_objects = ignored_objects if ignored_objects else list()
        super(MakeParser, self).__init__(*args, **kwargs)

    def _get_object_key(self, object_path):
        return re.sub(self.object_key_re, r'\2', object_path)

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
            try:
                output = subprocess.check_output(expression.group(1),
                                                 stderr=subprocess.STDOUT,
                                                 shell=True)
            except subprocess.CalledProcessError:
                output = 'makegyp_unknown_evaluation'
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
        pass

    def _handle_make_mode_args(self, args):
        self.make_mode = re.sub(self.make_mode_re, r'\1', args)

    def _handle_start_make_args(self, args):
        # Determines the current working directory:
        target_directory = re.sub(self.start_make_re, r'\1', args)
        current_directory = self.current_directory
        while True:
            directory = os.path.join(current_directory, target_directory)
            directory = os.path.relpath(directory)
            if os.path.isdir(directory):
                self.current_directory = directory
                return
            else:
                current_directory = os.path.join(current_directory, '..')
                current_directory = os.path.relpath(current_directory)
                if current_directory.startswith('..'):
                    print('Cannot find target directory: %r' % target_directory)
                    exit(1)

    def _handle_unknown_args(self, args):
        pass

    def get_config_files(self, configure_output):
        config_files = list()
        current_directory = '.'

        switch_dir_re = re.compile(r'continue configure in \w+ builddir \"(.*)\"\s*')

        for line in configure_output.split('\n'):
            config_file = None

            # Switching directory:
            if switch_dir_re.match(line):
                target_directory = re.sub(switch_dir_re, r'\1', line)
                current_directory = os.path.join(current_directory,
                                                 target_directory)
                current_directory = os.path.relpath(current_directory)
                continue
            # Creating config file:
            elif self.config_creating_re.match(line):
                config_file = re.sub(self.config_creating_re, r'\1', line)
            elif self.config_linking_re.match(line):
                config_file = re.sub(self.config_linking_re, r'\1', line)
            else:
                continue

            config_file_path = os.path.join(current_directory, config_file)
            config_file_path = os.path.relpath(config_file_path)
            if os.path.isfile(config_file_path):
                config_files.append(config_file_path)
            else:
                print('Failed to get config file at %r' % config_file_path)

        return config_files

    def get_targets(self, make_output):
        """Parse the make output and returns a list of targets."""
        self.current_directory = '.'
        self.make_mode = None
        self.targets = list()
        self.compiled_objects = dict()

        line_head = ''  # caches line ends with '\'
        for line in make_output.split('\n'):
            line = line_head + line.strip()
            line_head = ''
            arg_type = self._get_arg_type(line)
            if arg_type == 'start_make':
                self._handle_start_make_args(line)
            elif arg_type == 'end_make':
                self._handle_end_make_args(line)
            elif arg_type == 'make_mode':
                self._handle_make_mode_args(line)
            else:
                # Removes evaluation expression
                line = self.__replace_expressions(line)
                # Removes conditional expressions:
                if re.match(self.trim_re, line):
                    line = re.sub(self.trim_re, r'\2', line)
                if line.endswith('\\'):
                    line_head = line[:-1]
                    continue

                self._handle_unknown_args(line)

        return self.targets


class CmakeParser(Parser):
    archiver_argument_parser = argparser.ArchiverArgumentParser()
    gcc_argument_parser = argparser.GccArgumentParser()

    target_directories_path = os.path.join('CMakeFiles',
                                           'TargetDirectories.txt')

    # Regular expression patterns:
    source_re = re.compile(r'^CMakeFiles/.+\.dir/(.*)\.\w+\s?$')
    cmake_set_start_re = re.compile(r'^SET\((\w+)\s*$')
    cmake_set_end_re = re.compile(r'^\s*\)\s*$')
    cmake_target_path_re = re.compile(r'^(.+?/CMakeFiles/.+\.dir).*?$')

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
        target_link_info = self.__get_link_info(target_directory)
        if target_link_info is None:
            return None

        target = gyp.Target(target_link_info.output)
        self.targets.append(target)
        # Sets target path for searching in self.targets:
        target.target_directory = target_directory
        # Sets sources:
        target.sources.update(target_link_info.sources)
        # Sets defines:
        defines = self.__get_target_defines(target_directory)
        target.defines = target.defines.union(defines)
        # Finds include directories and dependencies:
        depend_info_path = os.path.join(target_directory, 'DependInfo.cmake')
        self.__merge_target_depend_info(target, depend_info_path)

        return target

    def __get_target_defines(self, target_path):
        defines = set()
        flag_file = open(os.path.join(target_path, 'flags.make'))
        for line in flag_file:
            if line.startswith('#'):
                continue

            for match in re.finditer(r'-D(\w+)', line):
                define = match.group(1)
                defines.add(define)
        flag_file.close()
        return defines


    def __merge_target_depend_info(self, target, depend_info_path):
        depend_info_file = open(depend_info_path)
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
                        target.dependencies.add(dependency)
                    # Adds dependencies recursively:
                    self.__merge_target_depend_info(target, value)
                # Include directories:
                elif variable_name == 'CMAKE_C_TARGET_INCLUDE_PATH':
                    target.include_dirs.add(value)

        depend_info_file.close()

    def get_config_files(self, configure_output):
        return list()

    def __get_link_info(self, target_path):
        """Inspects the link.txt file for link info.

        This method inspects the link.txt file and iterate each line in the
        file to find out linked source files and the target name.

        It returns the Namespace() object returned by an ArgumentParser. It
        includes a lift of 'sources' indicating the source files and the
        'output' indicating the target name.

        The paths in 'sources' was revised by removing cmake-specific directory
        and prefixing the actual target directory to generate a real pate where
        the source file is.
        """
        path = self.__get_root_target_path(target_path)
        if path is None:
            return None
        else:
            path = os.path.join(path, 'link.txt')

        parsed_args = None
        link_file = open(path)
        for line in link_file:
            line = line.strip()
            if self.archiver_argument_parser.match_pattern(line):
                parsed_args = self.archiver_argument_parser.parse_args(line)
                break
            # The link may be done through gcc argumnet parser.
            if self.gcc_argument_parser.match_pattern(line):
                parsed_args = self.gcc_argument_parser.parse_args(line)
                break
        else:
            print('Failed to find source files at %r' % path)
            exit(1)
        link_file.close()

        # Converts built source paths to original source paths.
        revised_sources = list()
        # Determines the directory containing parsed source files.
        source_directory = os.path.join(target_path, '../../');
        for source in parsed_args.sources:
            if (self.source_re.match(source)):
                path = os.path.join(source_directory,
                                    re.sub(self.source_re, r'\1', source))
                revised_sources.append(os.path.relpath(path))
        parsed_args.sources = revised_sources

        return parsed_args

    def get_targets(self, make_output):
        targets = list()

        # Determines target directories:
        target_directories_file = open(self.target_directories_path)
        target_directories = target_directories_file.read()
        target_directories_file.close()

        # Iterates each target directory to gather target info:
        for target_directory in target_directories.splitlines():
            target_directory = target_directory.strip()
            if not target_directory:
                continue
            target = self.__get_target(target_directory)
            if target is None:
                print('Failed to get target info at %r' % target_directory)
                exit(1)
            targets.append(target)

        return targets


class GccParser(MakeParser):
    archiver_argument_parser = argparser.ArchiverArgumentParser()
    gcc_argument_parser = argparser.GccArgumentParser()

    # Regular expression patterns:
    library_re = re.compile(
        r'^(\.{0,2}/)?([\.\w]+?/)*(lib)(\w+?)\.(a|la|.*dylib)$')

    def _add_compiled_object(self, parsed_args):
        """Add parsed arguments to the compiled object list.

        The parsed arguments should be a Namespace object returned by
        argparser.ArgumentParser's parse_args() method.

        The Namespace object should contain at least both "output" and "sources"
        attributes where output is a string represented the compiled object and
        sources is a list of source paths that generate the output object.
        """
        # Determines the current directory by checking if the source exists:
        source = parsed_args.sources[0]
        current_directory = self.current_directory
        if (current_directory, source) in self.ignored_objects:
            return
        while True:
            source_path = os.path.join(current_directory, source)
            source_path = os.path.relpath(source_path)
            if os.path.isfile(source_path):
                self.current_directory = current_directory
                break
            else:
                current_directory = os.path.join(current_directory, '..')
                current_directory = os.path.relpath(current_directory)
                if current_directory == '..':
                    print("Cannot find compiled object: %r" % source_path)
                    exit(1)

        dirname = os.path.join(current_directory, parsed_args.output)
        dirname = os.path.relpath(os.path.dirname(dirname))
        parsed_args.sources[0] = source_path

        revised_include_dirs = set()
        for include_dir_arg in ['include_dirs', 'iquote']:
            include_dirs = getattr(parsed_args, include_dir_arg)
            if include_dirs is None:
                continue

            for include_dir in include_dirs:
                include_dir = os.path.join(current_directory, include_dir)
                if not os.path.isabs(include_dir):
                    include_dir = os.path.relpath(include_dir)
                revised_include_dirs.add(include_dir)
        parsed_args.include_dirs = sorted(revised_include_dirs)

        if dirname in self.compiled_objects:
            compiled_objects = self.compiled_objects[dirname]
        else:
            compiled_objects = dict()
            self.compiled_objects[dirname] = compiled_objects

        object_key = self._get_object_key(parsed_args.output)
        # Updates exisiting attributes if the compiled object already exists:
        if object_key in compiled_objects:
            compiled_object = compiled_objects[object_key]

            for attr_name in dir(parsed_args):
                attr = getattr(parsed_args, attr_name)
                if isinstance(attr, list):
                    if not hasattr(compiled_object, attr_name):
                        setattr(compiled_object, attr_name, attr)

                    compiled_attr = getattr(compiled_object, attr_name)
                    if isinstance(compiled_attr, list):
                        new_list = list(set(compiled_attr + attr))
                        setattr(compiled_object, attr_name, new_list)
        # Adds the compiled object if it's not exists in the list:
        else:
            compiled_objects[object_key] = parsed_args

    def _add_target(self, parsed_args):
        target_object_name = os.path.basename(parsed_args.output)
        target = gyp.Target(target_object_name)
        for cached_target in self.targets:
            if target.name == cached_target.name:
                target = cached_target
                break
        else:
            self.targets.append(target)

        for source_path in parsed_args.sources:
            # If the source path represents a dependency, find the corresponded
            # target instance and get the target name:
            if re.match(self.library_re, source_path):
                library_name = re.sub(self.library_re, r'lib\4', source_path)
                for cached_target in self.targets:
                    if cached_target.name == library_name:
                        target.dependencies.add(cached_target)
                        break
                else:
                    print('Error: Cannot find dependent library %r' %
                          library_name)
                    exit(1)
                continue

            # Retrieves the parsed arguments of the source by checking
            # the dictionary of compiled objects:
            dirname = os.path.join(self.current_directory,
                                   os.path.dirname(source_path))
            dirname = os.path.relpath(dirname)
            # The current source object is included in a libary and is not
            # a real object.
            if re.match(self.library_re, dirname):
                continue

            # Now we can make sure the source path is a valid source object:
            try:
                compiled_objects = self.compiled_objects[dirname]
            except KeyError:
                print('Error: Failed to add %r to target %r' %
                      (source_path, target_object_name))
                print('self.compiled_objects: %r is not in %r' %
                      (dirname, self.compiled_objects.keys()))
                exit(1)
            object_key = self._get_object_key(source_path)
            source_args = compiled_objects[object_key]
            # Adds source path:
            source_path = source_args.sources[0]
            target.sources.add(source_path)
            # Adds include dirs:
            if source_args.include_dirs is not None:
                target.include_dirs = target.include_dirs.union(
                    source_args.include_dirs)
            # Adds defines:
            if source_args.defines is not None:
                target.defines = target.defines.union(source_args.defines)
            # Add libraries:
            if hasattr(parsed_args, 'libs') and parsed_args.libs:
                target.libraries = target.libraries.union(parsed_args.libs)
            if hasattr(parsed_args, 'frameworks') and parsed_args.frameworks:
                frameworks = parsed_args.frameworks
                target.frameworks = target.frameworks.union(frameworks)
            # Adds C flags:
            target.add_cflags(vars(source_args))

    def _handle_unknown_args(self, args):
        # Determines the argument type and generates parsed arguments:
        if self.gcc_argument_parser.match_pattern(args):
            argument_parser = self.gcc_argument_parser
        elif self.archiver_argument_parser.match_pattern(args):
            argument_parser = self.archiver_argument_parser
        else:
            return  # unknown type

        parsed_args = argument_parser.parse_args(args)
        build_type = parsed_args._build_type

        if build_type == 'compile':
            self._add_compiled_object(parsed_args)
        elif build_type == 'link':
            self._add_target(parsed_args)
