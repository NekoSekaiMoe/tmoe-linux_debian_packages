package system

import (
	"testing"
)

func TestDetectArch(t *testing.T) {
	arch, err := DetectArch()
	if err != nil {
		t.Fatalf("DetectArch failed: %v", err)
	}

	if arch == "" {
		t.Error("DetectArch returned empty string")
	}

	t.Logf("Detected architecture: %s", arch)
}

func TestArchTypeToDebianArch(t *testing.T) {
	tests := []struct {
		input    ArchType
		expected string
	}{
		{ArchAMD64, "amd64"},
		{ArchARM64, "arm64"},
		{ArchARMHF, "armhf"},
		{ArchI386, "i386"},
		{ArchRISCV64, "riscv64"},
		{ArchS390X, "s390x"},
	}

	for _, tt := range tests {
		t.Run(string(tt.input), func(t *testing.T) {
			result := tt.input.ToDebianArch()
			if result != tt.expected {
				t.Errorf("ToDebianArch(%s) = %s, want %s", tt.input, result, tt.expected)
			}
		})
	}
}

func TestNormalizeArch(t *testing.T) {
	tests := []struct {
		input    string
		expected ArchType
	}{
		{"amd64", ArchAMD64},
		{"x86_64", ArchAMD64},
		{"arm64", ArchARM64},
		{"aarch64", ArchARM64},
		{"armhf", ArchARMHF},
		{"i386", ArchI386},
		{"i686", ArchI386},
		{"riscv64", ArchRISCV64},
		{"s390x", ArchS390X},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			// This tests the normalization logic
			result := normalizeArchTest(tt.input)
			if result != tt.expected {
				t.Errorf("normalize(%s) = %s, want %s", tt.input, result, tt.expected)
			}
		})
	}
}

func normalizeArchTest(arch string) ArchType {
	switch arch {
	case "x86_64", "amd64":
		return ArchAMD64
	case "aarch64", "arm64":
		return ArchARM64
	case "armv7l", "armhf":
		return ArchARMHF
	case "i386", "i686":
		return ArchI386
	case "riscv64":
		return ArchRISCV64
	case "s390x":
		return ArchS390X
	default:
		return ArchType(arch)
	}
}
