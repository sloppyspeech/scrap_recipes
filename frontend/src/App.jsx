import { ChakraProvider, Box, Flex, HStack, Button, useColorMode, useColorModeValue, IconButton, Heading } from '@chakra-ui/react';
import { BrowserRouter, Routes, Route, Link as RouterLink, useLocation } from 'react-router-dom';
import { SunIcon, MoonIcon } from '@chakra-ui/icons';
import { motion, AnimatePresence } from 'framer-motion';
import theme from './theme';
import SearchPage from './pages/SearchPage';
import RecipePage from './pages/RecipePage';
import AdminPage from './pages/AdminPage';

function NavBar() {
  const { colorMode, toggleColorMode } = useColorMode();
  const bg = useColorModeValue('whiteAlpha.900', 'blackAlpha.700');
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <Box
      as="nav"
      position="sticky"
      top={0}
      zIndex={100}
      bg={bg}
      backdropFilter="blur(15px)"
      borderBottom="1px solid"
      borderColor={useColorModeValue('gray.200', 'whiteAlpha.100')}
      shadow="sm"
    >
      <Flex maxW="7xl" mx="auto" px={4} py={3} justify="space-between" align="center">
        <HStack spacing={6}>
          <Heading
            as={RouterLink}
            to="/?reset=true"
            size="md"
            fontFamily="heading"
            bgGradient="linear(to-r, saffron.400, spice.400)"
            bgClip="text"
            _hover={{ transform: 'scale(1.05)' }}
            transition="transform 0.2s"
            onClick={() => {
              if (window.location.search.includes('reset=true')) {
                // Force reload if already on reset page to ensure state clears
                window.location.href = '/?reset=true';
              }
            }}
          >
            🍛 RecipeLens
          </Heading>
          <HStack spacing={1}>
            <Button
              as={RouterLink}
              to="/"
              variant={isActive('/') ? 'solid' : 'ghost'}
              colorScheme={isActive('/') ? 'saffron' : 'gray'}
              size="sm"
              borderRadius="full"
            >
              Search
            </Button>
            <Button
              as={RouterLink}
              to="/admin"
              variant={isActive('/admin') ? 'solid' : 'ghost'}
              colorScheme={isActive('/admin') ? 'saffron' : 'gray'}
              size="sm"
              borderRadius="full"
            >
              ⚙️ Admin
            </Button>
          </HStack>
        </HStack>

        <IconButton
          icon={colorMode === 'dark' ? <SunIcon /> : <MoonIcon />}
          onClick={toggleColorMode}
          variant="ghost"
          colorScheme="saffron"
          borderRadius="full"
          aria-label="Toggle color mode"
        />
      </Flex>
    </Box>
  );
}

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
      >
        <Routes location={location}>
          <Route path="/" element={<SearchPage />} />
          <Route path="/recipe/:id" element={<RecipePage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <ChakraProvider theme={theme}>
      <BrowserRouter>
        <Box minH="100vh">
          <NavBar />
          <AnimatedRoutes />
        </Box>
      </BrowserRouter>
    </ChakraProvider>
  );
}
