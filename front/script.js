const API_URL = 'http://127.0.0.1:8000';
let user = null;
let tokenValue = null;
const tokenKey = 'token';
let token = null;

// Функция для подписки на журнал
async function subscribeToJournal(journalId) {
    try {
        const response = await fetch(`${API_URL}/subscriptions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ journal_id: journalId }) // Передаем ID журнала
        });

        if (!response.ok) {
            throw new Error('Ошибка при подписке на журнал');
        }

        // Успешная подписка, перезагружаем страницу
        location.reload();
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// Функция для отписки от журнала
async function unsubscribeFromJournal(journalId) {
    try {
        const response = await fetch(`${API_URL}/subscriptions/${journalId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Ошибка при отписке от журнала');
        }

        // Успешная отписка, перезагружаем страницу
        location.reload();
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось отписаться от журнала. Пожалуйста, попробуйте еще раз.');
    }
}

function updateNavLinks() {
    const loginLink = document.getElementById('login-link');
    const registerLink = document.getElementById('register-link');

    if (user !== null) {
        // Если пользователь авторизован, скрываем ссылки на Login и Register
        loginLink.style.display = 'none';
        registerLink.style.display = 'none';

        const logoutLink = document.createElement('a');
        logoutLink.href = '#'; // Устанавливаем href в '#', чтобы избежать перехода по ссылке
        logoutLink.id = 'logout-link'; // Устанавливаем id для дальнейшего обращения
        logoutLink.innerText = 'Logout';

        // Добавляем обработчик события на клик
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault(); // Отменяем стандартное поведение ссылки
            logout(); // Вызываем функцию logout
            updateNavLinks(); // Обновляем навигацию после выхода
            location.reload(); // Перезагружаем страницу
        });

        // Вставляем кнопку Logout перед Create Post
        const navLinks = document.querySelector('.nav-links');
        navLinks.insertAdjacentHTML('beforeend', "<a href=\"create_post.html\">Create Post</a><a href=\"create_journal.html\">Create Journal</a>");
        navLinks.insertBefore(logoutLink, navLinks.firstChild);

    } else {
        // Если пользователь не авторизован, показываем ссылки на Login и Register
        loginLink.style.display = 'inline';
        registerLink.style.display = 'inline';
    }
}


function parseJwt(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
}

function checkUser() {
    const token_ = sessionStorage.getItem(tokenKey);
    console.log(token_);
    if (token_) {
        user = parseJwt(token_);
        token = sessionStorage.getItem('token');
    } else {
        token = "";
    }
}

async function register(event) {
    event.preventDefault();

    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    try {
        const response = await fetch(`${API_URL}/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        document.getElementById('registerMessage').innerText = data.detail || 'Registration successful!';
        window.location.href = '/notification_service/front/index.html';
    } catch (error) {
        document.getElementById('registerMessage').innerText = 'Error during registration';
        console.error(error);
    }
}


function logout() {
    sessionStorage.removeItem('token'); // Удаляем токен из sessionStorage
    updateNavLinks();
    location.reload(); // Перезагружаем страницу
}

async function login(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const formData = new FormData();
        formData.append('grant_type', 'password');
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            sessionStorage.setItem('token', data.access_token);
            window.location.href = '/notification_service/front/index.html';
        } else {
            document.getElementById('loginMessage').innerText = data.detail || 'Login failed!';
        }
    } catch (error) {
        document.getElementById('loginMessage').innerText = 'Error during login';
        console.error(error);
    }
}

async function fetchSubscriptions() {
    const response = await fetch(`${API_URL}/subscriptions`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (response.ok) {
        const subscriptions = await response.json();
        return subscriptions.map(sub => sub.journal_id); // Предполагаем, что у подписки есть поле journal_id
    } else {
        console.error('Failed to fetch subscriptions:', response.statusText);
        return [];
    }
}

async function loadJournals() {
    const searchQuery = document.getElementById('search').value;

    try {
        let response;
        if (searchQuery === "") {
            response = await fetch(`${API_URL}/journals/`);
        } else {
            response = await fetch(`${API_URL}/journals/search?query=${searchQuery}`);
        }

        let journals = await response.json();


        const journalsDiv = document.getElementById('journals');
        journalsDiv.innerHTML = '';

        const subscriptions = await fetchSubscriptions();
        console.log(subscriptions);
        const searchTerm = document.getElementById('search').value;
        const subscribed = document.getElementById('subscribedCheckbox').checked;
        const owned = document.getElementById('ownedCheckbox').checked;

        if (owned && user !== null) {
            journals = journals.filter((journal) => journal.user_id === user.user_id)
        }

        if (subscribed && user !== null) {
            journals = journals.filter((journal) => subscriptions.includes(journal.id))
        }

        journals.forEach(journal => {
            const journalElement = document.createElement('div');
            const title = document.createElement('h3');

            const titleText = document.createElement('span');
            titleText.textContent = journal.name;

            // Добавляем функциональность удаления при клике на заголовок
            if (user !== null && journal.user_id === user.user_id) {
                const deleteLink = document.createElement('span');
                deleteLink.textContent = ' (Удалить)';
                deleteLink.style.color = 'red';
                deleteLink.style.cursor = 'pointer';

                deleteLink.onclick = async () => {
                    const confirmation = confirm(`Вы уверены, что хотите удалить журнал "${journal.name}"?`);
                    if (confirmation) {
                        try {
                            const deleteResponse = await fetch(`${API_URL}/journals/${journal.id}`, {
                                method: 'DELETE',
                                headers: {
                                    'Authorization': `Bearer ${token}`
                                },
                            });

                            if (deleteResponse.ok) {
                                alert('Журнал успешно удален.');
                                window.location.href = '/notification_service/front/index.html';
                            } else {
                                alert('Ошибка при удалении журнала.');
                            }
                        } catch (error) {
                            console.error('Ошибка:', error);
                        }
                    }
                };

                titleText.appendChild(deleteLink); // Добавляем ссылку на удаление к заголовку
            }

            title.appendChild(titleText);
            journalElement.appendChild(title);

            // Кнопка подписки
            const subscriptionButton = document.createElement('button');

            // Проверяем, есть ли у пользователя подписка на этот журнал
            if (subscriptions.includes(journal.id)) {
                subscriptionButton.innerText = 'Unsubscribe'; // Изменяем текст кнопки
                subscriptionButton.onclick = () => unsubscribeFromJournal(journal.id);
                subscriptionButton.style.backgroundColor = "red";
            } else {
                subscriptionButton.innerText = 'Subscribe';
                subscriptionButton.onclick = () => subscribeToJournal(journal.id);
            }
            if (user == null) {
                subscriptionButton.disabled = true;
                subscriptionButton.style.backgroundColor = "grey";
            }
            journalElement.appendChild(subscriptionButton);

            journalsDiv.appendChild(journalElement);
        });

    } catch (error) {
        console.error(error);
    }
}

async function createPost() {
    try {
        response = await fetch(`${API_URL}/journals/`);
        let journals = await response.json();
        journals = journals.filter((journal) => journal.user_id === user.user_id);

                    const select = document.getElementById('journalSelect');

            select.innerHTML = '';

            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.disabled = true;
            defaultOption.selected = true;
            defaultOption.textContent = '-- Выберите журнал --';
            select.appendChild(defaultOption);

            journals.forEach(journal => {
                const option = document.createElement('option');
                option.value = journal.id;
                option.textContent = journal.name;
                select.appendChild(option);
            });

    } catch (error) {
        console.error(error);
    }
}

if (document.getElementById("createPostForm")) {
    document.getElementById("createPostForm").onsubmit = async function (event) {
        event.preventDefault();

        const journal_id = document.getElementById("journalSelect").value;
        const postText = document.getElementById("postContent").value;

        try {
            const response = await fetch(`${API_URL}/posts`, { // Замените на ваш API
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({journal_id, text: postText})
            });

            if (!response.ok) throw new Error('Ошибка при публикации поста');

            alert('Пост успешно опубликован!');

            window.location.href = '/notification_service/front/index.html';
        } catch (error) {
            console.error('Ошибка:', error);
        }
    }
}

if (document.getElementById("createJournalForm")) {
    document.getElementById('createJournalForm').addEventListener('submit', async function(event) {
        event.preventDefault(); // Предотвращаем стандартное поведение формы

        const name = document.getElementById('journalName').value;

        try {
            const response = await fetch(`${API_URL}/journals`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name }),
            });

            if (!response.ok) {
                throw new Error('Ошибка при создании журнала');
            }

            const result = await response.json();
            alert('Журнал успешно создан: ' + result.name);

            // Очистка поля ввода после успешного создания
            window.location.href = '/notification_service/front/index.html';
        } catch (error) {
            console.error('Ошибка:', error);
        }
    })
}

window.onload = () => {
    checkUser();
    if (window.location.pathname === "/notification_service/front/index.html") {
        updateNavLinks();
        loadJournals();
    }
    if (window.location.pathname === "/notification_service/front/create_post.html") {
        createPost();
    }
    // loadJournals(); // Загружаем журналы
};