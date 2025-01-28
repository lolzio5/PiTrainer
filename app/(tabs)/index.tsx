import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, Dimensions } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { RootStackParamList } from '@/types';
import { NavigationProp } from '@react-navigation/native';
import { PieChart } from 'react-native-chart-kit';

interface WorkoutQuality {
  quality: string;
  reps: number;
}

interface Stat {
  label: string;
  value: string;
}

interface WorkoutData {
  workoutQualities: WorkoutQuality[];
}

const stats: Stat[] = [
  { label: 'Total Workouts', value: '15' },
  { label: 'Avg. Workout Time', value: '45 min' },
  { label: 'Calories Burned', value: '3,500' },
];

const renderStat = ({ item }: { item: Stat }) => (
  <View style={styles.statItem}>
    <Text style={styles.statValue}>{item.value}</Text>
    <Text style={styles.statLabel}>{item.label}</Text>
  </View>
);

const fetchWorkoutData = async (): Promise<WorkoutData | null> => {
  try {
    // Simulate fetching data from an API
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Example data - replace with actual API call
    const exampleData: WorkoutData = {
      workoutQualities: [
        { quality: 'Perfect', reps: 50 },
        { quality: 'Good', reps: 30 },
        { quality: 'Fair', reps: 15 },
        { quality: 'Poor', reps: 5 },
      ],
    };

    return exampleData;
  } catch (error) {
    console.error('Error fetching workout data:', error);
    return null;
  }
};

const processWorkoutData = (data: WorkoutData) => {
  const chartData = data.workoutQualities.map((item) => ({
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

  const totalReps = data.workoutQualities.reduce((sum, item) => sum + item.reps, 0);
  return { chartData, totalReps };
};

export default function Dashboard() {
  const navigation = useNavigation<NavigationProp<RootStackParamList>>();
  const [workoutData, setWorkoutData] = useState<{
    chartData: { name: string; population: number; color: string; legendFontColor: string; legendFontSize: number }[];
    totalReps: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchWorkoutData().then((data) => {
      if (data) {
        setWorkoutData(processWorkoutData(data));
      }
      setIsLoading(false);
    });
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.headerContainer}>
        <Text style={styles.header}>Enter App Name Here</Text>
      </View>
      <Text style={styles.subheader}>Your data at a glance</Text>
      <FlatList
        data={stats}
        renderItem={renderStat}
        keyExtractor={(item, index) => index.toString()}
        horizontal={true}
        showsHorizontalScrollIndicator={false}
        style={styles.statsList}
      />
      <View style={styles.pieChartContainer}>
        <Text style={styles.chartHeader}>Last Workout Breakdown</Text>
        {isLoading ? (
          <ActivityIndicator size="large" color="#0000ff" />
        ) : workoutData ? (
          <>
            <PieChart
              data={workoutData.chartData}
              width={Dimensions.get('window').width - 40} // Dynamic width
              height={220}
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
            <Text style={styles.totalRepsText}>
              Total Reps: {workoutData.totalReps}
            </Text>
          </>
        ) : (
          <Text>Failed to load workout data.</Text>
        )}
      </View>
    </View>
  );
}

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
  subheader: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 20,
    marginBottom: 10,
    color: '#555',
  },
  statsList: {
    marginBottom: 20,
  },
  statItem: {
    backgroundColor: '#fff',
    padding: 15,
    marginRight: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    width: 120,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
  },
  pieChartContainer: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
    elevation: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chartHeader: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  totalRepsText: {
    fontSize: 14,
  },
});
