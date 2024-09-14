import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const Signup: React.FC = () => {
    const [message, setMessage] = useState<string | null>(null);
    const [messageType, setMessageType] = useState<'success' | 'error' | null>(null);

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const formData = new FormData(event.currentTarget);
        const name = formData.get('name') as string;
        const email = formData.get('email') as string;
        const password = formData.get('password') as string;

        try {
            const response = await fetch('http://localhost:5000/api/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, password }),
            });

            const result = await response.json();

            if (response.ok) {
                setMessage(result.message);
                setMessageType('success');
                setTimeout(() => (window.location.href = '/login'), 2000);
            } else {
                setMessage(result.error);
                setMessageType('error');
            }
        } catch (error) {
            setMessage('An unexpected error occurred.');
            setMessageType('error');
        }
    };

    return (
        <main className="container mx-auto p-6 max-w-md">
            <h1 className="text-3xl font-bold mb-6">Kayıt Ol</h1>

            <div id="message-container" className="mb-4">
                {message && (
                    <div className={`text-sm p-2 rounded ${messageType === 'success' ? 'text-green-300' : 'text-red-300'}`}>
                        {message}
                    </div>
                )}
            </div>

            <form id="signup-form" className="space-y-4" onSubmit={handleSubmit} noValidate>
                <div className="form-group">
                    <label htmlFor="name" className="block text-sm font-medium">İsim</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        className="mt-1 block w-full p-2 border border-zinc-600 rounded-md shadow-sm dark:bg-zinc-900/20 dark:text-zinc-50 backdrop-blur"
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="email" className="block text-sm font-medium">E-posta</label>
                    <input
                        type="email"
                        id="email"
                        name="email"
                        className="mt-1 block w-full p-2 border border-zinc-600 rounded-md shadow-sm dark:bg-zinc-900/20 dark:text-zinc-50 backdrop-blur"
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password" className="block text-sm font-medium">Şifre</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        className="mt-1 block w-full p-2 border border-zinc-600 rounded-md shadow-sm dark:bg-zinc-900/20 dark:text-zinc-50 backdrop-blur"
                        required
                    />
                </div>

                <button
                    type="submit"
                    className="w-full py-2 px-4 rounded-lg shadow-md bg-zinc-900 text-zinc-50 hover:bg-zinc-700 active:bg-zinc-600 dark:bg-zinc-50 dark:text-zinc-950 dark:hover:bg-zinc-300 dark:active:bg-zinc-400"
                >
                    Kayıt Ol
                </button>

                <p className="mt-4 text-sm text-center">
                    <span>Hesabınız var mı?&nbsp;</span>
                    <Link to="/login" className="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
                        Buradan giriş yapın
                    </Link>
                </p>
            </form>
        </main>
    );
};

export default Signup;
