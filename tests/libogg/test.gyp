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
                'gyp_deps/libogg/libogg.gyp:libogg',
            ],
        },
    ],
}