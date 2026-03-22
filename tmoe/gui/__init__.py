"""GUI and remote desktop management for TMOE.

Provides management for:
- VNC servers (TigerVNC, TightVNC)
- noVNC Web client
- XSDL (Android X server)
- Desktop environment installation
"""

from tmoe.gui.vnc import VncManager

__all__ = ["VncManager"]
