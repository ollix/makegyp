{
    'includes': [
        '../common.gypi',
    ],
    'targets': [
        {
            'target_name': 'test',
            'type': 'executable',
            'sources': [
                'test.c',
            ],
            'dependencies': [
                'gyp_deps/mpg123/mpg123.gyp:libmpg123',
            ],
        },
    ],
}