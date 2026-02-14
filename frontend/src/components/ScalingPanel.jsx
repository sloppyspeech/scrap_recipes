import { useState } from 'react';
import {
    Box, VStack, HStack, Text, NumberInput, NumberInputField, NumberInputStepper,
    NumberIncrementStepper, NumberDecrementStepper, Button, Switch, FormControl,
    FormLabel, Table, Thead, Tbody, Tr, Th, Td, TableContainer, Badge,
    useColorModeValue, Spinner, Alert, AlertIcon, Divider,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { scaleRecipe } from '../api/client';

const MotionBox = motion(Box);

export default function ScalingPanel({ recipeId, ingredients = [], makes = '' }) {
    const [targetServings, setTargetServings] = useState(4);
    const [mode, setMode] = useState('algorithmic'); // 'llm' or 'algorithmic'
    const [scaledIngredients, setScaledIngredients] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [scaleInfo, setScaleInfo] = useState(null);

    const bg = useColorModeValue('white', 'gray.800');
    const tableBg = useColorModeValue('orange.50', 'whiteAlpha.50');

    const handleScale = async () => {
        setLoading(true);
        setError(null);
        try {
            const result = await scaleRecipe(recipeId, targetServings, mode);
            setScaledIngredients(result.scaled_ingredients);
            setScaleInfo(result);
        } catch (err) {
            setError(err.response?.data?.detail || 'Scaling failed. Is Ollama running?');
        } finally {
            setLoading(false);
        }
    };

    return (
        <MotionBox
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            bg={bg}
            borderRadius="xl"
            border="1px solid"
            borderColor={useColorModeValue('gray.200', 'whiteAlpha.200')}
            p={5}
            shadow="md"
        >
            <VStack spacing={4} align="stretch">
                <Text fontSize="lg" fontWeight="bold" fontFamily="heading">
                    🍽️ Scale Ingredients
                </Text>

                {makes && (
                    <Text fontSize="sm" color="gray.500">
                        Original recipe makes: <Badge colorScheme="purple">{makes}</Badge>
                    </Text>
                )}

                <HStack spacing={4} flexWrap="wrap">
                    <FormControl w="auto">
                        <FormLabel fontSize="sm">Target servings</FormLabel>
                        <NumberInput
                            min={1}
                            max={100}
                            value={targetServings}
                            onChange={(_, v) => setTargetServings(v)}
                            size="md"
                            w="120px"
                        >
                            <NumberInputField />
                            <NumberInputStepper>
                                <NumberIncrementStepper />
                                <NumberDecrementStepper />
                            </NumberInputStepper>
                        </NumberInput>
                    </FormControl>

                    <FormControl display="flex" alignItems="center" w="auto" pt={6}>
                        <FormLabel fontSize="sm" mb={0}>
                            {mode === 'llm' ? '🤖 LLM' : '📐 Math'}
                        </FormLabel>
                        <Switch
                            colorScheme="saffron"
                            isChecked={mode === 'llm'}
                            onChange={(e) => setMode(e.target.checked ? 'llm' : 'algorithmic')}
                        />
                    </FormControl>

                    <Box pt={6}>
                        <Button
                            colorScheme="saffron"
                            onClick={handleScale}
                            isLoading={loading}
                            loadingText="Scaling..."
                        >
                            Scale
                        </Button>
                    </Box>
                </HStack>

                {error && (
                    <Alert status="error" borderRadius="lg">
                        <AlertIcon />
                        {error}
                    </Alert>
                )}

                {loading && (
                    <HStack justify="center" py={4}>
                        <Spinner color="saffron.400" />
                        <Text>
                            {mode === 'llm' ? 'Asking LLM to scale ingredients...' : 'Calculating...'}
                        </Text>
                    </HStack>
                )}

                {scaledIngredients && !loading && (
                    <Box>
                        <Divider my={2} />
                        <HStack mb={3} justify="space-between">
                            <Text fontSize="sm" fontWeight="600">
                                Scaled for {scaleInfo?.target_servings} servings
                            </Text>
                            <Badge colorScheme={mode === 'llm' ? 'blue' : 'green'}>
                                {scaleInfo?.mode === 'llm' ? `🤖 ${scaleInfo?.model}` : '📐 Algorithmic'}
                            </Badge>
                        </HStack>
                        <TableContainer>
                            <Table size="sm" variant="simple">
                                <Thead>
                                    <Tr bg={tableBg}>
                                        <Th>Ingredient</Th>
                                        <Th>Scaled Quantity</Th>
                                    </Tr>
                                </Thead>
                                <Tbody>
                                    {scaledIngredients.map((item, i) => (
                                        <Tr key={i} _hover={{ bg: tableBg }}>
                                            <Td fontWeight="500">{item.name}</Td>
                                            <Td>
                                                <Badge colorScheme="saffron" variant="subtle">
                                                    {item.quantity || '—'}
                                                </Badge>
                                            </Td>
                                        </Tr>
                                    ))}
                                </Tbody>
                            </Table>
                        </TableContainer>
                    </Box>
                )}
            </VStack>
        </MotionBox>
    );
}
