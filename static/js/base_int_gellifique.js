function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

var timerInterval; // Will be used to keep track of the interval that updates the timer
var startTime; // Will store the time when the spinner was created
var formattedTime;

function spinner_on() {
  // create the loading spinner element
  var spinner = document.createElement("div");
  spinner.className = "loading";
  spinner.innerHTML = `
    <div class="spinner"></div>
    <div class="timer">00:00</div>
  `;

  // append the spinner to the body
  document.body.appendChild(spinner);

  // Start the timer
  startTime = new Date(); // Capture the start time
  if (timerInterval) {
    clearInterval(timerInterval); // Clear any existing interval to avoid multiple timers running
  }
  timerInterval = setInterval(updateTimer, 1000); // Update the timer every second
}

function updateTimer() {
  var currentTime = new Date();
  var elapsedTime = currentTime - startTime; // Time elapsed in milliseconds
  var seconds = Math.floor(elapsedTime / 1000) % 60; // Convert to seconds
  var minutes = Math.floor(elapsedTime / (1000 * 60)); // Convert to minutes

  // Format time to always show two digits
  formattedTime =
    (minutes < 10 ? "0" + minutes : minutes) +
    ":" +
    (seconds < 10 ? "0" + seconds : seconds);

  // Update the timer element with the new time
  var timerElement = document.querySelector(".timer");
  if (timerElement) {
    timerElement.textContent = formattedTime;
  }
}

function spinner_off() {
  // remove the loading spinner element from the body
  var spinner = document.querySelector(".loading");
  if (spinner) {
    spinner.parentNode.removeChild(spinner);
  }

  // Stop the timer
  clearInterval(timerInterval);
}
