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
                'util.c',
                'write_read.c',
            ],
            'dependencies': [
                'gyp_deps/libvorbis/libvorbis.gyp:libvorbisenc',
            ],
        },
    ],
}