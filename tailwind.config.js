/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./static/src/**/*.js"],
  theme: {
    extend: {
      colors: {
        // Light mode colors
        'kahve-yellow': '#F6E96B',
        'kahve-light-green': '#BEDC74',
        'kahve-medium-green': '#A2CA71',
        'kahve-dark-green': '#387F39',

        // Dark mode colors
        'kahve-dark-yellow': '#D4C54E',
        'kahve-dark-light-green': '#9BCA5F',
        'kahve-dark-medium-green': '#7EAB4B',
        'kahve-dark-dark-green': '#2D5A2E',

        'soft-pink': '#ff80b5',
        'soft-purple': '#9089fc',
        'deep-blue': 'rgb(23, 21, 59)',
        'midnight-blue': 'rgb(46, 35, 108)',
        'dark-purple': 'rgb(67, 61, 139)',
        // 'lavender': 'rgb(200, 172, 214)',
        'lavender': '#d2b48c',

        'pale-beige': '#f5f5dc',
        'light-tan': '#d8cfc4',
        'sandy-brown': '#f4a460',
        'light-brown': '#d2b48c',
        'medium-beige': '#c6a69b',
        'golden-beige': '#e4b965',
        'light-cocoa': '#b17a5a',
        'soft-mocha': '#a89f91',
        'dusty-rose': '#d7a7a0',
        'cinnamon-brown': '#a0522d',
      },
    },
  },
  plugins: [],
};
