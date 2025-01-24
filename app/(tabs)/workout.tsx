import React, { useState } from 'react';
import { View, Text, Button, StyleSheet, Image } from 'react-native';
import { Picker } from '@react-native-picker/picker';


interface Exercise {
  name: string;
  image: string;
  reps: number;
  sets: number;
}


const exercises: Exercise[] = [
  {
    name: 'Triceps Extensions',
    image: require('../../assets/images/triceps_extension.jpg'), // Replace with a valid image URL or local asset
    reps: 0,
    sets: 0,
  },
  {
    name: 'Lat Pulldowns',
    image: require('../../assets/images/lat_pulldown.jpg'), // Replace with a valid image URL or local asset
    reps: 0,
    sets: 0,
  },
];

const Workout: React.FC = () => {
  const [selectedExercise, setSelectedExercise] = useState<Exercise>(exercises[0]);

  const incrementReps = () => {
    setSelectedExercise((prev) => ({
      ...prev,
      reps: prev.reps + 1,
    }));
  };

  const incrementSets = () => {
    setSelectedExercise((prev) => ({
      ...prev,
      sets: prev.sets + 1,
    }));
  };

  const endWorkout = () => {
    console.log('Workout ended:', exercises);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>New Workout</Text>
      <Picker
        selectedValue={selectedExercise.name}
        onValueChange={(itemValue) => {
          const selected = exercises.find((exercise) => exercise.name === itemValue);
          if (selected) setSelectedExercise(selected);
        }}
        style={styles.picker}
      >
        {exercises.map((exercise) => (
          <Picker.Item key={exercise.name} label={exercise.name} value={exercise.name} />
        ))}
      </Picker>

      <View style={styles.exerciseDetails}>
        <Image
          source={selectedExercise.image}
          style={styles.exerciseImage}
          resizeMode="contain"
        />
        <Text style={styles.exerciseName}>{selectedExercise.name}</Text>
        <Text style={styles.exerciseStats}>
          Reps: {selectedExercise.reps} | Sets: {selectedExercise.sets}
        </Text>
        <Button title="Increment Reps" onPress={incrementReps} />
        <Button title="Increment Sets" onPress={incrementSets} />
      </View>

      <Button title="End Workout" onPress={endWorkout} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 40,
    backgroundColor: '#f4f4f4',
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  picker: {
    height: 60,
    width: '100%',
    marginBottom: 5,
  },
  exerciseDetails: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    marginTop: 0,
  },
  exerciseImage: {
    width: 300,
    height: 300,
    marginBottom: 0,
    marginTop: 0,
    borderRadius: 10,
  },
  exerciseName: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  exerciseStats: {
    fontSize: 16,
    marginBottom: 20,
  },
});

export default Workout;
