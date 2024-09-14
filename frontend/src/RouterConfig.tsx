import React from 'react';
import {BrowserRouter, Routes, Route} from 'react-router-dom';
import App from './App';
import Home from './pages/Home';
import About from './pages/About';
import Privacy from './pages/Privacy';
import License from './pages/License';
import ContactUs from './pages/ContactUs';
import Login from './pages/Login';
import Signup from './pages/Signup';

const RouterConfig: React.FC = () => {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<App/>}>
                    <Route index element={<Home/>}/>
                    <Route path="about" element={<About/>}/>
                    <Route path="privacy" element={<Privacy/>}/>
                    <Route path="license" element={<License/>}/>
                    <Route path="contact_us" element={<ContactUs/>}/>
                    <Route path="login" element={<Login/>}/>
                    <Route path="signup" element={<Signup/>}/>
                </Route>
            </Routes>
        </BrowserRouter>
    );
};

export default RouterConfig;
