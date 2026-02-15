import { useState, useEffect } from 'react';
import {
    Box, Container, Heading, Text, VStack, HStack, Select, Button,
    useColorModeValue, Progress, Card, CardBody, CardHeader, Badge,
    Alert, AlertIcon, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { getModels, setModel, setEmbeddingModel, getSettings, refreshEmbeddings, getRefreshStatus } from '../api/client';

const MotionBox = motion(Box);

export default function AdminPage() {
    const [models, setModels] = useState([]);
    const [activeModel, setActiveModel] = useState('');
    const [activeEmbeddingModel, setActiveEmbeddingModel] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState({ is_indexing: false, message: 'Idle', processed: 0, total: 0 });
    const [ragStatus, setRagStatus] = useState('unknown');

    const cardBg = useColorModeValue('white', 'gray.700');

    useEffect(() => {
        loadData();
        // Poll status every 2 seconds
        const interval = setInterval(checkStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    const loadData = async () => {
        try {
            const data = await getModels();
            setModels(data.models || []);
            setActiveModel(data.active_model);
            setActiveEmbeddingModel(data.active_embedding_model);

            const settings = await getSettings();
            setRagStatus(settings.rag_status);
        } catch (err) {
            console.error(err);
        }
    };

    const checkStatus = async () => {
        try {
            const s = await getRefreshStatus();
            setStatus(s);
            if (!s.is_indexing && s.message === 'Completed') {
                // Refresh settings to show RAG is loaded
                const settings = await getSettings();
                setRagStatus(settings.rag_status);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleModelChange = async (e) => {
        const newModel = e.target.value;
        setLoading(true);
        try {
            await setModel(newModel);
            setActiveModel(newModel);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleEmbeddingModelChange = async (e) => {
        const newModel = e.target.value;
        setLoading(true);
        try {
            await setEmbeddingModel(newModel);
            setActiveEmbeddingModel(newModel);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = async () => {
        try {
            await refreshEmbeddings();
            checkStatus(); // Immediate check
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <Container maxW="7xl" py={8}>
            <Heading mb={8}>⚙️ Admin Dashboard</Heading>

            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={8}>
                {/* AI Configuration */}
                <Card bg={cardBg} shadow="lg" borderRadius="xl">
                    <CardHeader pb={0}>
                        <Heading size="md">🤖 AI Configuration</Heading>
                    </CardHeader>
                    <CardBody>
                        <VStack spacing={6} align="stretch">
                            <Box>
                                <Text mb={2} fontWeight="bold">Active Chat Model</Text>
                                <Select
                                    value={activeModel}
                                    onChange={handleModelChange}
                                    isDisabled={loading}
                                    mb={2}
                                >
                                    {models.map(m => (
                                        <option key={m.name} value={m.name}>
                                            {m.name} ({Math.round(m.size / 1024 / 1024 / 1024 * 10) / 10} GB)
                                        </option>
                                    ))}
                                </Select>
                                <Text fontSize="sm" color="gray.500">
                                    Used for scaling, summarization, and smart search answers.
                                </Text>
                            </Box>

                            <Box>
                                <Text mb={2} fontWeight="bold">Embedding Model</Text>
                                <Select
                                    value={activeEmbeddingModel}
                                    onChange={handleEmbeddingModelChange}
                                    isDisabled={loading || status.is_indexing}
                                    mb={2}
                                >
                                    {models.map(m => (
                                        <option key={m.name} value={m.name}>
                                            {m.name}
                                        </option>
                                    ))}
                                </Select>
                                <Text fontSize="sm" color="gray.500">
                                    Used for RAG vector generation. Changing this requires re-indexing.
                                </Text>
                            </Box>
                        </VStack>
                    </CardBody>
                </Card>

                {/* RAG Status */}
                <Card bg={cardBg} shadow="lg" borderRadius="xl">
                    <CardHeader pb={0}>
                        <Heading size="md">📚 RAG Search Index</Heading>
                    </CardHeader>
                    <CardBody>
                        <VStack spacing={6} align="stretch">
                            <HStack justify="space-between">
                                <Text fontWeight="bold">Index Status:</Text>
                                <Badge
                                    colorScheme={ragStatus === 'loaded' ? 'green' : 'red'}
                                    fontSize="0.9em"
                                    px={2}
                                    borderRadius="full"
                                >
                                    {ragStatus === 'loaded' ? 'Active' : 'Not Loaded'}
                                </Badge>
                            </HStack>

                            <Box>
                                <HStack justify="space-between" mb={2}>
                                    <Text fontWeight="bold">Refresh Index</Text>
                                    {status.is_indexing && (
                                        <Text fontSize="sm" color="blue.500">
                                            {status.message}
                                        </Text>
                                    )}
                                </HStack>

                                {status.is_indexing ? (
                                    <Box mb={4}>
                                        <Progress
                                            value={(status.processed / status.total) * 100}
                                            size="lg"
                                            colorScheme="blue"
                                            hasStripe
                                            isAnimated
                                            borderRadius="full"
                                        />
                                        <Text fontSize="xs" mt={1} textAlign="right">
                                            {status.processed} / {status.total} recipes
                                        </Text>
                                    </Box>
                                ) : (
                                    <Button
                                        colorScheme="blue"
                                        onClick={handleRefresh}
                                        width="full"
                                    >
                                        Start Re-indexing
                                    </Button>
                                )}

                                <Alert status="info" mt={4} borderRadius="md" fontSize="sm">
                                    <AlertIcon />
                                    Re-indexing will process all recipes using the selected embedding model. This may take a few minutes.
                                </Alert>
                            </Box>
                        </VStack>
                    </CardBody>
                </Card>
            </SimpleGrid>
        </Container>
    );
}
