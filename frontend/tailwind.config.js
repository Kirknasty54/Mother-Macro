/** @type {import('tailwindcss').Config} */
//export default {
  // In Tailwind CSS v4, most configuration is now done in CSS
  // This file is kept for any JavaScript-based configuration if needed
//}
const withMT = require("@material-tailwind/react/utils/withMT");
module.exports = withMT({
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {},
    },
    plugins: [],
});