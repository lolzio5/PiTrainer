import { useState } from 'react';
import { TextInput, Button, Text } from 'react-native';
import axios from 'axios';

export default function RegisterScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async () => {
    try {
        const response = await axios.post('http://18.170.31.251:80/api/signup', {
        email,
        password,
      });
    
    } catch (err) {
      setError('Registration failed. Please try again.');
    }
  };

  return (
    <div>
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
      <Button title="Register" onPress={handleRegister} />
      {error && <Text>{error}</Text>}
    </div>
  );
}
