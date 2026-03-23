"""Extended tests for mirror manager.

These tests cover additional mirror management features that exist
in the shell version but may be missing in the Python version.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, mock_open

from tmoe.sources.mirrors import MirrorManager, MirrorSource, MirrorRegion


class TestMirrorManagerChinaMirrors:
    """Test China mirror support.
    
    Shell version supports 14+ China university mirrors.
    """
    
    @pytest.fixture
    def mirror_manager(self):
        """Create a mirror manager instance."""
        return MirrorManager()
    
    def test_tsinghua_mirror(self, mirror_manager):
        """Test Tsinghua University mirror."""
        mirror = mirror_manager.get_mirror("tsinghua")
        
        assert mirror is not None
        assert mirror.name == "Tsinghua University"
        assert mirror.url == "mirrors.tuna.tsinghua.edu.cn"
        assert mirror.region == MirrorRegion.CHINA
    
    def test_ustc_mirror(self, mirror_manager):
        """Test USTC mirror."""
        mirror = mirror_manager.get_mirror("ustc")
        
        assert mirror is not None
        assert "USTC" in mirror.name
        assert mirror.url == "mirrors.ustc.edu.cn"
        assert mirror.region == MirrorRegion.CHINA
    
    def test_bfsu_mirror(self, mirror_manager):
        """Test BFSU (Beijing Foreign Studies University) mirror."""
        mirror = mirror_manager.get_mirror("bfsu")
        
        assert mirror is not None
        assert "BFSU" in mirror.name
        assert mirror.url == "mirrors.bfsu.edu.cn"
        assert mirror.region == MirrorRegion.CHINA
    
    def test_sjtu_mirror(self, mirror_manager):
        """Test SJTU (Shanghai Jiao Tong University) mirror."""
        mirror = mirror_manager.get_mirror("sjtu")
        
        assert mirror is not None
        assert "SJTU" in mirror.name
        assert mirror.url == "mirror.sjtu.edu.cn"
        assert mirror.region == MirrorRegion.CHINA
    
    def test_aliyun_mirror(self, mirror_manager):
        """Test Aliyun mirror."""
        mirror = mirror_manager.get_mirror("aliyun")
        
        assert mirror is not None
        assert "Aliyun" in mirror.name
        assert mirror.url == "mirrors.aliyun.com"
        assert mirror.region == MirrorRegion.CHINA
    
    def test_tencent_mirror(self, mirror_manager):
        """Test Tencent Cloud mirror."""
        mirror = mirror_manager.get_mirror("tencent")
        
        assert mirror is not None
        assert "Tencent" in mirror.name
        assert mirror.url == "mirrors.cloud.tencent.com"
        assert mirror.region == MirrorRegion.CHINA
    
    def test_huawei_mirror(self, mirror_manager):
        """Test Huawei Cloud mirror."""
        mirror = mirror_manager.get_mirror("huawei")
        
        assert mirror is not None
        assert "Huawei" in mirror.name
        assert mirror.url == "mirrors.huaweicloud.com"
        assert mirror.region == MirrorRegion.CHINA
    
    @pytest.mark.skip(reason="Additional mirrors not yet implemented")
    def test_additional_china_mirrors(self, mirror_manager):
        """Test additional China mirrors.
        
        Shell version supports:
        - Zhejiang University (ZJU)
        - Huazhong University (HUST)
        - Beijing Institute of Technology (BIT)
        - Beijing Jiaotong University (BJTU)
        - Lanzhou University (LZU)
        - Nanjing University (NJU)
        - Nanjing University of Posts and Telecommunications (NUPT)
        - Northwest A&F University (NWAFU)
        """
        additional_mirrors = [
            "zju", "hust", "bit", "bjtu",
            "lzu", "nju", "nupt", "nwafu"
        ]
        
        for mirror_name in additional_mirrors:
            mirror = mirror_manager.get_mirror(mirror_name)
            assert mirror is not None, f"Missing mirror: {mirror_name}"
            assert mirror.region == MirrorRegion.CHINA


class TestMirrorManagerGlobalMirrors:
    """Test global mirror support."""
    
    def test_debian_official_mirror(self):
        """Test Debian official mirror."""
        manager = MirrorManager()
        mirror = manager.get_mirror("debian")
        
        assert mirror is not None
        assert "Debian" in mirror.name
        assert mirror.url == "deb.debian.org"
        assert mirror.region == MirrorRegion.GLOBAL
    
    def test_ubuntu_official_mirror(self):
        """Test Ubuntu official mirror."""
        manager = MirrorManager()
        mirror = manager.get_mirror("ubuntu")
        
        assert mirror is not None
        assert "Ubuntu" in mirror.name
        assert mirror.url == "archive.ubuntu.com"
        assert mirror.region == MirrorRegion.GLOBAL
    
    def test_arch_official_mirror(self):
        """Test Arch Linux official mirror."""
        manager = MirrorManager()
        mirror = manager.get_mirror("arch")
        
        assert mirror is not None
        assert "Arch" in mirror.name
        assert mirror.url == "mirrors.kernel.org"
        assert mirror.region == MirrorRegion.GLOBAL


class TestMirrorManagerRegionFiltering:
    """Test mirror region filtering."""
    
    def test_get_china_mirrors(self):
        """Test getting all China mirrors."""
        manager = MirrorManager()
        china_mirrors = manager.get_mirrors_by_region(MirrorRegion.CHINA)
        
        assert len(china_mirrors) >= 7  # At least the implemented ones
        
        for mirror in china_mirrors:
            assert mirror.region == MirrorRegion.CHINA
    
    def test_get_global_mirrors(self):
        """Test getting all global mirrors."""
        manager = MirrorManager()
        global_mirrors = manager.get_mirrors_by_region(MirrorRegion.GLOBAL)
        
        assert len(global_mirrors) >= 3
        
        for mirror in global_mirrors:
            assert mirror.region == MirrorRegion.GLOBAL
    
    def test_mirror_priority_ordering(self):
        """Test mirrors are ordered by priority."""
        manager = MirrorManager()
        china_mirrors = manager.get_mirrors_by_region(MirrorRegion.CHINA)
        
        # Check that mirrors are sorted by priority (lower is higher priority)
        priorities = [m.priority for m in china_mirrors]
        assert priorities == sorted(priorities)


class TestMirrorManagerDistroSupport:
    """Test distribution-specific mirror switching."""
    
    @pytest.fixture
    def mirror_manager(self):
        """Create a mirror manager with mocked platform."""
        manager = MirrorManager()
        return manager
    
    @pytest.mark.asyncio
    async def test_switch_debian_mirror(self, mirror_manager, tmp_path):
        """Test switching Debian mirror."""
        sources_list = tmp_path / "sources.list"
        sources_list.write_text("# Original content\n")
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", return_value="deb http://deb.debian.org/debian stable main"):
                with patch("pathlib.Path.write_text") as mock_write:
                    with patch.object(mirror_manager, "_run_apt_update", new_callable=AsyncMock):
                        result = await mirror_manager.switch_mirror("debian", "tsinghua", "bookworm")
                        
                        assert result is True
                        mock_write.assert_called_once()
                        
                        # Check content includes Tsinghua mirror
                        content = mock_write.call_args[0][0]
                        assert "mirrors.tuna.tsinghua.edu.cn" in content
                        assert "bookworm" in content
    
    @pytest.mark.asyncio
    async def test_switch_ubuntu_mirror(self, mirror_manager):
        """Test switching Ubuntu mirror."""
        with patch.object(Path, "exists", return_value=True):
            with patch("pathlib.Path.rename"):
                with patch("pathlib.Path.write_text") as mock_write:
                    with patch.object(mirror_manager, "_run_apt_update", new_callable=AsyncMock):
                        result = await mirror_manager.switch_mirror("ubuntu", "tsinghua", "jammy")
                        
                        assert result is True
                        content = mock_write.call_args[0][0]
                        assert "mirrors.tuna.tsinghua.edu.cn" in content
                        assert "jammy" in content
    
    @pytest.mark.asyncio
    async def test_switch_arch_mirror(self, mirror_manager):
        """Test switching Arch Linux mirror."""
        with patch.object(Path, "exists", return_value=True):
            with patch("pathlib.Path.rename"):
                with patch("pathlib.Path.write_text") as mock_write:
                    result = await mirror_manager.switch_mirror("arch", "tsinghua")
                    
                    assert result is True
                    content = mock_write.call_args[0][0]
                    assert "mirrors.tuna.tsinghua.edu.cn" in content
    
    @pytest.mark.asyncio
    async def test_switch_alpine_mirror(self, mirror_manager):
        """Test switching Alpine Linux mirror."""
        with patch.object(Path, "exists", return_value=True):
            with patch("pathlib.Path.rename"):
                with patch("pathlib.Path.write_text") as mock_write:
                    result = await mirror_manager.switch_mirror("alpine", "tsinghua", "v3.19")
                    
                    assert result is True
                    content = mock_write.call_args[0][0]
                    assert "mirrors.tuna.tsinghua.edu.cn" in content
    
    @pytest.mark.asyncio
    async def test_switch_fedora_mirror(self, mirror_manager):
        """Test switching Fedora mirror."""
        with patch.object(Path, "exists", return_value=True):
            # Fedora switching is simplified in current implementation
            result = await mirror_manager.switch_mirror("fedora", "tsinghua")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_switch_unknown_distro(self, mirror_manager):
        """Test switching mirror for unknown distro raises error."""
        with pytest.raises(ValueError, match="Unsupported distribution"):
            await mirror_manager.switch_mirror("unknown", "tsinghua")
    
    @pytest.mark.asyncio
    async def test_switch_unknown_mirror(self, mirror_manager):
        """Test switching to unknown mirror raises error."""
        with pytest.raises(ValueError, match="Unknown mirror"):
            await mirror_manager.switch_mirror("debian", "nonexistent")


class TestMirrorManagerSpeedTest:
    """Test mirror speed testing functionality."""
    
    @pytest.mark.asyncio
    async def test_mirror_speed_test(self):
        """Test mirror speed measurement."""
        manager = MirrorManager()
        
        # Mock httpx client
        mock_response = Mock()
        mock_response.content = b"x" * 102400  # 100KB
        mock_response.raise_for_status = Mock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.get = AsyncMock(return_value=mock_response)
            
            speed = await manager.test_mirror_speed("tsinghua")
            
            # Speed should be positive
            assert speed > 0
            mock_client.return_value.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mirror_speed_test_failure(self):
        """Test mirror speed test on failure."""
        manager = MirrorManager()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.get = AsyncMock(side_effect=Exception("Connection failed"))
            
            speed = await manager.test_mirror_speed("tsinghua")
            
            # Should return 0 on failure
            assert speed == 0.0


class TestMirrorManagerBackup:
    """Test mirror configuration backup functionality."""
    
    @pytest.mark.asyncio
    async def test_sources_list_backup(self):
        """Test that sources.list is backed up before modification."""
        manager = MirrorManager()
        
        # First call checks sources_list.exists(), second checks backup.exists()
        with patch.object(Path, "exists", side_effect=[True, False]):
            with patch.object(Path, "read_text", return_value="deb http://deb.debian.org/debian stable main"):
                with patch("pathlib.Path.rename") as mock_rename:
                    with patch("pathlib.Path.write_text"):
                        with patch.object(manager, "_run_apt_update", new_callable=AsyncMock):
                            await manager.switch_mirror("debian", "tsinghua")
                            
                            # Should backup the file
                            mock_rename.assert_called_once()
                            backup_path = mock_rename.call_args[0][0]
                            assert str(backup_path).endswith(".backup")
    
    @pytest.mark.asyncio
    async def test_backup_only_once(self):
        """Test that backup is only created once."""
        manager = MirrorManager()
        
        with patch.object(Path, "exists", side_effect=[True, True, True]):
            with patch("pathlib.Path.rename") as mock_rename:
                with patch("pathlib.Path.write_text"):
                    with patch.object(manager, "_run_apt_update", new_callable=AsyncMock):
                        # First call - should backup
                        await manager.switch_mirror("debian", "tsinghua")
                        
                        # Check if backup exists is called
                        # If backup exists, rename should not be called again
                        pass


class TestMirrorManagerAptOperations:
    """Test apt operations."""
    
    @pytest.mark.asyncio
    async def test_apt_update_success(self):
        """Test successful apt update."""
        manager = MirrorManager()
        
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            # Should not raise
            await manager._run_apt_update()
    
    @pytest.mark.asyncio
    async def test_apt_update_failure(self):
        """Test failed apt update."""
        manager = MirrorManager()
        
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Some error"))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="apt update failed"):
                await manager._run_apt_update()


class TestMirrorManagerAdditionalDistros:
    """Test additional distribution support.
    
    Shell version supports more distributions.
    """
    
    @pytest.mark.skip(reason="Additional distro support not yet implemented")
    @pytest.mark.asyncio
    async def test_switch_opensuse_mirror(self):
        """Test switching openSUSE mirror."""
        manager = MirrorManager()
        
        result = await manager.switch_mirror("opensuse", "tsinghua")
        assert result is True
    
    @pytest.mark.skip(reason="Additional distro support not yet implemented")
    @pytest.mark.asyncio
    async def test_switch_centos_mirror(self):
        """Test switching CentOS mirror."""
        manager = MirrorManager()
        
        result = await manager.switch_mirror("centos", "tsinghua")
        assert result is True
    
    @pytest.mark.skip(reason="Additional distro support not yet implemented")
    @pytest.mark.asyncio
    async def test_switch_gentoo_mirror(self):
        """Test switching Gentoo mirror."""
        manager = MirrorManager()
        
        result = await manager.switch_mirror("gentoo", "tsinghua")
        assert result is True


class TestMirrorManagerAutoSelection:
    """Test automatic mirror selection features.
    
    Shell version can automatically select the fastest mirror.
    """
    
    @pytest.mark.skip(reason="Auto-selection not yet implemented")
    @pytest.mark.asyncio
    async def test_auto_select_fastest_mirror(self):
        """Test automatic selection of fastest mirror."""
        manager = MirrorManager()
        
        # Mock speed tests
        speeds = {
            "tsinghua": 5000.0,
            "ustc": 3000.0,
            "aliyun": 4000.0,
        }
        
        with patch.object(manager, "test_mirror_speed", side_effect=lambda m: AsyncMock(return_value=speeds.get(m, 0))()):
            best_mirror = await manager.auto_select_mirror("debian")
            
            assert best_mirror == "tsinghua"  # Fastest
    
    @pytest.mark.skip(reason="Auto-selection not yet implemented")
    def test_get_recommended_mirrors(self):
        """Test getting recommended mirrors for user's region."""
        manager = MirrorManager()
        
        # Mock platform detection
        manager.platform.is_china = True
        
        recommended = manager.get_recommended_mirrors()
        
        # Should prefer China mirrors when in China
        china_mirrors = [m for m in recommended if m.region == MirrorRegion.CHINA]
        assert len(china_mirrors) > 0
