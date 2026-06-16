package mirror

import (
	"testing"
	"time"
)

func TestNewMirrorManager(t *testing.T) {
	distros := []DistroType{
		DistroDebian,
		DistroUbuntu,
		DistroArch,
		DistroAlpine,
		DistroKali,
	}

	for _, distro := range distros {
		t.Run(string(distro), func(t *testing.T) {
			mgr := NewMirrorManager(distro)
			if mgr == nil {
				t.Fatal("NewMirrorManager returned nil")
			}

			mirrors := mgr.ListMirrors()
			if len(mirrors) == 0 {
				t.Errorf("No mirrors found for %s", distro)
			}

			t.Logf("%s has %d mirrors", distro, len(mirrors))
		})
	}
}

func TestMirrorList(t *testing.T) {
	mgr := NewMirrorManager(DistroDebian)
	mirrors := mgr.ListMirrors()

	if len(mirrors) < 3 {
		t.Errorf("Expected at least 3 mirrors, got %d", len(mirrors))
	}

	// Check mirror structure
	for _, m := range mirrors {
		if m.Name == "" {
			t.Error("Mirror has empty name")
		}
		if m.URL == "" {
			t.Error("Mirror has empty URL")
		}
		if m.Country == "" {
			t.Error("Mirror has empty country")
		}
	}
}

func TestGenerateSourcesList(t *testing.T) {
	mgr := NewMirrorManager(DistroDebian)
	mirrors := mgr.ListMirrors()

	if len(mirrors) == 0 {
		t.Fatal("No mirrors available")
	}

	mirror := mirrors[0]
	release := "bookworm"
	components := []string{"main", "contrib", "non-free"}

	sourcesList := mgr.GenerateSourcesList(mirror, release, components)

	if sourcesList == "" {
		t.Error("GenerateSourcesList returned empty string")
	}

	// Check that sources.list contains expected content
	if !contains(sourcesList, "deb") {
		t.Error("sources.list does not contain 'deb'")
	}
	if !contains(sourcesList, release) {
		t.Errorf("sources.list does not contain release '%s'", release)
	}
	if !contains(sourcesList, mirror.URL) {
		t.Errorf("sources.list does not contain mirror URL '%s'", mirror.URL)
	}

	t.Logf("Generated sources.list:\n%s", sourcesList)
}

func TestGetFastest(t *testing.T) {
	mgr := NewMirrorManager(DistroDebian)

	// Manually set speeds
	mirrors := mgr.ListMirrors()
	for i := range mirrors {
		mirrors[i].Speed = time.Duration((i + 1) * 100) * time.Millisecond
	}
	mgr.mirrors = mirrors

	fastest := mgr.GetFastest()
	if fastest == nil {
		t.Fatal("GetFastest returned nil")
	}

	if fastest.Speed != 100*time.Millisecond {
		t.Errorf("Expected fastest speed 100ms, got %v", fastest.Speed)
	}
}

func TestGetSortedBySpeed(t *testing.T) {
	mgr := NewMirrorManager(DistroDebian)

	// Set some mirrors with speeds, some without
	mirrors := mgr.ListMirrors()
	if len(mirrors) < 3 {
		t.Skip("Not enough mirrors for test")
	}

	mirrors[0].Speed = 200 * time.Millisecond
	mirrors[1].Speed = 0 // Not tested
	mirrors[2].Speed = 100 * time.Millisecond
	mgr.mirrors = mirrors

	sorted := mgr.GetSortedBySpeed()

	// Check that tested mirrors come first
	if sorted[0].Speed == 0 {
		t.Error("Untested mirror appears first")
	}

	// Check that sorted by speed
	if sorted[0].Speed > sorted[1].Speed && sorted[1].Speed != 0 {
		t.Error("Mirrors not sorted by speed")
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && (s[:len(substr)] == substr || s[len(s)-len(substr):] == substr || containsMiddle(s, substr)))
}

func containsMiddle(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
