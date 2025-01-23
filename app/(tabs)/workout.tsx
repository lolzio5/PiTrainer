import React, { useState } from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { RootStackParamList } from '@/types'; // Correct import path
import { NavigationProp } from '@react-navigation/native';

const Workout: React.FC = () => {
  const [repCount, setRepCount] = useState(0);
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();
  const incrementRepCount = () => {
    setRepCount(repCount + 1);
  };

  const endWorkout = () => {
    // Navigate back to the dashboard
    // Implement navigation logic here (e.g., using react-navigation)
    console.log('Workout ended. Rep count:', repCount);
    // Example navigation using react-navigation:
    navigation.navigate('Dashboard'); 
  };

  return (
    <View style={styles.container}>
      <Text style={styles.repCounterText}>Reps: {repCount}</Text>
      <Button title="Increment Rep" onPress={incrementRepCount} />
      <Button title="End Workout" onPress={endWorkout} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  repCounterText: {
    fontSize: 24,
    marginBottom: 20,
  },
});

export default Workout;