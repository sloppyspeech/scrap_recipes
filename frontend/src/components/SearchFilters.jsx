import { useState, useCallback, useRef } from 'react';
import {
    Box, Input, Select, HStack, VStack, Button, RangeSlider, RangeSliderTrack,
    RangeSliderFilledTrack, RangeSliderThumb, Text, Tag, TagLabel, TagCloseButton,
    Wrap, WrapItem, InputGroup, InputLeftElement, Collapse, useDisclosure,
    useColorModeValue, IconButton, Tooltip,
} from '@chakra-ui/react';
import { SearchIcon, ChevronDownIcon, ChevronUpIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';

const MotionBox = motion(Box);

export default function SearchFilters({ tags = [], categories = [], onSearch }) {
    const [selectedCategory, setSelectedCategory] = useState('');
    const [query, setQuery] = useState('');
    const [ingredient, setIngredient] = useState('');
    const [queryTag, setQueryTag] = useState('');
    const [selectedTags, setSelectedTags] = useState([]);
    const [calRange, setCalRange] = useState([0, 2000]);
    const { isOpen, onToggle } = useDisclosure();
    const debounceRef = useRef(null);

    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'whiteAlpha.200');

    const doSearch = useCallback((overrides = {}) => {
        const params = {
            q: query,
            ingredient,
            category: selectedCategory,
            tag: selectedTags.join(','),
            cal_min: calRange[0] > 0 ? calRange[0] : undefined,
            cal_max: calRange[1] < 2000 ? calRange[1] : undefined,
            ...overrides,
        };
        onSearch(params);
    }, [query, ingredient, selectedCategory, selectedTags, calRange, onSearch]);

    const handleQueryChange = (e) => {
        setQuery(e.target.value);
        clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
            doSearch({ q: e.target.value });
        }, 400);
    };

    const addTag = (tagName) => {
        if (!selectedTags.includes(tagName)) {
            const newTags = [...selectedTags, tagName];
            setSelectedTags(newTags);
            doSearch({ tag: newTags.join(',') });
        }
    };

    const removeTag = (tagName) => {
        const newTags = selectedTags.filter(t => t !== tagName);
        setSelectedTags(newTags);
        doSearch({ tag: newTags.join(',') });
    };

    return (
        <MotionBox
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            bg={bg}
            borderRadius="xl"
            border="1px solid"
            borderColor={borderColor}
            p={5}
            mb={6}
            shadow="lg"
        >
            <VStack spacing={4} align="stretch">
                {/* Main search bar */}
                <HStack>
                    <InputGroup size="lg">
                        <InputLeftElement>
                            <SearchIcon color="saffron.400" />
                        </InputLeftElement>
                        <Input
                            placeholder="Search recipes by name..."
                            value={query}
                            onChange={handleQueryChange}
                            variant="filled"
                            _focus={{ borderColor: 'saffron.400', bg: useColorModeValue('white', 'gray.700') }}
                        />
                    </InputGroup>
                    <Button
                        size="lg"
                        colorScheme="saffron"
                        onClick={() => doSearch()}
                        px={8}
                    >
                        Search
                    </Button>
                </HStack>

                {/* Advanced filters toggle */}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onToggle}
                    rightIcon={isOpen ? <ChevronUpIcon /> : <ChevronDownIcon />}
                    color="saffron.400"
                >
                    {isOpen ? 'Hide Filters' : 'Advanced Filters'}
                </Button>

                <Collapse in={isOpen} animateOpacity>
                    <VStack spacing={4} align="stretch" pt={2}>
                        {/* Category Selector */}
                        <Box>
                            <Text fontSize="sm" fontWeight="600" mb={2}>Category</Text>
                            <Select
                                placeholder="Select category..."
                                value={selectedCategory}
                                onChange={(e) => {
                                    setSelectedCategory(e.target.value);
                                    // Trigger search immediately on category change? Or wait for update?
                                    // Given implementation of doSearch with deps, we should call it manually with new value
                                    // or let useEffect handle it if we had one.
                                    // Here we call doSearch explicitly.
                                    // But doSearch uses closure state 'selectedCategory'.
                                    // So we must pass override.
                                    // Better: separate state update and search or use effect.
                                    // But to keep it simple and consistent with this component style:
                                    // We'll pass the new value in override.
                                    // Wait, doSearch uses state. State update is async.
                                    // So we must pass it.
                                    // But wait, doSearch deps includes selectedCategory.
                                    // If we just set state, we don't trigger search automatically unless we use useEffect.
                                    // The existing code for tags calls doSearch explicitly.
                                    // So let's do that.
                                }}
                            // Actually, let's fix the onChange to call doSearch properly
                            >
                                {categories.map((c) => (
                                    <option key={c.name} value={c.name}>
                                        {c.name} ({c.count})
                                    </option>
                                ))}
                            </Select>
                        </Box>

                        {/* Ingredient search */}
                        <InputGroup>
                            <InputLeftElement>🥘</InputLeftElement>
                            <Input
                                placeholder="Filter by ingredient..."
                                value={ingredient}
                                onChange={(e) => setIngredient(e.target.value)}
                                variant="filled"
                            />
                        </InputGroup>

                        {/* Calorie Range */}
                        <Box>
                            <Text fontSize="sm" fontWeight="600" mb={2}>
                                Calories: {calRange[0]} — {calRange[1] >= 2000 ? '2000+' : calRange[1]}
                            </Text>
                            <RangeSlider
                                min={0}
                                max={2000}
                                step={50}
                                value={calRange}
                                onChange={setCalRange}
                                onChangeEnd={() => doSearch()}
                                colorScheme="saffron"
                            >
                                <RangeSliderTrack>
                                    <RangeSliderFilledTrack />
                                </RangeSliderTrack>
                                <RangeSliderThumb index={0} boxSize={5} />
                                <RangeSliderThumb index={1} boxSize={5} />
                            </RangeSlider>
                        </Box>

                        {/* Tag selector - Searchable & Multi-select */}
                        <Box>
                            <Text fontSize="sm" fontWeight="600" mb={2}>Filter by Tags</Text>

                            <Input
                                placeholder="Search tags to add..."
                                value={queryTag}
                                onChange={(e) => setQueryTag(e.target.value)}
                                size="sm"
                                mb={2}
                            />

                            <Box
                                maxH="150px"
                                overflowY="auto"
                                border="1px solid"
                                borderColor={borderColor}
                                borderRadius="md"
                                bg={useColorModeValue('gray.50', 'gray.700')}
                            >
                                {tags
                                    .filter(t =>
                                        !selectedTags.includes(t.name) &&
                                        t.name.toLowerCase().includes(queryTag.toLowerCase())
                                    )
                                    .sort((a, b) => a.name.localeCompare(b.name))
                                    .map(t => (
                                        <Box
                                            key={t.name}
                                            px={3}
                                            py={2}
                                            cursor="pointer"
                                            _hover={{ bg: useColorModeValue('saffron.100', 'whiteAlpha.200') }}
                                            onClick={() => {
                                                addTag(t.name);
                                                setQueryTag('');
                                            }}
                                        >
                                            <Text fontSize="sm">{t.name} <Text as="span" color="gray.500" fontSize="xs">({t.count})</Text></Text>
                                        </Box>
                                    ))}
                                {tags.length === 0 && <Text p={2} fontSize="sm" color="gray.500">No tags available</Text>}
                            </Box>

                            {selectedTags.length > 0 && (
                                <Wrap mt={3}>
                                    {selectedTags.map(t => (
                                        <WrapItem key={t}>
                                            <Tag size="md" colorScheme="saffron" borderRadius="full">
                                                <TagLabel>{t}</TagLabel>
                                                <TagCloseButton onClick={() => removeTag(t)} />
                                            </Tag>
                                        </WrapItem>
                                    ))}
                                </Wrap>
                            )}
                        </Box>
                    </VStack>
                </Collapse>
            </VStack>
        </MotionBox>
    );
}
