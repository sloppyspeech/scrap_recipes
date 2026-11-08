import { useState, useEffect, useCallback } from 'react';
import {
    Box, Container, Heading, Text, VStack, Input, Table, Thead, Tbody, Tr, Th, Td,
    Button, HStack, Spinner, useColorModeValue, Badge, InputGroup, InputLeftElement
} from '@chakra-ui/react';
import { searchIngredients } from '../api/client';

export default function CaloriesPage() {
    const [query, setQuery] = useState('');
    const [ingredients, setIngredients] = useState([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const pageSize = 20;

    const doSearch = useCallback(async (q, p) => {
        setLoading(true);
        try {
            const data = await searchIngredients({ q, page: p, page_size: pageSize });
            setIngredients(data.ingredients);
            setTotal(data.total);
            setPage(data.page);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [pageSize]);

    useEffect(() => {
        // Initial load
        doSearch('', 1);
    }, [doSearch]);

    const handleSearch = (e) => {
        e.preventDefault();
        doSearch(query, 1);
    };

    const handlePageChange = (newPage) => {
        doSearch(query, newPage);
    };

    const gradientStart = useColorModeValue('saffron.400', 'saffron.200');
    const gradientEnd = useColorModeValue('spice.500', 'spice.300');
    const cardBg = useColorModeValue('white', 'gray.700');

    return (
        <Container maxW="7xl" py={6}>
            <VStack spacing={6} align="stretch">
                <Box textAlign="center" mb={4}>
                    <Heading
                        size="xl"
                        bgGradient={`linear(to-r, ${gradientStart}, ${gradientEnd})`}
                        bgClip="text"
                        mb={2}
                    >
                        🍎 Calorie Lookup
                    </Heading>
                    <Text color="gray.500">
                        Check calories for common Indian ingredients
                    </Text>
                </Box>

                <form onSubmit={handleSearch}>
                    <HStack>
                        <InputGroup size="lg">
                            <InputLeftElement pointerEvents="none" children="🔍" />
                            <Input
                                placeholder="Search ingredients (e.g. Rice, Onion)..."
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                bg={cardBg}
                            />
                        </InputGroup>
                        <Button type="submit" size="lg" colorScheme="saffron" px={8}>
                            Search
                        </Button>
                    </HStack>
                </form>

                <Box bg={cardBg} borderRadius="lg" boxShadow="sm" overflowX="auto">
                    <Table variant="simple">
                        <Thead>
                            <Tr>
                                <Th>Ingredient</Th>
                                <Th>Original Name</Th>
                                <Th isNumeric>Calories</Th>
                                <Th>Quantity</Th>
                                <Th>Category</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {loading ? (
                                <Tr>
                                    <Td colSpan={5} textAlign="center" py={10}>
                                        <Spinner color="saffron.500" />
                                    </Td>
                                </Tr>
                            ) : ingredients.length === 0 ? (
                                <Tr>
                                    <Td colSpan={5} textAlign="center" py={10}>
                                        No ingredients found.
                                    </Td>
                                </Tr>
                            ) : (
                                ingredients.map((ing) => (
                                    <Tr key={ing.id}>
                                        <Td fontWeight="bold">{ing.clean_name}</Td>
                                        <Td fontSize="sm" color="gray.500">{ing.original_name}</Td>
                                        <Td isNumeric fontWeight="bold" color="green.500">
                                            {ing.calories}
                                        </Td>
                                        <Td>{ing.quantity}</Td>
                                        <Td>
                                            <Badge colorScheme="purple">{ing.category}</Badge>
                                        </Td>
                                    </Tr>
                                ))
                            )}
                        </Tbody>
                    </Table>
                </Box>

                {/* Pagination */}
                {total > pageSize && (
                    <HStack justify="center" spacing={4} pt={4}>
                        <Button
                            onClick={() => handlePageChange(page - 1)}
                            isDisabled={page <= 1}
                            size="sm"
                        >
                            Previous
                        </Button>
                        <Text fontSize="sm">
                            Page {page} of {Math.ceil(total / pageSize)}
                        </Text>
                        <Button
                            onClick={() => handlePageChange(page + 1)}
                            isDisabled={page >= Math.ceil(total / pageSize)}
                            size="sm"
                        >
                            Next
                        </Button>
                    </HStack>
                )}
            </VStack>
        </Container>
    );
}
