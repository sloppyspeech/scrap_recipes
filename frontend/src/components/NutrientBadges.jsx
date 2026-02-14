import { Badge, HStack, Wrap, WrapItem, Tooltip, useColorModeValue } from '@chakra-ui/react';

const NUTRIENT_COLORS = {
    calories: 'orange',
    proteinContent: 'green',
    carbohydrateContent: 'blue',
    fatContent: 'red',
    fiberContent: 'teal',
    cholesterolContent: 'pink',
    sodiumContent: 'purple',
};

const NUTRIENT_LABELS = {
    calories: '🔥 Calories',
    proteinContent: '💪 Protein',
    carbohydrateContent: '🍞 Carbs',
    fatContent: '🧈 Fat',
    fiberContent: '🌾 Fiber',
    cholesterolContent: '❤️ Cholesterol',
    sodiumContent: '🧂 Sodium',
};

export default function NutrientBadges({ nutrients = {} }) {
    if (!nutrients || Object.keys(nutrients).length === 0) {
        return null;
    }

    return (
        <Wrap spacing={2}>
            {Object.entries(nutrients).map(([key, value]) => {
                if (!value || key === '@type') return null;
                const color = NUTRIENT_COLORS[key] || 'gray';
                const label = NUTRIENT_LABELS[key] || key;

                return (
                    <WrapItem key={key}>
                        <Tooltip label={label} placement="top" hasArrow>
                            <Badge
                                colorScheme={color}
                                variant="subtle"
                                borderRadius="full"
                                px={3}
                                py={1}
                                fontSize="xs"
                                fontWeight="600"
                            >
                                {label.split(' ')[0]} {value}
                            </Badge>
                        </Tooltip>
                    </WrapItem>
                );
            })}
        </Wrap>
    );
}
