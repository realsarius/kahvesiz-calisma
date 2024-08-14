/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./static/src/scripts/main.js":
/*!************************************!*\
  !*** ./static/src/scripts/main.js ***!
  \************************************/
/***/ (() => {

eval("document.addEventListener(\"DOMContentLoaded\", function () {\n  var dropdownButton = document.getElementById(\"dropdownAvatarNameButton\");\n  var dropdownMenu = document.getElementById(\"dropdownAvatarName\");\n  if (dropdownButton && dropdownMenu) {\n    dropdownButton.addEventListener(\"click\", function () {\n      dropdownMenu.classList.toggle(\"hidden\");\n    });\n\n    // Optional: Close the dropdown if clicked outside\n    document.addEventListener(\"click\", function (event) {\n      if (!dropdownButton.contains(event.target) && !dropdownMenu.contains(event.target)) {\n        dropdownMenu.classList.add(\"hidden\");\n      }\n    });\n  }\n});\ndocument.addEventListener(\"DOMContentLoaded\", function () {\n  var toggles = document.querySelectorAll(\"[data-dial-toggle]\");\n  var plusSvg = document.getElementById('plus-svg');\n  toggles.forEach(function (toggle) {\n    toggle.addEventListener(\"click\", function () {\n      var targetId = this.getAttribute(\"data-dial-toggle\");\n      var target = document.getElementById(targetId);\n      if (target) {\n        target.classList.toggle(\"flex\");\n        plusSvg.classList.toggle('rotate-45');\n        target.classList.toggle(\"hidden\");\n      }\n    });\n  });\n});\ndocument.addEventListener('DOMContentLoaded', function () {\n  var toast = document.getElementById('toast-message-cta');\n  var toastLink = document.getElementById('show-add-cafe-toast');\n  var closeButton = toast.querySelector('[data-dismiss-target=\"#toast-message-cta\"]');\n  toastLink.addEventListener('click', function (event) {\n    event.preventDefault(); // Prevent the default link action\n    toast.classList.remove('hidden'); // Show the toast\n\n    setTimeout(function () {\n      toast.classList.add('hidden');\n    }, 10000);\n  });\n  closeButton.addEventListener('click', function () {\n    toast.classList.add('hidden'); // Hide the toast when close button is clicked\n  });\n});\n\n//# sourceURL=webpack://day-88/./static/src/scripts/main.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./static/src/scripts/main.js"]();
/******/ 	
/******/ })()
;