const path = require("path")

const output_dir = 'static/bundles'


module.exports = {
  entry: ["./js/index.js"],
  output: {
    path: path.resolve(output_dir),
    filename: "[name].js",
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "babel-loader",
      },
      {
        test: /\.scss$/,
        use: [
          { loader: "style-loader", options: {sourceMap: true} },
          { loader: "css-loader" },
          { loader: "sass-loader", options: { 
            //includePaths: [path.resolve(__dirname, 'node_modules')],
            sourceMap: true
          } }, 
        ]
      },
      { test: /\.css$/, use: [{loader: "css-loader"}] },
    ]
  },
  plugins: [
  ],
}
