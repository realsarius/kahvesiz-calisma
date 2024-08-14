const path = require('path');

module.exports = {
    entry: './static/src/scripts/main.js', // Entry point for your JavaScript files
    output: {
        filename: 'bundle.js', // Output file
        path: path.resolve(__dirname, 'static/dist/js'), // Output directory
    },
    module: {
        rules: [
            {
                test: /\.js$/, // Apply Babel loader to .js files
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env']
                    }
                }
            },
            {
                test: /\.css$/, // Apply CSS loader
                use: ['style-loader', 'css-loader'],
            },
            {
                test: /\.svg$/, // Apply file loader to SVG files
                use: ['file-loader'],
            }
        ]
    },
    mode: 'development', // Change to 'production' for production builds
};
