var slider = document.getElementById("cooking-time-range")
var output = document.getElementById("cooking-time-span-value");
output.innerHTML = slider.value; // Display the default slider value

// Update the current slider value (each time you drag the slider handle)
slider.oninput = function() {
  output.innerHTML = this.value;
}
