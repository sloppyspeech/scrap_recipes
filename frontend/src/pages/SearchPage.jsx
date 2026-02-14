import { useState, useEffect, useCallback } from 'react';
import {
    Box, Container, SimpleGrid, Heading, Text, HStack, Button, Spinner,
    VStack, useColorModeValue, Center, Textarea, Badge, FormControl,
    FormLabel, Switch, Icon, Divider
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import SearchFilters from '../components/SearchFilters';
import RecipeCard from '../components/RecipeCard';
import { searchRecipes, searchRecipesNatural, getTags } from '../api/client';

const MotionBox = motion(Box);

export default function SearchPage() {
    const [recipes, setRecipes] = useState([]);
    const [tags, setTags] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [searchParams, setSearchParams] = useState({});

    // Smart Search State
    const [isSmartMode, setIsSmartMode] = useState(false);
    const [smartQuery, setSmartQuery] = useState('');
    const [inferredFilters, setInferredFilters] = useState(null);

    const gradientStart = useColorModeValue('saffron.400', 'saffron.200');
    const gradientEnd = useColorModeValue('spice.500', 'spice.300');
    const inputBg = useColorModeValue('white', 'gray.700');

    useEffect(() => {
        getTags().then(setTags).catch(console.error);
        // Initial load - classic search
        doSearch({});
    }, []);

    const doSearch = useCallback(async (params, pageNum = 1) => {
        setLoading(true);
        try {
            const result = await searchRecipes({ ...params, page: pageNum, page_size: 20 });
            setRecipes(result.recipes);
            setTotal(result.total);
            setPage(pageNum);
            setSearchParams(params);
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleSearch = useCallback((params) => {
        setInferredFilters(null); // Clear smart filters if using classic
        doSearch(params, 1);
    }, [doSearch]);

    const handleSmartSearch = async () => {
        if (!smartQuery.trim()) return;
        setLoading(true);
        try {
            const result = await searchRecipesNatural(smartQuery);
            setRecipes(result.results.recipes);
            setTotal(result.results.total);
            setPage(1);
            setInferredFilters(result.inferred_filters);
            setSearchParams(result.inferred_filters); // Enable pagination using these filters
        } catch (err) {
            console.error('Smart search failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const totalPages = Math.ceil(total / 20);

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
                            onClick={() => setIsSmartMode(false)}
                        >
                            Classic Search
                        </Button>
                        <Button
                            variant={isSmartMode ? 'solid' : 'ghost'}
                            colorScheme={isSmartMode ? 'purple' : 'gray'}
                            borderRadius="full"
                            size="sm"
                            px={6}
                            onClick={() => setIsSmartMode(true)}
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
                            placeholder="Describe what you want: e.g. 'Spicy dosa without rice under 300 calories'..."
                            size="lg"
                            minH="120px"
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
                            loadingText="Asking AI..."
                            rightIcon={<span>✨</span>}
                        >
                            Find Recipes
                        </Button>

                        {inferredFilters && (
                            <Box
                                w="full"
                                p={4}
                                bg={useColorModeValue('purple.50', 'whiteAlpha.100')}
                                borderRadius="lg"
                                border="1px dashed"
                                borderColor="purple.200"
                            >
                                <Text fontSize="xs" fontWeight="bold" textTransform="uppercase" color="purple.500" mb={2}>
                                    AI Understood:
                                </Text>
                                <HStack flexWrap="wrap" spacing={2}>
                                    {inferredFilters.q && (
                                        <Badge colorScheme="blue" borderRadius="full" px={3} py={1}>
                                            Search: "{inferredFilters.q}"
                                        </Badge>
                                    )}
                                    {inferredFilters.include_ingredients?.map(ing => (
                                        <Badge key={`inc-${ing}`} colorScheme="green" borderRadius="full" px={3} py={1}>
                                            + {ing}
                                        </Badge>
                                    ))}
                                    {inferredFilters.exclude_ingredients?.map(ing => (
                                        <Badge key={`exc-${ing}`} colorScheme="red" borderRadius="full" px={3} py={1}>
                                            🚫 No {ing}
                                        </Badge>
                                    ))}
                                    {inferredFilters.cal_max && (
                                        <Badge colorScheme="orange" borderRadius="full" px={3} py={1}>
                                            &lt; {inferredFilters.cal_max} cal
                                        </Badge>
                                    )}
                                    {inferredFilters.tag && (
                                        <Badge colorScheme="purple" borderRadius="full" px={3} py={1}>
                                            Tag: {inferredFilters.tag}
                                        </Badge>
                                    )}
                                </HStack>
                            </Box>
                        )}
                    </VStack>
                </MotionBox>
            ) : (
                <SearchFilters tags={tags} onSearch={handleSearch} />
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
                    <HStack justify="space-between" mb={4}>
                        <Text fontSize="sm" color="gray.500">
                            Found {total.toLocaleString()} recipes
                        </Text>
                        {total > 20 && (
                            <Text fontSize="sm" color="gray.500">
                                Page {page} of {totalPages}
                            </Text>
                        )}
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
                                onClick={() => doSearch(searchParams, page - 1)}
                            >
                                ← Previous
                            </Button>

                            {[...Array(Math.min(5, totalPages))].map((_, i) => {
                                const pageNum = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
                                if (pageNum > totalPages) return null;
                                return (
                                    <Button
                                        key={pageNum}
                                        size="sm"
                                        variant={pageNum === page ? 'solid' : 'outline'}
                                        colorScheme={pageNum === page ? (isSmartMode ? 'purple' : 'saffron') : 'gray'}
                                        onClick={() => doSearch(searchParams, pageNum)}
                                    >
                                        {pageNum}
                                    </Button>
                                );
                            })}

                            <Button
                                size="sm"
                                variant="outline"
                                isDisabled={page >= totalPages}
                                onClick={() => doSearch(searchParams, page + 1)}
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
