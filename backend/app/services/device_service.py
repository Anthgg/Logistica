from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.security import generate_device_token, hash_device_token
from app.database.base import utc_now
from app.models.device import Device
from app.models.user import User
from app.repositories.device_repository import DeviceRepository


@dataclass
class DeviceResult:
    device: Device
    raw_token: str | None


class DeviceService:
    def __init__(self) -> None:
        self.repository = DeviceRepository()

    def recognize(
        self,
        database: Session,
        user: User,
        raw_device_token: str | None,
        user_agent: str | None,
    ) -> DeviceResult:
        # 1. Intentar reconocer por cookie device_token
        device = None
        if raw_device_token:
            device = self.repository.get_for_user_by_identifier(
                database, user.id, hash_device_token(raw_device_token)
            )
        if device:
            device.last_seen_at = utc_now()
            database.flush()
            return DeviceResult(device=device, raw_token=None)

        # 2. Fallback: buscar por perfil (browser + OS + device_type)
        browser, operating_system, device_type = self._describe_user_agent(user_agent)
        device = self.repository.get_for_user_by_profile(
            database, user.id, browser, operating_system, device_type
        )
        if device:
            device.last_seen_at = utc_now()
            database.flush()
            return DeviceResult(device=device, raw_token=None)

        # 3. No existe ningún dispositivo que coincida → crear uno nuevo
        raw_token = generate_device_token()
        device = self.repository.create(
            database,
            user_id=user.id,
            device_identifier=hash_device_token(raw_token),
            device_name="Navegador",
            browser=browser,
            operating_system=operating_system,
            device_type=device_type,
        )
        return DeviceResult(device=device, raw_token=raw_token)

    @staticmethod
    def _describe_user_agent(user_agent: str | None) -> tuple[str, str, str]:
        agent = (user_agent or "").lower()
        browser = (
            "Edge"
            if "edg/" in agent
            else "Chrome"
            if "chrome/" in agent
            else "Firefox"
            if "firefox/" in agent
            else "Safari"
            if "safari/" in agent
            else "Desconocido"
        )
        operating_system = (
            "Windows"
            if "windows" in agent
            else "Android"
            if "android" in agent
            else "iOS"
            if "iphone" in agent or "ipad" in agent
            else "macOS"
            if "mac os" in agent
            else "Linux"
            if "linux" in agent
            else "Desconocido"
        )
        device_type = "mobile" if "mobile" in agent else "desktop"
        return browser, operating_system, device_type