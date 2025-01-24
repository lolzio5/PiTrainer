import { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet } from 'react-native';

interface Workout {
  id: number;
  date: string;
  duration: number;
  exercises: string[];
}

export default function History() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for development
  const mockWorkouts: Workout[] = [
    { id: 1, date: '2023-11-15', duration: 45, exercises: ['Push-ups', 'Squats', 'Plank'] },
    { id: 2, date: '2023-11-16', duration: 60, exercises: ['Running', 'Lunges', 'Crunches'] },
    { id: 3, date: '2023-11-17', duration: 30, exercises: ['Jumping Jacks', 'Burpees', 'Mountain Climbers'] },
  ];

  const fetchWorkouts = useCallback(async () => {
      try {
      // Simulate network latency
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Use mock data instead of fetching from a server
      setWorkouts(mockWorkouts);
      } catch (err: any) {
      setError(err.message || 'An error occurred');
      } finally {
        setLoading(false);
      }
  }, []);

  useEffect(() => {
    
    // the block below, is just for test with a real server, is now deprecated, but keep it for future changes
    // const serverIp = "YOUR_SERVER_IP_ADDRESS"; // Replace with your server's IP address
    // const response = await fetch(`http://${serverIp}:3000/api/workouts`); // Replace with your API endpoint and port if necessary
    //    if (!response.ok) {
    //      throw new Error('Failed to fetch workouts');
    //    }
    //    const data: Workout[] = await response.json();

    fetchWorkouts();
  }, []);

  if (loading) {
    return <View><Text>Loading...</Text></View>;
  }

  if (error) {
    return <View><Text>Error: {error}</Text></View>;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={workouts}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.workoutItem}>
            <Text>Date: {item.date}</Text>
            <Text>Duration: {item.duration} minutes</Text>
            <Text>Exercises: {item.exercises.join(', ')}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
  },
  workoutItem: {
    marginBottom: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
  },
});
