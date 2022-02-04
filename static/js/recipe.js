var test = document.getElementById('flexSwitchCheckChecked')
var test1 = document.getElementById('flexSwitchCheckCheckedLabel')
test1.innerHTML = test.value; // Default measurement is metric

test.addEventListener("change", function() {
    if (this.checked) {
        test1.innerHTML = 'Metric'
    }
    else {
        test1.innerHTML = 'Imperial'
    }
} )

//TODO: When number of servings change...