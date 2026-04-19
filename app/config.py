import os


class Settings:
    API_KEY_NAME: str = "X-API-KEY"
    API_KEY: str = os.getenv("OCR_API_KEY", "my_default_secret")
    PDF_DPI: int = int(os.getenv("PDF_DPI", "200"))
    PDF_MAX_PAGES: int = int(os.getenv("PDF_MAX_PAGES", "50"))
    URL_DOWNLOAD_TIMEOUT: int = int(os.getenv("URL_DOWNLOAD_TIMEOUT", "15"))
    URL_MAX_BYTES: int = int(os.getenv("URL_MAX_BYTES", str(50 * 1024 * 1024)))
    URL_MAX_REDIRECTS: int = int(os.getenv("URL_MAX_REDIRECTS", "3"))
    ALLOW_PRIVATE_URLS: bool = os.getenv("ALLOW_PRIVATE_URLS", "false").lower() in ("1", "true", "yes")


settings = Settings()
