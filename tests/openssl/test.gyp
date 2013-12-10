{
    "target_defaults": {
        'variables': {
            'target_arch': 'ia32',
        },
    },
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
                'gyp_deps/openssl/openssl.gyp:libcrypto',
                'gyp_deps/openssl/openssl.gyp:libssl',
            ],
        },
    ],
}