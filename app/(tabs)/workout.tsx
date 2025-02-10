import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, Image, TouchableOpacity } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import axios from 'axios';
import { useAuth } from '../context';

interface Exercise {
  name: string;
  image: any;
}

const exercises: Exercise[] = [
  {
    name: 'Seated Cable Rows',
    image: require('../../assets/images/seated_cable_rows.png'),
  },
  {
    name: 'Lat Pulldowns',
    image: require('../../assets/images/lat_pulldown.jpg'),
  }
];
const Workout: React.FC = () => {
  const [selectedExercise, setSelectedExercise] = useState<Exercise>(exercises[0]);
  const [repCount, setRepCount] = useState(0);
  const [setCount, setSetCount] = useState(0);
  const [workoutActive, setWorkoutActive] = useState(false);
  const [setActive, setSetActive] = useState(false);
  const { token } = useAuth();

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (workoutActive && setActive) {
      interval = setInterval(fetchReps, 1000); // Poll reps every 1 seconds
    }
    return () => clearInterval(interval);
  }, [workoutActive]);

  const startWorkout = async () => {
    try {
      await axios.post(
        'http://18.134.249.18:80/api/start',
        { exercise_name: selectedExercise.name },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setWorkoutActive(true);
      setSetCount(0);
      setSetActive(true);
    } catch (error) {
      console.error('Error starting workout:', error);
    }
  };

  const fetchReps = async () => {
    try {
      const response = await axios.get('http://18.134.249.18:80/api/reps', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRepCount(response.data);
    } catch (error) {
      console.error('Error fetching reps:', error);
    }
  };

  const startSet = async () => {
    try {
      await axios.get('http://18.134.249.18:80/api/start_set', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRepCount(0);
      setSetCount((prev) => prev + 1);
      setSetActive(true);
    } catch (error) {
      console.error('Error starting set:', error);
    }
  };

  const endSet = async () => {
    try {
      await axios.get('http://18.134.249.18:80/api/end_set', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRepCount(0);
      setSetActive(false);
    } catch (error) {
      console.error('Error ending set:', error);
    }
  };

  const endWorkout = async () => {
    try {
      await axios.get('http://18.134.249.18:80/api/end', {
        headers: { Authorization: `Bearer ${token}` },
      });
      setWorkoutActive(false);
      setRepCount(0);
      setSetCount(0);
      setSetActive(false);
    } catch (error) {
      console.error('Error ending workout:', error);
    }
  };

  const renderButtons = () => {
    if (!workoutActive) {
      return (<TouchableOpacity style={styles.buttonStart} onPress={startWorkout}>
                <Text style={styles.buttonText}>Start Workout</Text>
              </TouchableOpacity>);
    }
  
    if (!setActive) {
      return (
        <>
        <TouchableOpacity style={styles.buttonStart} onPress={startSet}>
          <Text style={styles.buttonText}>Start Set</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.buttonEnd} onPress={endWorkout}>
          <Text style={styles.buttonText}>End Workout</Text>
        </TouchableOpacity>
        </>
      );
    }
  
    return (
      <>
        <TouchableOpacity style={styles.buttonEnd} onPress={endSet}>
          <Text style={styles.buttonText}>End Set</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.buttonEnd} onPress={endWorkout}>
          <Text style={styles.buttonText}>End Workout</Text>
        </TouchableOpacity>
      </>
    );
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
        enabled={!workoutActive}
      >
        {exercises.map((exercise) => (
          <Picker.Item key={exercise.name} label={exercise.name} value={exercise.name} />
        ))}
      </Picker>

      <View style={styles.exerciseDetails}>
        <Image source={selectedExercise.image} style={styles.exerciseImage} resizeMode="contain" />
        <Text style={styles.exerciseName}>{selectedExercise.name}</Text>
        <Text style={styles.exerciseStats}>Sets: {setCount}</Text>
        <Text style={styles.repCount}>{repCount}</Text> {/* Large Rep Counter */}
        {renderButtons()} {/* Render buttons based on workout state */}
      </View>
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
    marginBottom: 10,
  },
  exerciseDetails: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  exerciseImage: {
    width: 300,
    height: 300,
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
  repCount: {
    fontSize: 60, // Large Rep Counter
    fontWeight: 'bold',
    color: '#007BFF',
    marginVertical: 20,
  },
  buttonStart: {
    backgroundColor: '#007BFF',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonEnd: {
    backgroundColor: '#D32F2F',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default Workout;
