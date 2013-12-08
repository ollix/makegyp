{
    'includes': [
        '../common.gypi',
    ],
    'targets': [
        {
            'target_name': 'test',
            'type': 'executable',
            'sources': [
                'test.cc',
                'unittest.cc'
            ],
            'dependencies': [
                'gyp_deps/gtest/gtest.gyp:libgtest',
            ],
        },
    ],
}