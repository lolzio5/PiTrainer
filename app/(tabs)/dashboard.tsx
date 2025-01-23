// app/(tabs)/Dashboard.tsx
import React from 'react';
import { View, Text, Button, StyleSheet, FlatList, } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { RootStackParamList } from '@/types'; // Correct import path
import { NavigationProp } from '@react-navigation/native';

interface Workout {
  date: string;
  summary: string;
}

const workouts: Workout[] = [
  { date: '2024-03-08', summary: '3 sets of 10 reps' },
  { date: '2024-03-07', summary: '2 sets of 12 reps' },
  // ... more workouts
];


const Dashboard: React.FC = () => {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();

  const renderItem = ({ item }: { item: Workout }) => (
    <View style={styles.workoutItem}>
      <Text>{item.date}</Text>
      <Text>{item.summary}</Text>
    </View>
  );

   return (
    <View style={styles.container}>
      <FlatList
        data={workouts}
        renderItem={renderItem}
        keyExtractor={(_, index) => index.toString()}
      />
      <Button
        title="Start Workout"
        onPress={() => navigation.navigate('Workout')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  workoutItem: {
    marginBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
    paddingBottom: 10,
  },
});

export default Dashboard;