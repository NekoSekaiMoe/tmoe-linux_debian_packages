package system

import (
	"fmt"
	"os/exec"
	"runtime"
	"strings"
)

// ArchType represents system architecture
type ArchType string

const (
	ArchAMD64   ArchType = "amd64"
	ArchARM64   ArchType = "arm64"
	ArchARMHF   ArchType = "armhf"
	ArchARMEL   ArchType = "armel"
	ArchI386    ArchType = "i386"
	ArchMIPS64  ArchType = "mips64el"
	ArchMIPSEL  ArchType = "mipsel"
	ArchRISCV64 ArchType = "riscv64"
	ArchS390X   ArchType = "s390x"
	ArchPPC64EL ArchType = "ppc64el"
)

// DetectArch detects the system architecture
func DetectArch() (ArchType, error) {
	// Try dpkg first (Debian-based systems)
	if dpkgArch := getDpkgArch(); dpkgArch != "" {
		return dpkgArch, nil
	}

	// Fallback to uname -m
	return getUnameArch()
}

// getDpkgArch gets architecture from dpkg
func getDpkgArch() ArchType {
	cmd := exec.Command("dpkg", "--print-architecture")
	output, err := cmd.Output()
	if err != nil {
		return ""
	}

	arch := strings.TrimSpace(string(output))
	return normalizeArchFromDpkg(arch)
}

// getUnameArch gets architecture from uname -m
func getUnameArch() (ArchType, error) {
	// Use Go's runtime.GOARCH as fallback
	arch := runtime.GOARCH

	// Try to get more specific info from uname
	cmd := exec.Command("uname", "-m")
	output, err := cmd.Output()
	if err == nil {
		arch = strings.TrimSpace(string(output))
	}

	return normalizeArchFromUname(arch), nil
}

// normalizeArchFromDpkg normalizes dpkg architecture names
func normalizeArchFromDpkg(arch string) ArchType {
	switch arch {
	case "amd64":
		return ArchAMD64
	case "arm64":
		return ArchARM64
	case "armhf":
		return ArchARMHF
	case "armel":
		return ArchARMEL
	case "i386":
		return ArchI386
	case "mips64el":
		return ArchMIPS64
	case "mipsel":
		return ArchMIPSEL
	case "riscv64":
		return ArchRISCV64
	case "s390x":
		return ArchS390X
	case "ppc64el":
		return ArchPPC64EL
	default:
		return ArchType(arch)
	}
}

// normalizeArchFromUname normalizes uname architecture names
func normalizeArchFromUname(arch string) ArchType {
	switch {
	case arch == "x86_64" || arch == "amd64":
		return ArchAMD64
	case arch == "aarch64" || strings.HasPrefix(arch, "armv8") || arch == "arm64":
		return ArchARM64
	case strings.HasPrefix(arch, "armv7") || arch == "armv8l":
		return ArchARMHF
	case strings.HasPrefix(arch, "armv") && arch < "armv7":
		return ArchARMEL
	case arch == "i686" || arch == "i586" || arch == "i486" || arch == "i386" || arch == "x86":
		return ArchI386
	case arch == "mips64":
		return ArchMIPS64
	case strings.HasPrefix(arch, "mips"):
		return ArchMIPSEL
	case strings.HasPrefix(arch, "riscv64") || strings.HasPrefix(arch, "risc"):
		return ArchRISCV64
	case strings.HasPrefix(arch, "s390"):
		return ArchS390X
	case strings.HasPrefix(arch, "ppc64le") || strings.HasPrefix(arch, "ppc"):
		return ArchPPC64EL
	default:
		return ArchType(arch)
	}
}

// String returns the string representation of architecture
func (a ArchType) String() string {
	return string(a)
}

// ToDebianArch converts to Debian architecture name
func (a ArchType) ToDebianArch() string {
	switch a {
	case ArchAMD64:
		return "amd64"
	case ArchARM64:
		return "arm64"
	case ArchARMHF:
		return "armhf"
	case ArchARMEL:
		return "armel"
	case ArchI386:
		return "i386"
	case ArchMIPS64:
		return "mips64el"
	case ArchMIPSEL:
		return "mipsel"
	case ArchRISCV64:
		return "riscv64"
	case ArchS390X:
		return "s390x"
	case ArchPPC64EL:
		return "ppc64el"
	default:
		return string(a)
	}
}

// PrintArchInfo prints architecture information
func PrintArchInfo() error {
	arch, err := DetectArch()
	if err != nil {
		return err
	}

	fmt.Printf("Architecture: %s\n", arch)
	fmt.Printf("Debian arch: %s\n", arch.ToDebianArch())
	fmt.Printf("Go arch: %s\n", runtime.GOARCH)
	fmt.Printf("OS: %s\n", runtime.GOOS)

	return nil
}
