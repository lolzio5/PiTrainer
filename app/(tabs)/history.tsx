import React, { useState, useCallback,  } from 'react';
import { View, Text, FlatList, StyleSheet, Dimensions, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context';
import { router } from 'expo-router';
import axios from 'axios';
import { useFocusEffect } from '@react-navigation/native';

interface Workout {
  WorkoutID: string;
  UserID: string;
  date: string;
  rep_number: number;
  exercise: string;
  rep_quality: number[];
}

// New fetchHistoryData function using similar structure as Index page
const fetchHistoryData = async (token: string | null): Promise<Workout[] | null> => {
  try {
    if (token) {
      // Request protected route using token in header
      const response = await axios.get('http://3.10.117.27:80/api/history', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      // Assuming response.data is an array of workout items
      const data = response.data;
      // Filter and map data to ensure each item matches the Workout interface
      const workouts: Workout[] = data
        .filter((item: any) =>
          item.UserID &&
          item.WorkoutID &&
          item.date &&
          typeof item.rep_number === 'number' &&
          item.exercise &&
          Array.isArray(item.rep_quality)
        )
        .map((item: any) => ({
          WorkoutID: item.WorkoutID || item.id, // Adjust as necessary if API uses a different name
          UserID: item.UserID,
          date: item.date,
          rep_number: item.rep_number,
          exercise: item.exercise,
          rep_quality: item.rep_quality,
        }));
      return workouts;
    }
    return null;
  } catch (error: any) {
    //console.error('Error fetching history data:', error);
    return null;
  }
};

const screenWidth = Dimensions.get('window').width;

export default function History() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWorkout, setSelectedWorkout] = useState<Workout | null>(null);
  const { token } = useAuth();

  // Use useCallback to define the data fetcher function
  const fetchWorkouts = useCallback(async () => {
    setLoading(true);
    const fetchedWorkouts = await fetchHistoryData(token);
    if (fetchedWorkouts) {
      // Sort workouts by date (latest first)
      const sortedWorkouts = fetchedWorkouts.sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      );
      setWorkouts(sortedWorkouts);
      setSelectedWorkout(sortedWorkouts[sortedWorkouts.length-1]);
    } else {
      setError(null);
    }
    setLoading(false);
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      fetchWorkouts();
    }, [fetchWorkouts])
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#fb8c00" />
        <Text style={styles.loadingText}>Fetching your workout history...</Text>
      </View>
    );
  }
  if (error) {
    return (
      <View style={styles.container}>
        <Text>Error: {error}</Text>
      </View>
    );
  }

  if (workouts.length === 0) {
    return (
      <View style={styles.noWorkoutContainer}>
        <Text style={styles.noWorkoutText}>No workouts found</Text>
        <Text style={styles.noWorkoutSubtext}>
          Start a new workout by navigating to the "New Workout" tab!
        </Text>
        <TouchableOpacity style={styles.startWorkoutButton} onPress={() => router.push('./workout')}>
          <Text style={styles.startWorkoutButtonText}>Start Workout</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Calculate average rep quality for each workout
  const averageRepQuality = workouts.map((workout) => ({
    date: workout.date,
    averageRepQuality:
      workout.rep_quality.reduce((acc, quality) => acc + quality, 0) / workout.rep_quality.length,
  }));

  // Prepare chart data for rep quality over time using the selected workout
  const chartData = selectedWorkout
    ? {
        labels: selectedWorkout.rep_quality
          .map((_, index) => index)
          .filter((num) => num % 5 === 0)
          .map(String),
        datasets: [
          {
            data: selectedWorkout.rep_quality,
            strokeWidth: 2,
          },
        ],
        name: selectedWorkout.exercise,
        date: selectedWorkout.date,
      }
    : {
        labels: [],
        datasets: [
          {
            data: [],
            strokeWidth: 2,
          },
        ],
        name: '',
        date: '',
      };

  const defaultAverageChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'], // Example months
    datasets: [
      {
        data: [0, 0, 0, 0, 0], // Placeholder averages
        strokeWidth: 2,
      },
    ],
  };

  // Chart data for average rep quality per workout
  const averageChartData = averageRepQuality.length
    ? {
        labels: averageRepQuality.map((item) => {
          const [year, month, day] = item.date.split('-');
          return `${month}-${day}`; // Show month and day
        }),
        datasets: [
          {
            data: averageRepQuality.map((item) => item.averageRepQuality),
            strokeWidth: 2,
          },
        ],
      }
    : defaultAverageChartData;

  return (
    <View style={styles.container}>
      {/* First Line Chart: Rep Quality over Time */}
      <LinearGradient
        colors={['#fb8c00', '#ffa726']}
        start={{ x: 0, y: 1 }}
        end={{ x: 1, y: 0 }}
        style={styles.chartContainer}
      >
        <Text style={styles.chartTitle}>
          {chartData.name} on {chartData.date}
        </Text>
        <LineChart
          data={chartData}
          width={screenWidth - 30}
          height={220}
          chartConfig={{
            backgroundColor: '#e26a00',
            backgroundGradientFrom: '#fb8c00',
            backgroundGradientTo: '#ffa726',
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '2',
              stroke: '#ffa726',
            },
          }}
          bezier
          style={styles.chartStyle}
        />
        <View style={styles.axisLabels1}>
          <Text style={styles.axisLabel1}>Rep Count</Text>
          <Text style={[styles.axisLabel1, styles.yAxisLabel1]}>Rep Quality</Text>
        </View>
      </LinearGradient>

      {/* Second Line Chart: Average Rep Quality per Workout */}
      <LinearGradient
        colors={['#4caf50', '#66bb6a']}
        start={{ x: 0, y: 1 }}
        end={{ x: 1, y: 0 }}
        style={styles.chartContainer}
      >
        <Text style={styles.chartTitle}>Average Rep Quality</Text>
        <LineChart
          data={averageChartData}
          width={screenWidth - 30}
          height={200}
          chartConfig={{
            backgroundColor: '#388e3c',
            backgroundGradientFrom: '#4caf50',
            backgroundGradientTo: '#66bb6a',
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '2',
              stroke: '#66bb6a',
            },
          }}
          bezier
          style={styles.chartStyle}
        />
        <View style={styles.axisLabels2}>
          <Text style={styles.axisLabel2}>Date</Text>
          <Text style={[styles.axisLabel2, styles.yAxisLabel2]}>Average Rep Quality</Text>
        </View>
      </LinearGradient>

      {/* Workout List */}
      <FlatList
        data={workouts}
        keyExtractor={(item) => item.WorkoutID}
        initialNumToRender={10}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.workoutItem}
            onPress={() => setSelectedWorkout(item)}
          >
            <Text>Date: {item.date}</Text>
            <Text>Exercise: {item.exercise}</Text>
            <Text>Total reps: {item.rep_number}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 35,
    backgroundColor: '#f4f4f4',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f4f4f4',
  },
  loadingText: {
    marginTop: 15,
    fontSize: 18,
    fontWeight: '600',
    color: '#555',
  },
  chartContainer: {
    backgroundColor: '#fb8c00',
    padding: 0,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 5,
    width: screenWidth - 30,
    alignSelf: 'center',
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    color: '#fff',
  },
  chartStyle: {
    marginVertical: 0,
    borderRadius: 16,
    padding: 0,
    paddingBottom: 10,
  },
  workoutItem: {
    marginBottom: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 16,
    width: screenWidth - 30,
    alignSelf: 'center',
    backgroundColor: '#fff',
  },
  axisLabels1: {
    position: 'absolute',
    bottom: 7,
    left: 150,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  axisLabel1: {
    fontSize: 14,
    color: '#fff',
    textAlign: 'center',
  },
  yAxisLabel1: {
    transform: [{ rotate: '-90deg' }],
    position: 'absolute',
    top: '50%',
    left: -170,
    marginTop: -130,
  },
  axisLabels2: {
    position: 'absolute',
    bottom: 7,
    left: 160,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  axisLabel2: {
    fontSize: 14,
    color: '#fff',
    textAlign: 'center',
  },
  yAxisLabel2: {
    transform: [{ rotate: '-90deg' }],
    position: 'absolute',
    top: '50%',
    left: -210,
    marginTop: -120,
  },
  noWorkoutContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
    backgroundColor: '#f4f4f4',
  },
  noWorkoutText: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  noWorkoutSubtext: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
    color: '#666',
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