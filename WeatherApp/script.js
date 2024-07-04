const apiKey = '5fd28d654e6992883a83491122b6e4f5'; // Replace with your OpenWeatherMap API key

document.getElementById('searchBtn').addEventListener('click', () => {
    const city = document.getElementById('cityInput').value;
    if (city) {
        getCoordinates(city);
    }
});

function getCoordinates(city) {
    fetch(`https://api.openweathermap.org/geo/1.0/direct?q=${city},US&limit=1&appid=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const { lat, lon } = data[0];
                fetchWeather(lat, lon);
            } else {
                alert('City not found. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error fetching city coordinates. Please try again.');
        });
}

function fetchWeather(lat, lon) {
    fetch(`https://api.openweathermap.org/data/3.0/onecall?lat=${lat}&lon=${lon}&exclude=minutely,hourly,daily,alerts&units=imperial&appid=${apiKey}`)
        .then(response => response.json())
        .then(data => {
            displayWeather(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error fetching weather data. Please try again.');
        });
}

function displayWeather(data) {
    const weatherInfo = document.getElementById('weatherInfo');
    const cityName = document.getElementById('cityName');
    const temperature = document.getElementById('temperature');
    const description = document.getElementById('description');
    const humidity = document.getElementById('humidity');
    const windSpeed = document.getElementById('windSpeed');

    cityName.textContent = document.getElementById('cityInput').value;
    temperature.textContent = `Temperature: ${Math.round(data.current.temp)}°F`;
    description.textContent = `Weather: ${data.current.weather[0].description}`;
    humidity.textContent = `Humidity: ${data.current.humidity}%`;
    windSpeed.textContent = `Wind Speed: ${data.current.wind_speed} mph`;

    weatherInfo.style.display = 'block';
}