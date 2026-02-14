import {
    Box, Heading, Text, HStack, VStack, Tag, Badge, useColorModeValue,
    LinkBox, LinkOverlay,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiClock, FiZap } from 'react-icons/fi';

const MotionBox = motion(Box);

export default function RecipeCard({ recipe, index = 0 }) {
    const bg = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.100', 'whiteAlpha.100');
    const hoverBg = useColorModeValue('orange.50', 'whiteAlpha.100');

    return (
        <MotionBox
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
        >
            <LinkBox
                as="article"
                bg={bg}
                border="1px solid"
                borderColor={borderColor}
                borderRadius="xl"
                p={5}
                shadow="md"
                _hover={{
                    shadow: 'xl',
                    bg: hoverBg,
                    borderColor: 'saffron.400',
                    transform: 'translateY(-2px)',
                }}
                transition="all 0.25s ease"
                cursor="pointer"
            >
                <VStack align="stretch" spacing={3}>
                    {/* Recipe name */}
                    <Heading size="md" noOfLines={2}>
                        <LinkOverlay as={RouterLink} to={`/recipe/${recipe.id}`}>
                            {recipe.name}
                        </LinkOverlay>
                    </Heading>

                    {/* Badges row */}
                    <HStack spacing={3} flexWrap="wrap">
                        {recipe.calories && (
                            <Badge
                                colorScheme="orange"
                                variant="subtle"
                                borderRadius="full"
                                px={3}
                                py={1}
                                fontSize="xs"
                                display="flex"
                                alignItems="center"
                                gap={1}
                            >
                                <FiZap /> {recipe.calories}
                            </Badge>
                        )}
                        {recipe.total_time && (
                            <Badge
                                colorScheme="teal"
                                variant="subtle"
                                borderRadius="full"
                                px={3}
                                py={1}
                                fontSize="xs"
                                display="flex"
                                alignItems="center"
                                gap={1}
                            >
                                <FiClock /> {recipe.total_time}
                            </Badge>
                        )}
                        {recipe.makes && (
                            <Badge
                                colorScheme="purple"
                                variant="subtle"
                                borderRadius="full"
                                px={3}
                                py={1}
                                fontSize="xs"
                            >
                                {recipe.makes}
                            </Badge>
                        )}
                    </HStack>

                    {/* Tags */}
                    {recipe.tags && recipe.tags.length > 0 && (
                        <HStack spacing={1} flexWrap="wrap">
                            {recipe.tags.slice(0, 4).map(tag => (
                                <Tag
                                    key={tag}
                                    size="sm"
                                    variant="outline"
                                    colorScheme="saffron"
                                    borderRadius="full"
                                >
                                    {tag}
                                </Tag>
                            ))}
                            {recipe.tags.length > 4 && (
                                <Text fontSize="xs" color="gray.500">
                                    +{recipe.tags.length - 4} more
                                </Text>
                            )}
                        </HStack>
                    )}
                </VStack>
            </LinkBox>
        </MotionBox>
    );
}
