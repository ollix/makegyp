{
    "variables": {
        "target_arch%": "x64",
    },
    "target_defaults": {
        "default_configuration": "Debug",
        "configurations": {
            "Debug": {
                "defines": [
                    "DEBUG",
                    "_DEBUG"
                ],
            },
            "Release": {
                "defines": [
                    "NDEBUG"
                ],
            },
        },  # end of configurations
        "conditions": [
            ["OS=='mac'",
                {"conditions": [
                    ["target_arch=='ia32'",
                        {"xcode_settings": {"ARCHS": ["i386"]}}
                    ],
                    ["target_arch=='x64'",
                        {"xcode_settings": {"ARCHS": ["x86_64"]}}
                    ],
                ]},
            ],  # end of OS=='mac'
        ],  # end of conditions
    },  # end of target_defaults
}
