// app/(auth)/login.tsx
import { useState } from 'react';
import { TextInput, Button, Text, View } from 'react-native';
import axios from 'axios';
import { useAuth } from '../context';  // Import the useAuth hook

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { setToken } = useAuth();  // Get setToken from Auth Context

  const handleLogin = async () => {
    try {
      const response = await axios.post('http://18.170.31.251:80/api/login', {
        email,
        password,
      });

      // Get the access token from the response
      const accessToken = response.data.access_token;  // assuming the server sends `access_token`

      // Store the token using the context
      setToken(accessToken);

    } catch (err) {
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
    <View>
      <TextInput
        value={email}
        onChangeText={setEmail}
        placeholder="Email"
        keyboardType="email-address"
      />
      <TextInput
        value={password}
        onChangeText={setPassword}
        placeholder="Password"
        secureTextEntry
      />
      <Button title="Login" onPress={handleLogin} />
      {error && <Text>{error}</Text>}
      <Button
        title="Don't have an account? Register"
      />
    </View>
  );
}
