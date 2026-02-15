import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
    Box, Container, SimpleGrid, Heading, Text, HStack, Button, Spinner,
    VStack, useColorModeValue, Center, Textarea, Badge, FormControl,
    FormLabel, Switch, Icon, Divider
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import SearchFilters from '../components/SearchFilters';
import RecipeCard from '../components/RecipeCard';
import { searchRecipes, searchRecipesNatural, getTags, getCategories } from '../api/client';

const MotionBox = motion(Box);

export default function SearchPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const [recipes, setRecipes] = useState([]);
    const [tags, setTags] = useState([]);
    const [categories, setCategories] = useState([]);
    const [pageSize, setPageSize] = useState(20);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [searchParams, setSearchParams] = useState({});

    const [isSmartMode, setIsSmartMode] = useState(false);
    const [smartQuery, setSmartQuery] = useState('');

    const gradientStart = useColorModeValue('saffron.400', 'saffron.200');
    const gradientEnd = useColorModeValue('spice.500', 'spice.300');
    const inputBg = useColorModeValue('white', 'gray.700');

    useEffect(() => {
        getTags().then(setTags).catch(console.error);
        getCategories().then(setCategories).catch(console.error);
        // Initial load - classic search
        doSearch({}, 1, 20);
    }, []);

    const doSearch = useCallback(async (params, pageNum = 1, pSize = pageSize) => {
        setLoading(true);
        try {
            // Check if we are in smart mode or if this is a classic search
            // If params are empty and smartQuery is set, it might be a smart search pagination
            if (isSmartMode && smartQuery) {
                const result = await searchRecipesNatural(smartQuery, { page: pageNum, page_size: pSize });
                setRecipes(result.results.recipes);
                setTotal(result.results.total);
            } else {
                const result = await searchRecipes({ ...params, page: pageNum, page_size: pSize });
                setRecipes(result.recipes);
                setTotal(result.total);
            }
            setPage(pageNum);
            setSearchParams(params);
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setLoading(false);
        }
    }, [pageSize, isSmartMode, smartQuery]);

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        if (params.get('reset') === 'true') {
            setIsSmartMode(false);
            setSmartQuery('');
            setRecipes([]);
            setTotal(0);
            setPage(1);
            setSearchParams({});

            // Explicitly run default classic search to avoid stale state in doSearch
            setLoading(true);
            searchRecipes({ page: 1, page_size: 20 })
                .then(result => {
                    setRecipes(result.recipes);
                    setTotal(result.total);
                })
                .catch(err => console.error('Reset search failed:', err))
                .finally(() => setLoading(false));

            navigate('/', { replace: true });
        }
    }, [location.search, navigate]);

    const handleSearch = useCallback((params) => {
        doSearch(params, 1, pageSize);
    }, [doSearch, pageSize]);

    const handleSmartSearch = async () => {
        if (!smartQuery.trim()) return;
        doSearch({}, 1, pageSize);
    };

    const handlePageChange = (newPage) => {
        doSearch(searchParams, newPage, pageSize);
    };

    const handlePageSizeChange = (e) => {
        const newSize = parseInt(e.target.value);
        setPageSize(newSize);
        doSearch(searchParams, 1, newSize);
    };

    const totalPages = Math.ceil(total / pageSize);

    return (
        <Container maxW="7xl" py={6}>
            {/* Hero Section */}
            <MotionBox
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                textAlign="center"
                mb={8}
            >
                <Heading
                    size="2xl"
                    bgGradient={`linear(to-r, ${gradientStart}, ${gradientEnd})`}
                    bgClip="text"
                    fontFamily="heading"
                    mb={2}
                >
                    🍛 Recipe Browser
                </Heading>
                <Text fontSize="lg" color="gray.500" mb={6}>
                    Discover {total > 0 ? total.toLocaleString() : 'thousands of'} delicious Indian recipes
                </Text>

                {/* Mode Toggle */}
                <Center mb={8}>
                    <HStack
                        bg={useColorModeValue('gray.100', 'gray.700')}
                        p={1}
                        borderRadius="full"
                        spacing={0}
                    >
                        <Button
                            variant={!isSmartMode ? 'solid' : 'ghost'}
                            colorScheme={!isSmartMode ? 'saffron' : 'gray'}
                            borderRadius="full"
                            size="sm"
                            px={6}
                            onClick={() => { setIsSmartMode(false); setRecipes([]); setTotal(0); }}
                        >
                            Classic Search
                        </Button>
                        <Button
                            variant={isSmartMode ? 'solid' : 'ghost'}
                            colorScheme={isSmartMode ? 'purple' : 'gray'}
                            borderRadius="full"
                            size="sm"
                            px={6}
                            onClick={() => { setIsSmartMode(true); setRecipes([]); setTotal(0); }}
                        >
                            ✨ Smart AI Search
                        </Button>
                    </HStack>
                </Center>
            </MotionBox>

            {/* Search Interface */}
            {isSmartMode ? (
                <MotionBox
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    mb={10}
                >
                    <VStack spacing={4} maxW="3xl" mx="auto">
                        <Textarea
                            value={smartQuery}
                            onChange={(e) => setSmartQuery(e.target.value)}
                            placeholder="Ask me anything! e.g. 'I want a high protein breakfast with eggs'..."
                            size="lg"
                            minH="100px"
                            bg={inputBg}
                            fontSize="lg"
                            borderRadius="xl"
                            boxShadow="md"
                            _focus={{ borderColor: 'purple.400', boxShadow: '0 0 0 1px var(--chakra-colors-purple-400)' }}
                        />
                        <Button
                            colorScheme="purple"
                            size="lg"
                            w="full"
                            onClick={handleSmartSearch}
                            isLoading={loading}
                            loadingText="Thinking..."
                            rightIcon={<span>✨</span>}
                        >
                            Ask AI
                        </Button>


                    </VStack>
                </MotionBox>
            ) : (
                <SearchFilters tags={tags} categories={categories} onSearch={handleSearch} />
            )}

            {/* Results */}
            {loading ? (
                <Center py={20}>
                    <VStack>
                        <Spinner size="xl" color={isSmartMode ? "purple.400" : "saffron.400"} thickness="4px" />
                        <Text color="gray.500">{isSmartMode ? "Analyzing your request..." : "Finding recipes..."}</Text>
                    </VStack>
                </Center>
            ) : recipes.length === 0 ? (
                <Center py={20}>
                    <VStack>
                        <Text fontSize="5xl">🍽️</Text>
                        <Text fontSize="xl" color="gray.500">No recipes found. Try a different search!</Text>
                    </VStack>
                </Center>
            ) : (
                <>
                    <HStack justify="space-between" mb={4} flexWrap="wrap" gap={2}>
                        <Text fontSize="sm" color="gray.500">
                            Found {total > 0 ? total.toLocaleString() : 0} recipes
                        </Text>

                        <HStack>
                            <Text fontSize="sm" color="gray.500">Items per page:</Text>
                            <select
                                value={pageSize}
                                onChange={handlePageSizeChange}
                                style={{
                                    padding: '4px',
                                    borderRadius: '4px',
                                    border: '1px solid #CBD5E0'
                                }}
                            >
                                <option value="10">10</option>
                                <option value="20">20</option>
                                <option value="50">50</option>
                            </select>
                            {total > pageSize && (
                                <Text fontSize="sm" color="gray.500" ml={4}>
                                    Page {page} of {totalPages}
                                </Text>
                            )}
                        </HStack>
                    </HStack>

                    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={5}>
                        {recipes.map((recipe, i) => (
                            <RecipeCard key={recipe.id} recipe={recipe} index={i} />
                        ))}
                    </SimpleGrid>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <HStack justify="center" mt={8} spacing={2}>
                            <Button
                                size="sm"
                                variant="outline"
                                isDisabled={page <= 1}
                                onClick={() => handlePageChange(page - 1)}
                            >
                                ← Previous
                            </Button>

                            {[...Array(Math.min(5, totalPages))].map((_, i) => {
                                // Logic to show window around current page
                                let startPage = Math.max(1, page - 2);
                                if (startPage + 4 > totalPages) {
                                    startPage = Math.max(1, totalPages - 4);
                                }
                                const pageNum = startPage + i;

                                if (pageNum > totalPages) return null;
                                return (
                                    <Button
                                        key={pageNum}
                                        size="sm"
                                        variant={pageNum === page ? 'solid' : 'outline'}
                                        colorScheme={pageNum === page ? (isSmartMode ? 'purple' : 'saffron') : 'gray'}
                                        onClick={() => handlePageChange(pageNum)}
                                    >
                                        {pageNum}
                                    </Button>
                                );
                            })}

                            <Button
                                size="sm"
                                variant="outline"
                                isDisabled={page >= totalPages}
                                onClick={() => handlePageChange(page + 1)}
                            >
                                Next →
                            </Button>
                        </HStack>
                    )}
                </>
            )}
        </Container>
    );
}
