import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import React from 'react';
import { OpaqueColorValue, StyleProp, TextStyle } from 'react-native';

// Add your MaterialIcons mappings here
const MATERIAL_MAPPING = {
  'house.fill': 'home',
  'paperplane.fill': 'send',
  'chevron.left.forwardslash.chevron.right': 'code',
  'chevron.right': 'chevron-right',
  'history': 'history',
  'workout': 'fitness-center'
} as const;

export type IconSymbolName = keyof typeof MATERIAL_MAPPING;

/**
 * A simplified icon component that uses only MaterialIcons.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
}) {
  const mappedIcon = MATERIAL_MAPPING[name];

  if (mappedIcon) {
    return (
      <MaterialIcons
        name={mappedIcon}
        size={size}
        color={color}
        style={style}
      />
    );
  }

  console.warn(`IconSymbol: No mapping found for icon "${name}".`);
  return null; // Return null if the icon name doesn't exist in the mapping
}
