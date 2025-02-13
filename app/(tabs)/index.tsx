import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, Dimensions } from 'react-native';
import { PieChart } from 'react-native-chart-kit';
import { useAuth } from '../context';
import axios from 'axios';
import { useFocusEffect } from '@react-navigation/native';

interface WorkoutQuality {
  quality: string;
  reps: number;
}

type WorkoutData = WorkoutQuality[];

interface LifetimeMetrics {
  total_reps: number;
  total_workouts: number;
  total_calories_burned: number;
  lifetime_avg_rep_quality: number;
  best_workout: {
    date: string,
    exercise: string,
    avg_rep_quality: number,
  };
}

const renderStat = ({ item }: { item: { label: string; value: string } }) => (
  <View style={styles.statItem}>
    <Text style={styles.statValue}>{item.value}</Text>
    <Text style={styles.statLabel}>{item.label}</Text>
  </View>
);

const fetchWorkoutData = async (token: string | null): Promise<{
  lifetimeMetrics: LifetimeMetrics;
  lastWorkout: WorkoutData;
  feedback: string;
} | null> => {
  try {
    if (token) {
      // Use the token to access protected routes
       const response = await axios.get('http://3.10.117.27:80/api/home', {
          headers: {
            Authorization: `Bearer ${token}`,  // Send token in the request header
          },
        });
        const data = response.data;

        return {
            lifetimeMetrics: data.lifetime_metrics,
            lastWorkout: data.last_workout,
            feedback: data.feedback
        };
    }
    return null;
  } catch (error) {
    //console.error('Error fetching workout data:', error);
    return null;
  }
};

const processWorkoutData = (workoutQualities: WorkoutData) => {
  const chartData = workoutQualities.map((item) => ({
    name: item.quality,
    population: item.reps,
    color:
      item.quality === 'Perfect'
        ? 'green'
        : item.quality === 'Good'
        ? 'orange'
        : item.quality === 'Fair'
        ? 'yellow'
        : 'red',
    legendFontColor: '#333',
    legendFontSize: 14,
  }));

  const totalReps = workoutQualities.reduce((sum, item) => sum + item.reps, 0);
  return { chartData, totalReps };
};

export default function Dashboard() {
  const [workoutData, setWorkoutData] = useState<{
    chartData: { name: string; population: number; color: string; legendFontColor: string; legendFontSize: number }[] | null[];
    totalReps: number;
  } | null>(null);
  const [lifetimeMetrics, setLifetimeMetrics] = useState<LifetimeMetrics | null>(null);
  const [feedback, setFeedback] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const { token } = useAuth();
  
  useFocusEffect(
    useCallback(() => {
      fetchWorkoutData(token)
      .then((data) => {
        if (data) {
          setLifetimeMetrics(data.lifetimeMetrics);
          setWorkoutData(processWorkoutData(data.lastWorkout));  // Process the workout data
          setFeedback(data.feedback);
        }
      })
      .catch((error) => {
        console.error("Error in useEffect fetching data:", error);
      })
      .finally(() => {
        setIsLoading(false); // Ensure loading state is updated in both success and failure cases
      });
    }, []));


  const stats = [
    { label: 'Total Workouts', value: lifetimeMetrics?.total_workouts.toString() || 'N/A' },
    { label: 'Avg. Rep Quality', value: lifetimeMetrics?.lifetime_avg_rep_quality.toString() || 'N/A' },
    { label: 'Calories Burned', value: lifetimeMetrics?.total_calories_burned.toString() || 'N/A' },
    { label: 'Total Reps', value: lifetimeMetrics?.total_reps.toString() || 'N/A' },
  ];

  if (isLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#008000" />
          <Text style={styles.loadingText}>Loading home page...</Text>
        </View>
      );
    }

  return (
    <View style={styles.container}>
      <View style={styles.headerContainer}>
        <Text style={styles.header}>PiTrainer</Text>
        <Text style={styles.slogan}>Your gym Personal Trainer, in your pocket!</Text>
      </View>
      <Text style={styles.subheader}>Your data at a glance</Text>
  
      {/* Row containing Best Workout Box and FlatList */}
      <View style={styles.rowContainer}>
        {/* Best Workout Box */}
        <View style={styles.bestWorkoutContainer}>
          <View style={styles.bestWorkoutLeft}>
            <Text style={styles.bestWorkoutLabel}>Best Workout:</Text>
            <Text style={styles.bestWorkoutValue}>{lifetimeMetrics?.best_workout.exercise}</Text>
            <Text style={styles.bestWorkoutDate}>Date: {lifetimeMetrics?.best_workout.date}</Text>
            <Text style={styles.bestWorkoutQuality}>Avg Rep Quality: {lifetimeMetrics?.best_workout.avg_rep_quality}</Text>
          </View>
        </View>
  
        {/* FlatList on the right */}
        <View style={{ flex: 1 }}>
          <FlatList
            data={stats}
            renderItem={renderStat}
            keyExtractor={(item, index) => index.toString()}
            horizontal={false}
            showsHorizontalScrollIndicator={false}
            style={[styles.statsList, { height: '30%' }]}
          />
        </View>
      </View>
  
      {/* Pie Chart Container */}
      <View style={styles.pieChartContainer}>
        <Text style={styles.chartHeader}>Last Workout Breakdown</Text>
        {workoutData ? (
          <>
            <PieChart
              data={workoutData.chartData}
              width={Dimensions.get('window').width - 40} // Dynamic width (screen width minus padding)
              height={200}
              chartConfig={{
                backgroundGradientFrom: '#fff',
                backgroundGradientTo: '#fff',
                color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              }}
              accessor={'population'}
              backgroundColor={'transparent'}
              paddingLeft={'15'}
              absolute // Show actual values instead of percentages
            />
            <Text style={styles.totalRepsText}>Total Reps: {workoutData.totalReps}</Text>
            <Text style={styles.feedbackText}>{feedback}</Text>
          </>
        ) : (
          <Text>Failed to load workout data.</Text>
        )}
      </View>
    </View>
  );}
  const styles = StyleSheet.create({
    container: {
      flex: 1,
      padding: 20,
      backgroundColor: '#f4f4f4',
    },
    headerContainer: {
      paddingTop: 30,
      marginBottom: 0,
    },
    header: {
      fontSize: 24,
      fontWeight: 'bold',
      marginBottom: 10,
      color: '#333',
    },
    slogan: {
      fontSize: 15,
      marginBottom: 5,
      fontStyle: 'italic',
      color: '#333',
    },
    subheader: {
      fontSize: 18,
      fontWeight: '600',
      marginTop: 20,
      marginBottom: 10,
      color: '#555',
    },
    statsList: {
      marginBottom: 10,
    },
    statItem: {
      backgroundColor: '#fff',
      padding: 20,
      marginRight: 0,
      marginBottom: 5,
      borderRadius: 8,
      alignItems: 'center',
      justifyContent: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 1.41,
      elevation: 2,
      flex: 1,
    },
    statValue: {
      fontSize: 18,
      fontWeight: 'bold',
      color: '#333',
      alignItems: 'center',
      justifyContent: 'center',
    },
    statLabel: {
      fontSize: 14,
      color: '#666',
      alignItems: 'center',
      justifyContent: 'center',
    },
    pieChartContainer: {
      backgroundColor: '#fff',
      padding: 15,
      borderRadius: 8,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 1.41,
      elevation: 2,
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%', // Ensure the pie chart takes full width
    },
    chartHeader: {
      fontSize: 16,
      fontWeight: 'bold',
      marginBottom: 0,
    },
    totalRepsText: {
      fontSize: 14,
      paddingBottom: 5,
      fontWeight: 'bold',
    },
    feedbackText: {
      fontSize: 14,
      paddingBottom: 5,
    },
    bestWorkoutContainer: {
      justifyContent: 'center',
      backgroundColor: '#fff',
      padding: 20,
      borderRadius: 8,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 1.41,
      elevation: 2,
      alignItems: 'center',
      flex: 1,  // Ensure it stretches to fit the height and width
      marginRight: 5, // Add margin to separate it from the FlatList
      marginBottom: 10,
    },
    bestWorkoutLeft: {
      flex: 1,
      justifyContent: 'center', // Center the content vertically
    },
    bestWorkoutLabel: {
      fontWeight: 'bold',
      fontSize: 16,
    },
    bestWorkoutValue: {
      fontSize: 14,
    },
    bestWorkoutDate: {
      fontSize: 14,
      color: '#888',
    },
    bestWorkoutQuality: {
      fontSize: 14,
      color: '#888',
    },
    rowContainer: {
      flexDirection: 'row', // Align children in a row
      justifyContent: 'space-between', // Space them out
      alignItems: 'flex-start', // Align vertically at the top
      width: '100%', // Ensure the row takes the full width
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
  });
  