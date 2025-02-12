// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { useColorScheme } from '@/hooks/useColorScheme';
import { Colors } from '@/constants/Colors';
import { Platform } from 'react-native';
import { HapticTab } from '@/components/HapticTab';
import { IconSymbol } from '@/components/ui/IconSymbol';
import TabBarBackground from '@/components/ui/TabBarBackground';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors['light'].text,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarBackground: TabBarBackground,
        tabBarStyle: Platform.select({
          ios: {
            position: 'absolute',
          },
          default: {},
        }),
      }}>
        <Tabs.Screen
          name="index"
          options={{
            title: 'Home',
            tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
          }}
        />
        <Tabs.Screen
          name="analysis"
          options={{
            title: 'Latest Workout',
            tabBarIcon: ({ color }) => <IconSymbol size={28} name="analysis" color={color} />,
          }}
        />
        <Tabs.Screen
          name="history"
          options={{
            title: 'Workout History',
            tabBarIcon: ({ color }) => <IconSymbol size={28} name="history" color={color} />,
          }}
        />
        <Tabs.Screen
            name="workout"
            options={{
              title: 'New Workout',
              tabBarIcon: ({ color }) => <IconSymbol size={28} name="workout" color={color} />,
            }}
          />
      </Tabs>
  );
}
