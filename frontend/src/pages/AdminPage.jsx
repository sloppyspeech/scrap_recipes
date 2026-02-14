import { useState, useEffect } from 'react';
import {
    Container, Heading, VStack, HStack, Box, Text, Select, Button, Badge,
    useColorModeValue, useColorMode, Switch, FormControl, FormLabel,
    Alert, AlertIcon, Spinner, Divider, Table, Thead, Tbody, Tr, Th, Td,
    TableContainer, Card, CardBody, CardHeader, IconButton, Tooltip,
} from '@chakra-ui/react';
import { SunIcon, MoonIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';
import { getModels, setModel, getSettings } from '../api/client';

const MotionBox = motion(Box);

export default function AdminPage() {
    const { colorMode, toggleColorMode } = useColorMode();
    const [models, setModels] = useState([]);
    const [activeModel, setActiveModel] = useState('');
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        setLoading(true);
        try {
            const [modelsData, settingsData] = await Promise.all([
                getModels(),
                getSettings(),
            ]);
            setModels(modelsData.models || []);
            setActiveModel(settingsData.active_model || '');
        } catch (err) {
            setError('Failed to load settings. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    const handleModelChange = async (modelName) => {
        setSaving(true);
        setSuccess(null);
        setError(null);
        try {
            const result = await setModel(modelName);
            setActiveModel(result.active_model);
            setSuccess(`Model changed to ${result.active_model}`);
            setTimeout(() => setSuccess(null), 3000);
        } catch (err) {
            setError('Failed to change model.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <Container maxW="4xl" py={6}>
            <MotionBox
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
            >
                <Heading size="xl" fontFamily="heading" mb={6}>
                    ⚙️ Admin Settings
                </Heading>

                <VStack spacing={6} align="stretch">
                    {/* Theme Toggle */}
                    <Card bg={bg} borderColor={borderColor} borderWidth="1px" borderRadius="xl" shadow="md">
                        <CardHeader pb={2}>
                            <Heading size="md">🎨 Appearance</Heading>
                        </CardHeader>
                        <CardBody>
                            <FormControl display="flex" alignItems="center" justifyContent="space-between">
                                <HStack>
                                    <SunIcon color={colorMode === 'light' ? 'saffron.400' : 'gray.500'} />
                                    <FormLabel mb={0} fontSize="md">
                                        {colorMode === 'dark' ? 'Dark Mode' : 'Light Mode'}
                                    </FormLabel>
                                    <MoonIcon color={colorMode === 'dark' ? 'saffron.400' : 'gray.500'} />
                                </HStack>
                                <Switch
                                    colorScheme="saffron"
                                    size="lg"
                                    isChecked={colorMode === 'dark'}
                                    onChange={toggleColorMode}
                                />
                            </FormControl>
                        </CardBody>
                    </Card>

                    {/* Model Selection */}
                    <Card bg={bg} borderColor={borderColor} borderWidth="1px" borderRadius="xl" shadow="md">
                        <CardHeader pb={2}>
                            <Heading size="md">🤖 Ollama Model</Heading>
                        </CardHeader>
                        <CardBody>
                            {loading ? (
                                <HStack>
                                    <Spinner size="sm" />
                                    <Text>Loading models...</Text>
                                </HStack>
                            ) : (
                                <VStack spacing={4} align="stretch">
                                    <HStack>
                                        <Text fontSize="sm" color="gray.500">Current model:</Text>
                                        <Badge colorScheme="blue" fontSize="sm" px={3} py={1} borderRadius="full">
                                            {activeModel}
                                        </Badge>
                                    </HStack>

                                    {models.length > 0 && !models[0]?.error ? (
                                        <>
                                            <Select
                                                value={activeModel}
                                                onChange={(e) => handleModelChange(e.target.value)}
                                                variant="filled"
                                            >
                                                {models.map(m => (
                                                    <option key={m.name} value={m.name}>
                                                        {m.name} {m.size ? `(${(m.size / 1e9).toFixed(1)}GB)` : ''}
                                                    </option>
                                                ))}
                                            </Select>

                                            <Divider />

                                            <Text fontWeight="600" fontSize="sm">Available Models</Text>
                                            <TableContainer>
                                                <Table size="sm" variant="simple">
                                                    <Thead>
                                                        <Tr>
                                                            <Th>Model</Th>
                                                            <Th>Size</Th>
                                                            <Th>Modified</Th>
                                                            <Th></Th>
                                                        </Tr>
                                                    </Thead>
                                                    <Tbody>
                                                        {models.map(m => (
                                                            <Tr key={m.name}>
                                                                <Td fontWeight="500">
                                                                    {m.name}
                                                                    {m.name === activeModel && (
                                                                        <Badge ml={2} colorScheme="green" variant="subtle">Active</Badge>
                                                                    )}
                                                                </Td>
                                                                <Td>{m.size ? `${(m.size / 1e9).toFixed(1)} GB` : '—'}</Td>
                                                                <Td fontSize="xs" color="gray.500">
                                                                    {m.modified_at ? new Date(m.modified_at).toLocaleDateString() : '—'}
                                                                </Td>
                                                                <Td>
                                                                    <Button
                                                                        size="xs"
                                                                        colorScheme="saffron"
                                                                        variant={m.name === activeModel ? 'solid' : 'outline'}
                                                                        onClick={() => handleModelChange(m.name)}
                                                                        isLoading={saving}
                                                                    >
                                                                        {m.name === activeModel ? 'Active' : 'Use'}
                                                                    </Button>
                                                                </Td>
                                                            </Tr>
                                                        ))}
                                                    </Tbody>
                                                </Table>
                                            </TableContainer>
                                        </>
                                    ) : (
                                        <Alert status="warning" borderRadius="lg">
                                            <AlertIcon />
                                            Could not connect to Ollama. Make sure it's running on port 11435.
                                        </Alert>
                                    )}
                                </VStack>
                            )}
                        </CardBody>
                    </Card>

                    {/* Alerts */}
                    {error && (
                        <Alert status="error" borderRadius="lg">
                            <AlertIcon />
                            {error}
                        </Alert>
                    )}
                    {success && (
                        <Alert status="success" borderRadius="lg">
                            <AlertIcon />
                            {success}
                        </Alert>
                    )}
                </VStack>
            </MotionBox>
        </Container>
    );
}
