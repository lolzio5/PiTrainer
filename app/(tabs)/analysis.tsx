import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import axios from 'axios';
import { useAuth } from '../context';
import { router } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';

interface WorkoutSet {
  WorkoutID: string;
  set_count: number;
  overall_score: number;
  distance_score: number;
  distance_feedback: string;
  time_consistency_score: number;
  time_consistency_feedback: string;
  shakiness_score: number;
  shakiness_feedback: string;
}

const WorkoutAnalysis: React.FC = () => {
  const { token } = useAuth();
  const [sets, setSets] = useState<WorkoutSet[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch workout analysis data (array of sets) from the server
  const fetchWorkoutAnalysis = async () => {
    try {
      const response = await axios.get('http://3.10.117.27:80/api/analysis', {
        headers: { Authorization: `Bearer ${token}` },
      });
      // Assuming response.data is an array of set objects:
      setSets(response.data);
    } catch (err) {
      setError('Failed to load workout analysis data.');
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchWorkoutAnalysis();
    }, [token])
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#fb8c00" />
        <Text style={styles.loadingText}>Loading workout analysis...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (sets.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>No workouts found :(</Text>
        <Text style={styles.emptySubtext}>
          Start a new workout by navigating to the "New Workout" tab!
        </Text>
        <TouchableOpacity style={styles.startWorkoutButton} onPress={() => router.push('./workout')}>
          <Text style={styles.startWorkoutButtonText}>Start Workout</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Render item for FlatList
  const renderItem = ({ item }: { item: WorkoutSet }) => (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Set {item.set_count}</Text>
      <Text style={styles.cardText}>Overall Score: {item.overall_score}</Text>
      
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Distance</Text>
        <Text style={styles.cardText}>Score: {item.distance_score}</Text>
        <Text style={styles.feedbackText}>{item.distance_feedback}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Time Consistency</Text>
        <Text style={styles.cardText}>Score: {item.time_consistency_score}</Text>
        <Text style={styles.feedbackText}>{item.time_consistency_feedback}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Shakiness</Text>
        <Text style={styles.cardText}>Score: {item.shakiness_score}</Text>
        <Text style={styles.feedbackText}>{item.shakiness_feedback}</Text>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Workout Analysis</Text>
      <FlatList
        data={sets}
        keyExtractor={(item) => item.WorkoutID + '-' + item.set_count}
        renderItem={renderItem}
        contentContainerStyle={{ paddingBottom: 20 }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: 35,
    paddingHorizontal: 16,
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 16,
  },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  cardText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 4,
  },
  section: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  feedbackText: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 15,
    fontSize: 18,
    fontWeight: '600',
    color: '#555',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 18,
    color: 'red',
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  emptyText: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 16,
    textAlign: 'center',
    color: '#666',
    marginBottom: 20,
  },
  startWorkoutButton: {
    backgroundColor: '#007BFF',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  startWorkoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default WorkoutAnalysis;
