import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
    config: {
        initialColorMode: 'dark',
        useSystemColorMode: false,
    },
    fonts: {
        heading: `'Outfit', sans-serif`,
        body: `'Inter', sans-serif`,
    },
    colors: {
        brand: {
            50: '#FFF8E7',
            100: '#FFEAB3',
            200: '#FFDC80',
            300: '#FFCE4D',
            400: '#FFC01A',
            500: '#E6A600',
            600: '#B38100',
            700: '#805C00',
            800: '#4D3700',
            900: '#1A1300',
        },
        saffron: {
            50: '#FFF3E0',
            100: '#FFE0B2',
            200: '#FFCC80',
            300: '#FFB74D',
            400: '#FFA726',
            500: '#FF9800',
            600: '#FB8C00',
            700: '#F57C00',
            800: '#EF6C00',
            900: '#E65100',
        },
        spice: {
            50: '#FBE9E7',
            100: '#FFCCBC',
            200: '#FFAB91',
            300: '#FF8A65',
            400: '#FF7043',
            500: '#FF5722',
            600: '#F4511E',
            700: '#E64A19',
            800: '#D84315',
            900: '#BF360C',
        },
    },
    styles: {
        global: (props) => ({
            body: {
                bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
                color: props.colorMode === 'dark' ? 'gray.100' : 'gray.800',
            },
        }),
    },
    components: {
        Button: {
            defaultProps: {
                colorScheme: 'saffron',
            },
        },
        Card: {
            baseStyle: (props) => ({
                container: {
                    bg: props.colorMode === 'dark' ? 'whiteAlpha.100' : 'white',
                    backdropFilter: 'blur(10px)',
                    borderColor: props.colorMode === 'dark' ? 'whiteAlpha.200' : 'gray.200',
                },
            }),
        },
    },
});

export default theme;
