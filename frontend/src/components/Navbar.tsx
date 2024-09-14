import React, {useState} from 'react';
import {Link} from 'react-router-dom';

interface NavbarProps {
    isAuthenticated: boolean;
    userName: string;
    userEmail: string;
    isAdmin: boolean;
    userCafeId?: string;
}

const Navbar: React.FC<NavbarProps> = ({
                                           isAuthenticated,
                                           userName,
                                           userEmail,
                                           isAdmin,
                                           userCafeId
                                       }) => {
    const [dropdownOpen, setDropdownOpen] = useState(false);

    return (
        <nav className="border-gray-200 z-50">
            <div className="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto p-4">
                <Link
                    to="/"
                    className="flex transition-colors duration-200 hover:text-lavender items-center space-x-3 rtl:space-x-reverse"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="w-20 h-20 block"
                        viewBox="0 0 64 64"
                        xmlSpace="preserve"
                    >
                        {/* Updated fill color to light brown */}
                        <path
                            style={{fill: 'rgb(210, 180, 140)'}}
                            d="m61.948 19.134-.885 4.764H30.075l-.885-4.764h32.758zm-19.45 26.555v2.2c0 3.028-1.302 5.751-3.369 7.659h16.054l1.829-9.86H42.498zM10.639 31.593V47.89c0 4.799 3.905 8.704 8.704 8.704H32.05c4.804 0 8.709-3.905 8.709-8.704V31.593h-30.12z"
                        ></path>
                        <path
                            style={{fill: 'rgb(139, 104, 72)'}}
                            d="M38.481 31.449v16.297c0 4.799-3.905 8.704-8.709 8.704h3.542c4.804 0 8.709-3.905 8.709-8.704V31.449h-3.542z"
                        ></path>
                        {/* Other SVG paths */}
                    </svg>
                    <span className="self-center text-2xl lg:text-4xl caveat-400 whitespace-nowrap">
                        Kahvesiz Çalışma
                    </span>
                </Link>
                <div className="flex items-center md:order-2 space-x-3 md:space-x-0 rtl:space-x-reverse">
                    {isAuthenticated ? (
                        <div className="relative inline-block text-left">
                            <button
                                id="dropdownAvatarNameButton"
                                onClick={() => setDropdownOpen(!dropdownOpen)}
                                className="flex items-center text-sm pe-1 font-medium text-gray-900 rounded-full hover:text-blue-600 dark:hover:text-lavender md:me-0 focus:ring-4 focus:ring-gray-100 dark:focus:ring-lavender/50 dark:text-white transition-colors duration-200"
                                type="button"
                            >
                                <span className="sr-only">Open user menu</span>
                                <img
                                    className="w-8 h-8 me-2 rounded-full"
                                    src={`https://api.dicebear.com/9.x/initials/svg?seed=${userName}`}
                                    alt="user photo"
                                />
                                {userName}
                                <svg
                                    className="w-2.5 h-2.5 ms-3"
                                    aria-hidden="true"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 10 6"
                                >
                                    <path
                                        stroke="currentColor"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="m1 1 4 4 4-4"
                                    ></path>
                                </svg>
                            </button>

                            {dropdownOpen && (
                                <div
                                    id="dropdownAvatarName"
                                    className="z-10 bg-white divide-y divide-gray-100 rounded-lg shadow w-44 dark:bg-zinc-900/75 dark:divide-zinc-600 backdrop-blur absolute right-0 mt-2 dark:border dark:border-lavender/25"
                                >
                                    <div className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                                        <div className="font-medium">{userName}</div>
                                        <div className="truncate">{userEmail}</div>
                                    </div>
                                    <ul className="py-2 text-sm text-gray-700 dark:text-gray-200">
                                        {isAdmin && (
                                            <li>
                                                <Link
                                                    to="/admin_dashboard"
                                                    className="block px-4 mx-1 py-2 rounded hover:bg-gray-100 dark:hover:bg-lavender/40 dark:hover:text-white transition-colors duration-200"
                                                >
                                                    Dashboard
                                                </Link>
                                            </li>
                                        )}
                                        <li>
                                            <Link
                                                to="/account"
                                                className="block px-4 mx-1 py-2 rounded hover:bg-gray-100 dark:hover:bg-lavender/40 dark:hover:text-white transition-colors duration-200"
                                            >
                                                Hesap
                                            </Link>
                                        </li>
                                        {userCafeId && !isAdmin && (
                                            <li>
                                                <Link
                                                    to={`/cafes/${userCafeId}`}
                                                    className="block px-4 mx-1 py-2 rounded hover:bg-gray-100 dark:hover:bg-lavender/40 dark:hover:text-white transition-colors duration-200"
                                                >
                                                    Benim Kafem
                                                </Link>
                                            </li>
                                        )}
                                    </ul>
                                    <div className="py-2">
                                        <Link
                                            to="/logout"
                                            className="block px-4 mx-1 py-2 rounded text-sm text-gray-700 hover:bg-gray-100 dark:hover:bg-lavender/40 dark:text-gray-200 dark:hover:text-white transition-colors duration-200"
                                        >
                                            Çıkış yap
                                        </Link>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <Link
                            to="/login"
                            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm dark:bg-lavender dark:text-zinc-950 inter-weight-500 transition-colors duration-200"
                        >
                            Giriş
                        </Link>
                    )}

                    <button
                        data-collapse-toggle="navbar-user"
                        type="button"
                        className="inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-500 rounded-lg md:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-600"
                        aria-controls="navbar-user"
                        aria-expanded="false"
                    >
                        <span className="sr-only">Open main menu</span>
                        <svg
                            className="w-5 h-5"
                            aria-hidden="true"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 17 14"
                        >
                            <path
                                stroke="currentColor"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M1 1h15M1 7h15M1 13h15"
                            ></path>
                        </svg>
                    </button>
                </div>

                <div
                    className="items-center justify-between hidden w-full md:flex md:w-auto md:order-1"
                    id="navbar-user"
                >
                    <ul className="flex flex-col p-4 md:p-0 mt-4 border border-gray-100 rounded-lg md:space-x-8 rtl:space-x-reverse md:flex-row md:mt-0 md:border-0 tracking-wide inter-weight-500">
                        <li>
                            <Link
                                to="/"
                                className="navbar-links block py-2 px-3 hover:text-lavender transition-colors duration-200 hover:drop-shadow-lg text-sm lg:text-lg"
                                aria-current="page"
                            >
                                Ana Sayfa
                            </Link>
                        </li>
                        <li>
                            <Link
                                to="/cafes"
                                className="navbar-links block py-2 px-3 hover:text-lavender transition-colors duration-200 hover:drop-shadow-lg text-sm lg:text-lg"
                            >
                                Kafeler
                            </Link>
                        </li>
                        <li>
                            <Link
                                to="/contact_us"
                                className="navbar-links block py-2 px-3 hover:text-lavender transition-colors duration-200 hover:drop-shadow-lg text-sm lg:text-lg"
                            >
                                Bize Ulaşın
                            </Link>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
