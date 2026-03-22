"""Internationalization (i18n) support for TMOE.

Multi-language support using gettext-style translation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tmoe.core.config import TmoeConfig


@dataclass
class TranslationStrings:
    """Translation strings for a language."""
    
    # Common
    ok: str = "OK"
    cancel: str = "Cancel"
    back: str = "Back"
    save: str = "Save"
    delete: str = "Delete"
    create: str = "Create"
    start: str = "Start"
    stop: str = "Stop"
    install: str = "Install"
    
    # Menu titles
    main_menu: str = "TMOE Main Menu"
    container_menu: str = "Container Management"
    settings_menu: str = "Settings"
    
    # Container
    proot_container: str = "Proot Container"
    chroot_container: str = "Chroot Container"
    docker_container: str = "Docker Container"
    create_container: str = "Create Container"
    container_name: str = "Container Name"
    container_list: str = "Container List"
    no_containers: str = "No containers found"
    
    # Desktop
    desktop_environment: str = "Desktop Environment"
    install_xfce: str = "Install XFCE"
    install_lxde: str = "Install LXDE"
    install_mate: str = "Install MATE"
    
    # Messages
    success: str = "Success"
    error: str = "Error"
    warning: str = "Warning"
    please_wait: str = "Please wait..."
    operation_complete: str = "Operation complete"


class I18n:
    """Internationalization manager.
    
    Provides multi-language support for TMOE.
    
    Example:
        >>> from tmoe.core.i18n import I18n, get_i18n
        >>> i18n = get_i18n()
        >>> print(i18n.t("main_menu"))
        TMOE 主菜单
    """
    
    # Supported languages
    LANGUAGES = {
        "en": "English",
        "zh_CN": "简体中文",
        "zh_TW": "繁體中文",
        "ja": "日本語",
    }
    
    # Translation dictionaries
    TRANSLATIONS: dict[str, dict[str, str]] = {
        "zh_CN": {
            "ok": "确定",
            "cancel": "取消",
            "back": "返回",
            "save": "保存",
            "delete": "删除",
            "create": "创建",
            "start": "启动",
            "stop": "停止",
            "install": "安装",
            "main_menu": "TMOE 主菜单",
            "container_menu": "容器管理",
            "settings_menu": "设置",
            "proot_container": "Proot 容器",
            "chroot_container": "Chroot 容器",
            "docker_container": "Docker 容器",
            "create_container": "创建容器",
            "container_name": "容器名称",
            "container_list": "容器列表",
            "no_containers": "未找到容器",
            "desktop_environment": "桌面环境",
            "install_xfce": "安装 XFCE",
            "install_lxde": "安装 LXDE",
            "install_mate": "安装 MATE",
            "success": "成功",
            "error": "错误",
            "warning": "警告",
            "please_wait": "请稍候...",
            "operation_complete": "操作完成",
        },
        "zh_TW": {
            "ok": "確定",
            "cancel": "取消",
            "back": "返回",
            "save": "儲存",
            "delete": "刪除",
            "create": "創建",
            "start": "啟動",
            "stop": "停止",
            "install": "安裝",
            "main_menu": "TMOE 主選單",
            "container_menu": "容器管理",
            "settings_menu": "設定",
            "proot_container": "Proot 容器",
            "chroot_container": "Chroot 容器",
            "docker_container": "Docker 容器",
            "create_container": "創建容器",
            "container_name": "容器名稱",
            "container_list": "容器列表",
            "no_containers": "未找到容器",
            "desktop_environment": "桌面環境",
            "install_xfce": "安裝 XFCE",
            "install_lxde": "安裝 LXDE",
            "install_mate": "安裝 MATE",
            "success": "成功",
            "error": "錯誤",
            "warning": "警告",
            "please_wait": "請稍候...",
            "operation_complete": "操作完成",
        },
        "ja": {
            "ok": "OK",
            "cancel": "キャンセル",
            "back": "戻る",
            "save": "保存",
            "delete": "削除",
            "create": "作成",
            "start": "開始",
            "stop": "停止",
            "install": "インストール",
            "main_menu": "TMOE メインメニュー",
            "container_menu": "コンテナ管理",
            "settings_menu": "設定",
            "proot_container": "Proot コンテナ",
            "chroot_container": "Chroot コンテナ",
            "docker_container": "Docker コンテナ",
            "create_container": "コンテナ作成",
            "container_name": "コンテナ名",
            "container_list": "コンテナ一覧",
            "no_containers": "コンテナが見つかりません",
            "desktop_environment": "デスクトップ環境",
            "install_xfce": "XFCE をインストール",
            "install_lxde": "LXDE をインストール",
            "install_mate": "MATE をインストール",
            "success": "成功",
            "error": "エラー",
            "warning": "警告",
            "please_wait": "お待ちください...",
            "operation_complete": "操作完了",
        },
    }
    
    def __init__(self, language: str = "en") -> None:
        self.language = language
        self._translations = self.TRANSLATIONS.get(language, {})
    
    def t(self, key: str, default: str | None = None) -> str:
        """Translate a key.
        
        Args:
            key: Translation key
            default: Default value if key not found
            
        Returns:
            Translated string
        """
        return self._translations.get(key, default or key)
    
    def set_language(self, language: str) -> None:
        """Change language.
        
        Args:
            language: Language code (e.g., 'zh_CN', 'en')
        """
        self.language = language
        self._translations = self.TRANSLATIONS.get(language, {})
    
    def get_available_languages(self) -> dict[str, str]:
        """Get available languages.
        
        Returns:
            Dictionary of language codes to names
        """
        return self.LANGUAGES.copy()


@lru_cache(maxsize=1)
def get_i18n() -> I18n:
    """Get singleton I18n instance.
    
    Returns:
        I18n instance with current language from config
    """
    try:
        from tmoe.core.config import get_config
        config = get_config()
        return I18n(config.language)
    except Exception:
        return I18n("en")


def _(key: str, default: str | None = None) -> str:
    """Shorthand for translation.
    
    Args:
        key: Translation key
        default: Default value
        
    Returns:
        Translated string
        
    Example:
        >>> from tmoe.core.i18n import _
        >>> print(_("main_menu"))
        TMOE 主菜单
    """
    return get_i18n().t(key, default)
