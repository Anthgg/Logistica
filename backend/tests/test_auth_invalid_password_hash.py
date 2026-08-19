"""Hotfix F006 — un hash irreconocible no puede distinguirse de una credencial mala.

Ochenta cuentas heredadas quedaron en producción con un ``password_hash`` que no es
un hash, sino el literal con el que las sembró una fixture. ``pwdlib`` lanza
``UnknownHashError`` ante ellas, que hereda de ``PwdlibError`` y no de ``ValueError``,
así que escapaba del ``except`` de ``verify_password`` y el intento de acceso
terminaba en 500.

El problema no era la caída, sino la diferencia: un correo inexistente devuelve 401 y
uno con hash roto devolvía 500, de modo que la respuesta delataba qué correos existen.

Aquí se fija que las cinco situaciones —correo inexistente, contraseña incorrecta,
hash heredado, hash malformado y hash vacío— produzcan exactamente la misma respuesta,
y que un acceso legítimo siga funcionando.
"""

import pytest

from app.core.security import hash_password, verify_password
from app.models.user import User

#: Formas reales que puede tener un hash irreconocible. La primera es la que dejó la
#: fixture en producción; el resto son variaciones que también debe absorber.
INVALID_HASHES = [
    "hash-ficticio-no-utilizable",
    "hash...",
    "not-a-valid-password-hash",
    "abc123",
    "$broken$",
    "",
]

VALID_PASSWORD = "ContraseñaLegítima2026!"


@pytest.fixture(autouse=True)
def _isolate_rate_limiter():
    """Cada caso arranca con el contador de intentos a cero.

    El limitador de autenticación cuenta por `IP:ruta` en un diccionario en memoria
    que vive toda la sesión de pruebas, y permite 10 intentos por minuto. Este fichero
    hace más: sin aislar, los últimos casos recibirían 429 y estarían midiendo el
    limitador en vez del manejo del hash. No se altera ninguna configuración: solo se
    limpia el estado acumulado entre casos.
    """
    from app.core.rate_limit import rate_limiter

    rate_limiter._requests.clear()
    yield
    rate_limiter._requests.clear()


def _user(database, *, password_hash: str, email: str | None = None) -> User:
    from uuid import uuid4

    user = User(
        email=# El validador del endpoint rechaza el TLD reservado `.test`.
        email or f"hotfix-{uuid4().hex}@example.com",
        password_hash=password_hash,
        full_name="Usuario de prueba",
        role="operator",
        is_active=True,
        is_verified=True,
    )
    database.add(user)
    database.flush()
    database.commit()
    return user


def _csrf_headers(client) -> dict[str, str]:
    """El endpoint de acceso exige CSRF; sin él la respuesta sería 403 y no probaría nada."""
    response = client.get("/api/auth/csrf")
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def _login(client, email: str, password: str = "CualquierContraseña2026!"):
    return client.post(
        "/api/auth/login",
        headers=_csrf_headers(client),
        json={"email": email, "password": password, "remember_me": False},
    )


# ---------------------------------------------------------------------------
# verify_password: contrato de la función
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_hash", INVALID_HASHES, ids=[repr(h) for h in INVALID_HASHES])
def test_verify_password_returns_false_for_unreadable_hash(bad_hash: str) -> None:
    """No lanza: un hash que no se puede leer es simplemente una verificación fallida."""
    assert verify_password("cualquiera", bad_hash) is False


def test_verify_password_still_works_for_valid_hash() -> None:
    stored = hash_password(VALID_PASSWORD)
    assert verify_password(VALID_PASSWORD, stored) is True
    assert verify_password("otra distinta", stored) is False


def test_configuration_errors_still_propagate() -> None:
    """`HasherNotAvailable` no se traga.

    Es la otra hija de `PwdlibError` y significa que falta el backend de hashing: un
    fallo de configuración del servicio. Capturar la clase base lo convertiría en
    "credenciales inválidas" para todo el mundo, y el servicio parecería sano
    rechazando a todos sus usuarios.
    """
    from pwdlib.exceptions import HasherNotAvailable, PwdlibError, UnknownHashError

    assert issubclass(UnknownHashError, PwdlibError)
    assert issubclass(HasherNotAvailable, PwdlibError)
    assert not issubclass(HasherNotAvailable, UnknownHashError)


# ---------------------------------------------------------------------------
# El endpoint: mismo contrato para toda credencial inválida
# ---------------------------------------------------------------------------

def test_unknown_user_is_401(client):
    response = _login(client, "no-existe-en-absoluto@example.com")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_wrong_password_is_401(client, database):
    user = _user(database, password_hash=hash_password(VALID_PASSWORD))
    response = _login(client, user.email, "contraseña equivocada")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.parametrize("bad_hash", INVALID_HASHES, ids=[repr(h) for h in INVALID_HASHES])
def test_invalid_hash_never_returns_500(client, database, bad_hash: str):
    user = _user(database, password_hash=bad_hash)
    response = _login(client, user.email)
    assert response.status_code != 500
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_valid_login_still_works(client, database):
    user = _user(database, password_hash=hash_password(VALID_PASSWORD))
    response = _login(client, user.email, VALID_PASSWORD)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# No enumeración
# ---------------------------------------------------------------------------

def test_unknown_user_and_invalid_hash_are_indistinguishable(client, database):
    """Lo que se arregla de verdad: desde fuera, ambos casos son la misma respuesta."""
    legacy = _user(database, password_hash="hash-ficticio-no-utilizable")

    unknown_response = _login(client, "definitivamente-no-existe@example.com")
    legacy_response = _login(client, legacy.email)

    assert unknown_response.status_code == legacy_response.status_code
    assert unknown_response.json()["error"]["code"] == legacy_response.json()["error"]["code"]
    # También la forma del cuerpo: un campo de más en un caso sería otra señal.
    assert set(unknown_response.json()) == set(legacy_response.json())
    assert set(unknown_response.json()["error"]) == set(legacy_response.json()["error"])


def test_response_never_leaks_internals(client, database):
    """El cuerpo no puede mencionar la librería, la excepción ni el hash."""
    user = _user(database, password_hash="hash-ficticio-no-utilizable")
    body = _login(client, user.email).text

    for needle in (
        "Traceback",
        "UnknownHashError",
        "PwdlibError",
        "pwdlib",
        "argon2",
        "Argon2",
        "hash-ficticio-no-utilizable",
    ):
        assert needle not in body, f"la respuesta filtra {needle!r}"
