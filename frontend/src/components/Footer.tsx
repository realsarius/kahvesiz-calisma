import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  return (
    <footer className="w-full z-10">
      <div className="w-full mx-auto p-4 md:py-8">
        <div className="sm:flex sm:items-center sm:justify-between">
          <ul className="flex flex-wrap w-full items-center justify-center mb-6 text-sm sm:mb-0">
            <li>
              <Link to="/about" className="hover:underline me-4 md:me-6">Hakkımızda</Link>
            </li>
            <li>
              <Link to="/privacy" className="hover:underline me-4 md:me-6">Gizlilik</Link>
            </li>
            <li>
              <Link to="/license" className="hover:underline me-4 md:me-6">Lisans</Link>
            </li>
            <li>
              <Link to="/contact_us" className="hover:underline">Bize Ulaşın</Link>
            </li>
          </ul>
        </div>
        <hr className="my-6 w-2/4 mx-auto lg:my-4" />
        <span className="block text-sm text-center">
          © 2024 <Link to="/" className="hover:underline">Kahvesiz Çalışma™</Link>. Tüm hakları saklıdır.
        </span>
      </div>
    </footer>
  );
};

export default Footer;
