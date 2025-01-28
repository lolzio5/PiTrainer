import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { LinearGradient } from 'expo-linear-gradient';


interface Workout {
  id: number;
  date: string;
  rep_number: number;
  exercise: string;
  rep_quality: number[];
}

const screenWidth = Dimensions.get('window').width;

export default function History() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const mockWorkouts: Workout[] = [
    {
      id: 1,
      date: '2025-01-22',
      rep_number: 50,
      exercise: 'Triceps Extension',
      rep_quality: Array.from({ length: 50 }, () => Math.floor(Math.random() * (95 - 50) + 50)),
    },
    {
      id: 2,
      date: '2025-01-24',
      rep_number: 50,
      exercise: 'Triceps Extension',
      rep_quality: Array.from({ length: 50 }, () => Math.floor(Math.random() * (90 - 45) + 45)),
    },
    {
      id: 3,
      date: '2025-01-27',
      rep_number: 50,
      exercise: 'Triceps Extension',
      rep_quality: Array.from({ length: 50 }, () => Math.floor(Math.random() * (85 - 40) + 40)),
    },
  ];

  const fetchWorkouts = useCallback(async () => {
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setWorkouts(mockWorkouts);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkouts();
  }, [fetchWorkouts]);

  if (loading) {
    return (
      <View>
        <Text>Loading...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View>
        <Text>Error: {error}</Text>
      </View>
    );
  }

  const selectedWorkout = workouts[0];
  const chartData = {
    labels: selectedWorkout.rep_quality
      .map((_, index) => index + 1)
      .filter((num) => num % 5 === 0) // Show labels every 5 reps
      .map(String),
    datasets: [
      {
        data: selectedWorkout.rep_quality,
        strokeWidth: 2,
      },
    ],
    name: selectedWorkout.exercise,
    date: selectedWorkout.date,
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#fb8c00', '#ffa726']}
        start={{ x: 0, y: 1 }} // Gradient starts from left
        end={{ x: 1, y: 0 }} 
        style={styles.chartContainer}
        >
        <Text style={styles.chartTitle}>{chartData.name} on {chartData.date}</Text>
        
        <LineChart
          data={chartData}
          width={screenWidth - 30} // Same width as the boxes
          height={220}
          chartConfig={{
            backgroundColor: '#e26a00',
            backgroundGradientFrom: '#fb8c00',
            backgroundGradientTo: '#ffa726',
            decimalPlaces: 0, // Ensure Y-axis shows integers only
            color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
            style: {
              borderRadius: 16,
              marginLeft: 0, // Center the chart
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
        <View style={styles.axisLabels}>
          <Text style={styles.axisLabel}>Rep Count</Text>
          <Text style={[styles.axisLabel, styles.yAxisLabel]}>Rep Quality</Text>
        </View>
      </LinearGradient>
      <FlatList
        data={workouts}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.workoutItem}>
            <Text>Date: {item.date}</Text>
            <Text>Exercise: {item.exercise}</Text>
            <Text>Total reps: {item.rep_number}</Text>
          </View>
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
  chartContainer: {
    backgroundColor: '#fb8c00', // Orange box color
    padding: 0,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 20,
    width: screenWidth - 30, // Ensure it's not too wide
    alignSelf: 'center',
  },
  chartTitleContainer: {
    padding: 5,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 0,
    width: '100%',
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    color: '#fff', // Title text color should remain white
  },
  chartStyle: {
    marginVertical: 0,
    borderRadius: 16,
    padding: 0,
    paddingBottom: 10,
    marginLeft: 0, // Ensure no extra padding on the left
  },
  workoutItem: {
    marginBottom: 10,
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 16,
    width: screenWidth - 30, // Match the chart width
    alignSelf: 'center',
    backgroundColor: '#fff',
  },
  axisLabels: {
    position: 'absolute',
    bottom: 7,
    left: 150,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  axisLabel: {
    fontSize: 14,
    color: '#fff',
    textAlign: 'center',
  },
  yAxisLabel: {
    transform: [{ rotate: '-90deg' }],
    position: 'absolute',
    top: '50%',
    left: -170,
    marginTop: -10,
  },
});
