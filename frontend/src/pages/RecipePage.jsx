import { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
    Box, Container, Heading, Text, VStack, HStack, Badge, Button,
    Divider, Table, Thead, Tbody, Tr, Th, Td, TableContainer,
    Spinner, Alert, AlertIcon, useColorModeValue, Center,
    Breadcrumb, BreadcrumbItem, BreadcrumbLink, Tabs, TabList,
    TabPanels, Tab, TabPanel, Link, Skeleton, SkeletonText,
} from '@chakra-ui/react';
import { ChevronRightIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';
import { getRecipe, summarizeRecipe } from '../api/client';
import NutrientBadges from '../components/NutrientBadges';
import ScalingPanel from '../components/ScalingPanel';

const MotionBox = motion(Box);

export default function RecipePage() {
    const { id } = useParams();
    const [recipe, setRecipe] = useState(null);
    const [loading, setLoading] = useState(true);
    const [summary, setSummary] = useState(null);
    const [summaryLoading, setSummaryLoading] = useState(false);
    const [summaryError, setSummaryError] = useState(null);

    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');
    const tableBg = useColorModeValue('orange.50', 'whiteAlpha.50');

    useEffect(() => {
        setLoading(true);
        getRecipe(id)
            .then(setRecipe)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [id]);

    const handleSummarize = async () => {
        setSummaryLoading(true);
        setSummaryError(null);
        try {
            const result = await summarizeRecipe(id);
            setSummary(result);
        } catch (err) {
            setSummaryError(err.response?.data?.detail || 'Summarization failed. Is Ollama running?');
        } finally {
            setSummaryLoading(false);
        }
    };

    if (loading) {
        return (
            <Container maxW="5xl" py={8}>
                <VStack spacing={4} align="stretch">
                    <Skeleton height="40px" width="60%" />
                    <SkeletonText noOfLines={4} />
                    <Skeleton height="200px" />
                </VStack>
            </Container>
        );
    }

    if (!recipe) {
        return (
            <Container maxW="5xl" py={8}>
                <Alert status="error" borderRadius="lg">
                    <AlertIcon />
                    Recipe not found.
                </Alert>
            </Container>
        );
    }

    const times = recipe.times || {};
    const timeEntries = Object.entries(times).filter(([k, v]) => v);

    return (
        <Container maxW="5xl" py={6}>
            {/* Breadcrumb */}
            <Breadcrumb separator={<ChevronRightIcon color="gray.500" />} mb={4}>
                <BreadcrumbItem>
                    <BreadcrumbLink as={RouterLink} to="/" color="saffron.400">
                        Recipes
                    </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbItem isCurrentPage>
                    <BreadcrumbLink>{recipe.name}</BreadcrumbLink>
                </BreadcrumbItem>
            </Breadcrumb>

            <MotionBox
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
            >
                {/* Header */}
                <VStack align="stretch" spacing={4} mb={6}>
                    <Heading size="xl" fontFamily="heading">
                        {recipe.name}
                    </Heading>

                    <HStack spacing={3} flexWrap="wrap">
                        {recipe.calories && (
                            <Badge colorScheme="orange" fontSize="sm" px={3} py={1} borderRadius="full">
                                🔥 {recipe.calories}
                            </Badge>
                        )}
                        {recipe.makes && (
                            <Badge colorScheme="purple" fontSize="sm" px={3} py={1} borderRadius="full">
                                🍽️ {recipe.makes}
                            </Badge>
                        )}
                        <Link href={recipe.url} isExternal color="saffron.400" fontSize="sm">
                            View Original <ExternalLinkIcon mx="2px" />
                        </Link>
                    </HStack>

                    {/* Tags */}
                    {recipe.tags && recipe.tags.length > 0 && (
                        <HStack spacing={1} flexWrap="wrap">
                            {recipe.tags.map(tag => (
                                <Badge key={tag} variant="outline" colorScheme="saffron" borderRadius="full" px={2}>
                                    {tag}
                                </Badge>
                            ))}
                        </HStack>
                    )}
                </VStack>

                {/* Tabs */}
                <Tabs colorScheme="saffron" variant="enclosed-colored">
                    <TabList>
                        <Tab>📋 Details</Tab>
                        <Tab>🤖 AI Summary</Tab>
                        <Tab>⚖️ Scale</Tab>
                    </TabList>

                    <TabPanels>
                        {/* Details Tab */}
                        <TabPanel px={0} pt={4}>
                            <VStack spacing={6} align="stretch">
                                {/* Times */}
                                {timeEntries.length > 0 && (
                                    <Box bg={bg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} shadow="sm">
                                        <Text fontWeight="bold" mb={3} fontSize="lg">⏱️ Times</Text>
                                        <SimpleGridTimes entries={timeEntries} />
                                    </Box>
                                )}

                                {/* Ingredients */}
                                <Box bg={bg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} shadow="sm">
                                    <Text fontWeight="bold" mb={3} fontSize="lg">
                                        🥘 Ingredients ({recipe.ingredients?.length || 0})
                                    </Text>
                                    <TableContainer>
                                        <Table size="sm" variant="simple">
                                            <Thead>
                                                <Tr bg={tableBg}>
                                                    <Th>Ingredient</Th>
                                                    <Th>Quantity</Th>
                                                </Tr>
                                            </Thead>
                                            <Tbody>
                                                {recipe.ingredients?.map((ing, i) => (
                                                    <Tr key={i} _hover={{ bg: tableBg }}>
                                                        <Td fontWeight="500">{ing.name}</Td>
                                                        <Td>
                                                            <Badge colorScheme="saffron" variant="subtle">
                                                                {ing.quantity || '—'}
                                                            </Badge>
                                                        </Td>
                                                    </Tr>
                                                ))}
                                            </Tbody>
                                        </Table>
                                    </TableContainer>
                                </Box>

                                {/* Nutrients */}
                                {recipe.nutrient_values && Object.keys(recipe.nutrient_values).length > 0 && (
                                    <Box bg={bg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} shadow="sm">
                                        <Text fontWeight="bold" mb={3} fontSize="lg">🧪 Nutrition</Text>
                                        <NutrientBadges nutrients={recipe.nutrient_values} />
                                    </Box>
                                )}
                            </VStack>
                        </TabPanel>

                        {/* AI Summary Tab */}
                        <TabPanel px={0} pt={4}>
                            <Box bg={bg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} shadow="sm">
                                {!summary && !summaryLoading && (
                                    <VStack py={8}>
                                        <Text fontSize="4xl">🤖</Text>
                                        <Text color="gray.500" mb={4}>
                                            Use AI to summarize this recipe from its source page
                                        </Text>
                                        <Button
                                            colorScheme="saffron"
                                            size="lg"
                                            onClick={handleSummarize}
                                        >
                                            Generate AI Summary
                                        </Button>
                                    </VStack>
                                )}

                                {summaryLoading && (
                                    <Center py={8}>
                                        <VStack>
                                            <Spinner size="xl" color="saffron.400" thickness="4px" />
                                            <Text color="gray.500">AI is reading and summarizing the recipe...</Text>
                                            <Text fontSize="sm" color="gray.400">This may take 30-60 seconds</Text>
                                        </VStack>
                                    </Center>
                                )}

                                {summaryError && (
                                    <Alert status="error" borderRadius="lg" mb={4}>
                                        <AlertIcon />
                                        {summaryError}
                                    </Alert>
                                )}

                                {summary && (
                                    <VStack align="stretch" spacing={3}>
                                        <HStack justify="space-between">
                                            <Text fontWeight="bold" fontSize="lg">AI Summary</Text>
                                            <Badge colorScheme="blue" variant="subtle">
                                                🤖 {summary.model}
                                            </Badge>
                                        </HStack>
                                        <Divider />
                                        <Box
                                            whiteSpace="pre-wrap"
                                            fontSize="md"
                                            lineHeight="1.8"
                                            dangerouslySetInnerHTML={{
                                                __html: summary.summary
                                                    .replace(/###\s(.*)/g, '<strong>$1</strong>')
                                                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                                    .replace(/\n/g, '<br/>')
                                            }}
                                        />
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            colorScheme="saffron"
                                            onClick={handleSummarize}
                                            mt={2}
                                        >
                                            🔄 Regenerate
                                        </Button>
                                    </VStack>
                                )}
                            </Box>
                        </TabPanel>

                        {/* Scale Tab */}
                        <TabPanel px={0} pt={4}>
                            <ScalingPanel
                                recipeId={recipe.id}
                                ingredients={recipe.ingredients || []}
                                makes={recipe.makes}
                            />
                        </TabPanel>
                    </TabPanels>
                </Tabs>
            </MotionBox>
        </Container>
    );
}

/* Helper: Simple grid for time entries */
function SimpleGridTimes({ entries }) {
    const labelMap = {
        soaking_time: '🫧 Soaking',
        preparation_time: '⏱️ Prep',
        cooking_time: '🔥 Cooking',
        baking_time: '🥖 Baking',
        baking_temperature: '🌡️ Bake Temp',
        sprouting_time: '🌱 Sprouting',
        total_time: '⏰ Total',
    };

    return (
        <HStack spacing={4} flexWrap="wrap">
            {entries.map(([key, value]) => (
                <Badge key={key} px={3} py={2} borderRadius="lg" variant="subtle" colorScheme="teal" fontSize="sm">
                    {labelMap[key] || key}: {value}
                </Badge>
            ))}
        </HStack>
    );
}
