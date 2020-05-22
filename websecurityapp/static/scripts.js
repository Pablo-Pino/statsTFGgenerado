// La funcio usada para las alertas al usar un boton para redireccionar
function alerta_redireccion(mensaje, url) {
    eval = window.confirm(mensaje);
    if (eval) 
        window.location.href = url;
}

// La funcion usada para poder seleccionar la pagina a seleccionar en la paginacion
// Se activa al pulsar el boton asociado a esta funcionalidad
function selecciona_pagina(n_pagina, pagina_param) {
    if (n_pagina != null) {
        uri = encodeURI('?' + pagina_param + '=' + n_pagina);
        window.location.href = uri;
    } else {
        window.location.href = '';
    }
}


// Ejemplo de script usado para iniciar sesion en una actividad consumiendo la API REST
async function inicia_sesionactividad(identificador) {
    // Usa la API REST para iniciar sesion en la actividad
    fetch(
        'http://localhost:8000/sesionactividad/comienzo/' + identificador + '/'
    ).then(
        // Usa los datos de la respuesta JSON para notificar al usuario si ha sido un éxito o un error
        (response) => {
            divAlert = document.getElementById('alert-div');
            divAlert.innerHTML = '';
            divMensaje = document.createElement('div');
            divMensaje.id = 'message-div';
            if (response.status == 200)
                divMensaje.className = 'alert alert-success';
            else if (response.status == 500)
                divMensaje.className = 'alert alert-danger';
            divAlert.appendChild(divMensaje);
            return response.json();
    }).then(
         // Usa los datos dados en la respuesta JSON generada para guardar el token de sesion y
         // notificar al usuario si ha sido un éxito o un error
        (data) => {
            console.log(data);
            Cookies.set('sesionactividad_token', data['token']);
            // console.log(Cookies.get('sesionactividad_token'));
            // console.log(Cookies.get('csrftoken'));
            divMensaje = document.getElementById('message-div');
            messageText = document.createTextNode(data['status']);
            divMensaje.appendChild(messageText);
    });
}

// Ejemplo de script usado para indicar que se ha completado una actividad consumiendo la API REST
async function finaliza_sesionactividad(identificador) {
    // Obtiene el token de sesión y el token CSRF a partir de las cookies
    token = Cookies.get('sesionactividad_token');
    csrfToken = Cookies.get('csrftoken');
    // Consume al API REST para indicar que el usuario ha finalizado la actividad
    fetch('http://localhost:8000/sesionactividad/final/' + identificador + '/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({token: token})
    }).then(
        // Usa los datos de la respuesta JSON para notificar al usuario si ha sido un éxito o un error
        (response) => {
            jsonResponse = response.json();
            divAlert = document.getElementById('alert-div');
            divAlert.innerHTML = '';
            divMensaje = document.createElement('div');
            divMensaje.id = 'message-div';
            if (response.status == 201)
                divMensaje.className = 'alert alert-success';
            else if (response.status == 500)
                divMensaje.className = 'alert alert-danger';
            divAlert.appendChild(divMensaje);
            return jsonResponse;
        }
    )
    .then(
         // Usa los datos dados en la respuesta JSON generada para notificar al usuario si ha sido un éxito o un error
        (data) => {
            // console.log(data);
            divMensaje = document.getElementById('message-div');
            messageText = document.createTextNode(data.status);
            divMensaje.appendChild(messageText);
        }
    );
}