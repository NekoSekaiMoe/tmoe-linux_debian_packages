package mirror

import (
	"context"
	"fmt"
	"net/http"
	"sort"
	"strings"
	"time"
)

// Mirror represents a package mirror
type Mirror struct {
	Name        string
	Country     string
	URL         string
	Description string
	Protocols   []string // http, https
	Speed       time.Duration
}

// DistroType represents different Linux distributions
type DistroType string

const (
	DistroDebian DistroType = "debian"
	DistroUbuntu DistroType = "ubuntu"
	DistroArch   DistroType = "arch"
	DistroAlpine DistroType = "alpine"
	DistroKali   DistroType = "kali"
)

// MirrorManager manages package mirrors
type MirrorManager struct {
	distro  DistroType
	mirrors []Mirror
}

// NewMirrorManager creates a new mirror manager
func NewMirrorManager(distro DistroType) *MirrorManager {
	return &MirrorManager{
		distro:  distro,
		mirrors: getDefaultMirrors(distro),
	}
}

// getDefaultMirrors returns default mirrors for a distro
func getDefaultMirrors(distro DistroType) []Mirror {
	switch distro {
	case DistroDebian:
		return []Mirror{
			{Name: "Official", Country: "Global", URL: "http://deb.debian.org/debian", Description: "Debian official repository"},
			{Name: "Tsinghua", Country: "China", URL: "https://mirrors.tuna.tsinghua.edu.cn/debian", Description: "清华大学镜像站"},
			{Name: "USTC", Country: "China", URL: "https://mirrors.ustc.edu.cn/debian", Description: "中科大镜像站"},
			{Name: "Aliyun", Country: "China", URL: "https://mirrors.aliyun.com/debian", Description: "阿里云镜像站"},
			{Name: "Tencent", Country: "China", URL: "https://mirrors.cloud.tencent.com/debian", Description: "腾讯云镜像站"},
			{Name: "Huawei", Country: "China", URL: "https://mirrors.huaweicloud.com/debian", Description: "华为云镜像站"},
		}
	case DistroUbuntu:
		return []Mirror{
			{Name: "Official", Country: "Global", URL: "http://archive.ubuntu.com/ubuntu", Description: "Ubuntu official repository"},
			{Name: "Tsinghua", Country: "China", URL: "https://mirrors.tuna.tsinghua.edu.cn/ubuntu", Description: "清华大学镜像站"},
			{Name: "USTC", Country: "China", URL: "https://mirrors.ustc.edu.cn/ubuntu", Description: "中科大镜像站"},
			{Name: "Aliyun", Country: "China", URL: "https://mirrors.aliyun.com/ubuntu", Description: "阿里云镜像站"},
			{Name: "Tencent", Country: "China", URL: "https://mirrors.cloud.tencent.com/ubuntu", Description: "腾讯云镜像站"},
		}
	case DistroArch:
		return []Mirror{
			{Name: "Official", Country: "Global", URL: "https://archlinux.org/mirrorlist", Description: "Arch official mirrors"},
			{Name: "Tsinghua", Country: "China", URL: "https://mirrors.tuna.tsinghua.edu.cn/archlinux", Description: "清华大学镜像站"},
			{Name: "USTC", Country: "China", URL: "https://mirrors.ustc.edu.cn/archlinux", Description: "中科大镜像站"},
		}
	case DistroAlpine:
		return []Mirror{
			{Name: "Official", Country: "Global", URL: "http://dl-cdn.alpinelinux.org/alpine", Description: "Alpine official CDN"},
			{Name: "Tsinghua", Country: "China", URL: "https://mirrors.tuna.tsinghua.edu.cn/alpine", Description: "清华大学镜像站"},
			{Name: "USTC", Country: "China", URL: "https://mirrors.ustc.edu.cn/alpine", Description: "中科大镜像站"},
		}
	case DistroKali:
		return []Mirror{
			{Name: "Official", Country: "Global", URL: "http://http.kali.org/kali", Description: "Kali official repository"},
			{Name: "Tsinghua", Country: "China", URL: "https://mirrors.tuna.tsinghua.edu.cn/kali", Description: "清华大学镜像站"},
			{Name: "USTC", Country: "China", URL: "https://mirrors.ustc.edu.cn/kali", Description: "中科大镜像站"},
		}
	default:
		return []Mirror{}
	}
}

// ListMirrors returns all available mirrors
func (m *MirrorManager) ListMirrors() []Mirror {
	return m.mirrors
}

// TestSpeed tests the speed of a mirror
func (m *MirrorManager) TestSpeed(mirror *Mirror, timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	start := time.Now()

	req, err := http.NewRequestWithContext(ctx, "HEAD", mirror.URL, nil)
	if err != nil {
		return err
	}

	client := &http.Client{
		Timeout: timeout,
	}

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 400 {
		return fmt.Errorf("HTTP %d", resp.StatusCode)
	}

	mirror.Speed = time.Since(start)
	return nil
}

// TestAllSpeeds tests speeds of all mirrors
func (m *MirrorManager) TestAllSpeeds(timeout time.Duration) {
	for i := range m.mirrors {
		_ = m.TestSpeed(&m.mirrors[i], timeout)
	}
}

// GetFastest returns the fastest mirror
func (m *MirrorManager) GetFastest() *Mirror {
	var fastest *Mirror
	for i := range m.mirrors {
		if m.mirrors[i].Speed == 0 {
			continue // Not tested
		}
		if fastest == nil || m.mirrors[i].Speed < fastest.Speed {
			fastest = &m.mirrors[i]
		}
	}
	return fastest
}

// GetSortedBySpeed returns mirrors sorted by speed
func (m *MirrorManager) GetSortedBySpeed() []Mirror {
	sorted := make([]Mirror, len(m.mirrors))
	copy(sorted, m.mirrors)

	sort.Slice(sorted, func(i, j int) bool {
		// Untested mirrors go to the end
		if sorted[i].Speed == 0 && sorted[j].Speed == 0 {
			return false
		}
		if sorted[i].Speed == 0 {
			return false
		}
		if sorted[j].Speed == 0 {
			return true
		}
		return sorted[i].Speed < sorted[j].Speed
	})

	return sorted
}

// GenerateSourcesList generates sources.list for Debian/Ubuntu
func (m *MirrorManager) GenerateSourcesList(mirror Mirror, release string, components []string) string {
	var sb strings.Builder

	// Main repository
	sb.WriteString(fmt.Sprintf("deb %s %s", mirror.URL, release))
	for _, comp := range components {
		sb.WriteString(fmt.Sprintf(" %s", comp))
	}
	sb.WriteString("\n")

	// Source repository
	sb.WriteString(fmt.Sprintf("deb-src %s %s", mirror.URL, release))
	for _, comp := range components {
		sb.WriteString(fmt.Sprintf(" %s", comp))
	}
	sb.WriteString("\n")

	// Security updates (for Debian/Ubuntu)
	if m.distro == DistroDebian || m.distro == DistroUbuntu {
		securityURL := strings.Replace(mirror.URL, "debian", "debian-security", 1)
		sb.WriteString(fmt.Sprintf("\ndeb %s %s-security", securityURL, release))
		for _, comp := range components {
			sb.WriteString(fmt.Sprintf(" %s", comp))
		}
		sb.WriteString("\n")
	}

	// Updates
	if m.distro == DistroDebian {
		sb.WriteString(fmt.Sprintf("\ndeb %s %s-updates", mirror.URL, release))
		for _, comp := range components {
			sb.WriteString(fmt.Sprintf(" %s", comp))
		}
		sb.WriteString("\n")
	}

	return sb.String()
}

// DetectDistro detects the current distribution
func DetectDistro() (DistroType, string, error) {
	// Try to read /etc/os-release
	// This is a simplified version - full implementation would parse the file

	// For now, return unknown
	return "", "", fmt.Errorf("distribution detection not implemented")
}
