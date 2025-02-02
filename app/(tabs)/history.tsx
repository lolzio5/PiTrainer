import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, Dimensions, TouchableOpacity } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context';
import axios from 'axios';

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
  const [selectedWorkout, setSelectedWorkout] = useState<Workout | null>(null);
  const { token } = useAuth();
  const fetchWorkouts = useCallback(async () => {
    try {
      setLoading(true);
      if (token) {
      // Use the token to access protected routes
      axios
        .get('http://18.134.249.18:80/api/history', {
          headers: {
            Authorization: `Bearer ${token}`,  // Send token in the request header
          },
        })
        .then((response) => {
          const data: Workout[] = response.data
          setWorkouts(data);
          setSelectedWorkout(data[data.length - 1]);
        })
        .catch((error) => {
          console.error('Error fetching data', error);
        });
    }
    } catch (err: any) {
      setError(err.message || "An error occurred while fetching workouts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkouts();
  }, [fetchWorkouts]);

  if (loading) {
    return (
      <View style={styles.container}>
        <Text>Loading...</Text>
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
  

  // Calculate average rep quality for each workout
  const averageRepQuality = workouts.map((workout) => ({
    date: workout.date,
    averageRepQuality: workout.rep_quality.reduce((acc, quality) => acc + quality, 0) / workout.rep_quality.length,
  }));

  // Prepare chart data for rep quality over time
  const chartData = selectedWorkout
    ? {
        labels: selectedWorkout.rep_quality
          .map((_, index) => index )
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
      labels: []
        .map((_, index) => index + 1)
        .filter((num) => num % 5 === 0)
        .map(String),
      datasets: [
        {
          data: [],
          strokeWidth: 2,
        },
      ],
      name: '',
      date: '',
    };

  // Chart data for average rep quality per workout
  const averageChartData = {
    labels: averageRepQuality.map((item) => {
      const [year, month, day] = item.date.split('-');
      return `${month}-${day}`; // Show only the month and day
    }),
    datasets: [
      {
        data: averageRepQuality.map((item) => item.averageRepQuality),
        strokeWidth: 2,
      },
    ],
  };

  return (
    <View style={styles.container}>
      {/* First Line Chart: Rep Quality over Time */}
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
        <View style={styles.axisLabels1}>
          <Text style={styles.axisLabel1}>Rep Count</Text>
          <Text style={[styles.axisLabel1, styles.yAxisLabel1]}>Rep Quality</Text>
        </View>
      </LinearGradient>

      {/* Second Line Chart: Average Rep Quality per Workout */}
      <LinearGradient
        colors={['#4caf50', '#66bb6a']} // New color gradient for the second chart
        start={{ x: 0, y: 1 }} // Gradient starts from left
        end={{ x: 1, y: 0 }}
        style={styles.chartContainer}
      >
        <Text style={styles.chartTitle}>Average Rep Quality</Text>

        <LineChart
          data={averageChartData}
          width={screenWidth - 30} // Same width as the boxes
          height={200}
          chartConfig={{
            backgroundColor: '#388e3c',
            backgroundGradientFrom: '#4caf50',
            backgroundGradientTo: '#66bb6a',
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
        keyExtractor={(item) => item.id.toString()}
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
  chartContainer: {
    backgroundColor: '#fb8c00', // Orange box color
    padding: 0,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 5,
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
});
