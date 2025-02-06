import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Avatar,
    Button,
    TextField,
    Link,
    Grid,
    Box,
    Typography,
    Container,
    Alert,
    CircularProgress
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import axios from 'axios';
import './SignIn.css';

function SignIn() {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
    
        try {
            const response = await axios.post('http://localhost:5000/auth/login', {
                username: formData.username,
                password: formData.password,
            });
            const token = response.data.access_token;
            localStorage.setItem('token', token);  // Store the token in localStorage
            navigate('/dashboard');  // Redirect to the dashboard
        } catch (error) {
            console.error('Login error:', error.response?.data);
            setError(error.response?.data?.error || 'An unexpected error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container component="main" maxWidth="xs">
            <Box
                sx={{
                    marginTop: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                }}
            >
                <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
                    <LockOutlinedIcon />
                </Avatar>
                <Typography component="h1" variant="h5">
                    Sign In
                </Typography>
                {error && (
                    <Alert severity="error" sx={{ width: '100%', mt: 2 }}>
                        {error}
                    </Alert>
                )}
                <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1 }}>
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="username"
                        label="Username"
                        name="username"
                        autoComplete="username"
                        autoFocus
                        value={formData.username}
                        onChange={handleChange}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        name="password"
                        label="Password"
                        type="password"
                        id="password"
                        autoComplete="current-password"
                        value={formData.password}
                        onChange={handleChange}
                    />
                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        color="primary"
                        disabled={loading}
                        sx={{ mt: 3, mb: 2 }}
                    >
                        {loading ? <CircularProgress size={24} /> : 'Sign In'}
                    </Button>
                    <Grid container>
                        <Grid item>
                            <Link href="/signup" variant="body2">
                                {"Don't have an account? Sign Up"}
                            </Link>
                        </Grid>
                    </Grid>
                </Box>
            </Box>
        </Container>
    );
}

export default SignIn; 