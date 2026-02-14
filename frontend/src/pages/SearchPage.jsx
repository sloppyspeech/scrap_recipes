import { useState, useEffect, useCallback } from 'react';
import {
    Box, Container, SimpleGrid, Heading, Text, HStack, Button, Spinner,
    VStack, useColorModeValue, Center,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import SearchFilters from '../components/SearchFilters';
import RecipeCard from '../components/RecipeCard';
import { searchRecipes, getTags } from '../api/client';

const MotionBox = motion(Box);

export default function SearchPage() {
    const [recipes, setRecipes] = useState([]);
    const [tags, setTags] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [searchParams, setSearchParams] = useState({});

    const gradientStart = useColorModeValue('saffron.400', 'saffron.200');
    const gradientEnd = useColorModeValue('spice.500', 'spice.300');

    useEffect(() => {
        getTags().then(setTags).catch(console.error);
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
        doSearch(params, 1);
    }, [doSearch]);

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
                <Text fontSize="lg" color="gray.500">
                    Discover {total.toLocaleString()} delicious Indian recipes
                </Text>
            </MotionBox>

            {/* Search Filters */}
            <SearchFilters tags={tags} onSearch={handleSearch} />

            {/* Results */}
            {loading ? (
                <Center py={20}>
                    <VStack>
                        <Spinner size="xl" color="saffron.400" thickness="4px" />
                        <Text color="gray.500">Finding recipes...</Text>
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
                    <Text fontSize="sm" color="gray.500" mb={4}>
                        Showing {recipes.length} of {total.toLocaleString()} recipes — Page {page} of {totalPages}
                    </Text>

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
                                        colorScheme={pageNum === page ? 'saffron' : 'gray'}
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
