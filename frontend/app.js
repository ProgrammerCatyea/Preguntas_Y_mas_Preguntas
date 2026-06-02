const API = "http://127.0.0.1:8000";





async function register() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    if (!username || !password) {
        alert("Complete todos los campos");
        return;
    }

    try {

        const response = await fetch(
            `${API}/register?username=${username}&password=${password}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (response.ok) {

            alert("Usuario registrado correctamente");

        } else {

            alert(data.detail);
        }

    } catch (error) {

        console.error(error);
        alert("Error conectando con el servidor");
    }
}




async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    if (!username || !password) {
        alert("Complete todos los campos");
        return;
    }

    try {

        const response = await fetch(
            `${API}/login?username=${username}&password=${password}`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (response.ok) {

            localStorage.setItem(
                "user_id",
                data.id
            );

            localStorage.setItem(
                "username",
                data.username
            );

            localStorage.setItem(
                "points",
                data.points
            );

            window.location.href = "game.html";

        } else {

            alert(data.detail);
        }

    } catch (error) {

        console.error(error);
        alert("Error conectando con el servidor");
    }
}



let questions = [];
let currentQuestion = 0;



async function loadQuestions() {

    try {

        const response =
            await fetch(`${API}/questions`);

        questions =
            await response.json();

        showQuestion();

    } catch (error) {

        console.error(error);
    }
}




function showQuestion() {

    if (currentQuestion >= questions.length) {

        alert("Trivia finalizada");

        window.location.href =
            "ranking.html";

        return;
    }

    const q =
        questions[currentQuestion];

    document.getElementById("question")
        .innerText = q.question;

    document.getElementById("btnA")
        .innerText = q.option_a;

    document.getElementById("btnB")
        .innerText = q.option_b;

    document.getElementById("btnC")
        .innerText = q.option_c;

    document.getElementById("btnD")
        .innerText = q.option_d;
}




async function answer(letter) {

    const userId =
        localStorage.getItem("user_id");

    const question =
        questions[currentQuestion];

    try {

        const response =
            await fetch(
                `${API}/answer?user_id=${userId}&question_id=${question.id}&answer=${letter}`,
                {
                    method: "POST"
                }
            );

        const data =
            await response.json();

        if (data.correct) {

            alert(" Correcto");

        } else {

            alert("Incorrecto");
        }

        document.getElementById("score")
            .innerText =
            data.new_points;

        localStorage.setItem(
            "points",
            data.new_points
        );

        currentQuestion++;

        showQuestion();

    } catch (error) {

        console.error(error);
    }
}




async function loadRanking() {

    try {

        const response =
            await fetch(`${API}/ranking`);

        const users =
            await response.json();

        let html = "";

        users.forEach((user, index) => {

            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${user.username}</td>
                    <td>${user.points}</td>
                </tr>
            `;

        });

        document.getElementById("rankingBody")
            .innerHTML = html;

    } catch (error) {

        console.error(error);
    }
}




async function loadPodium() {

    try {

        const response =
            await fetch(`${API}/podium`);

        const podium =
            await response.json();

        if (podium.length > 0) {

            document.getElementById("goldName")
                .innerText =
                podium[0]?.username || "-";

            document.getElementById("goldPoints")
                .innerText =
                podium[0]?.points || 0;
        }

        if (podium.length > 1) {

            document.getElementById("silverName")
                .innerText =
                podium[1]?.username || "-";

            document.getElementById("silverPoints")
                .innerText =
                podium[1]?.points || 0;
        }

        if (podium.length > 2) {

            document.getElementById("bronzeName")
                .innerText =
                podium[2]?.username || "-";

            document.getElementById("bronzePoints")
                .innerText =
                podium[2]?.points || 0;
        }

    } catch (error) {

        console.error(error);
    }
}




let socket = null;

function connectWebSocket() {

    const username =
        localStorage.getItem("username");

    if (!username)
        return;

    socket =
        new WebSocket(
            `ws://127.0.0.1:8000/ws/${username}`
        );

    socket.onmessage = function(event) {

        const chat =
            document.getElementById("chat");

        if (!chat)
            return;

        chat.innerHTML +=
            `<p>${event.data}</p>`;

        chat.scrollTop =
            chat.scrollHeight;
    };
}




function sendMessage() {

    const input =
        document.getElementById("message");

    if (!input.value)
        return;

    socket.send(
        input.value
    );

    input.value = "";
}