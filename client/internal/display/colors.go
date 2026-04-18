package display

import "fmt"

const (
	Reset  = "\033[0m"
	Bold   = "\033[1m"
	Red    = "\033[31m"
	Green  = "\033[32m"
	Yellow = "\033[33m"
	Cyan   = "\033[36m"
	Gray   = "\033[90m"
)

func ColorWidth() int {
	return len(Green) + len(Reset)
}

func BoolColor(v bool, trueStr, falseStr string) string {
	if v {
		return Green + trueStr + Reset
	}
	return Red + falseStr + Reset
}

func IntegrityText(level uint32) string {
	switch {
	case level >= 0x6000:
		return "SYSTEM"
	case level >= 0x3000:
		return "HIGH"
	case level >= 0x2000:
		return "MEDIUM"
	default:
		return "LOW"
	}
}

func IntegrityColor(level uint32) string {
	text := IntegrityText(level)
	switch {
	case level >= 0x6000:
		return Red + text + Reset
	case level >= 0x3000:
		return Yellow + text + Reset
	case level >= 0x2000:
		return Green + text + Reset
	default:
		return Gray + text + Reset
	}
}

func ShortOS(build uint32) string {
	switch {
	case build >= 26100:
		return "Win11 24H2"
	case build >= 22631:
		return "Win11 23H2"
	case build >= 22621:
		return "Win11 22H2"
	case build >= 22000:
		return "Win11 21H2"
	case build >= 20348:
		return "Server 2022"
	case build >= 19045:
		return "Win10 22H2"
	case build >= 19044:
		return "Win10 21H2"
	case build >= 19043:
		return "Win10 21H1"
	case build >= 19042:
		return "Win10 20H2"
	case build >= 19041:
		return "Win10 2004"
	case build >= 18363:
		return "Win10 1909"
	case build >= 18362:
		return "Win10 1903"
	case build >= 17763:
		return "Win10 1809 / Server 2019"
	case build >= 17134:
		return "Win10 1803"
	case build >= 16299:
		return "Win10 1709"
	case build >= 15063:
		return "Win10 1703"
	case build >= 14393:
		return "Win10 1607 / Server 2016"
	case build >= 10586:
		return "Win10 1511"
	case build >= 10240:
		return "Win10 1507"
	case build >= 9600:
		return "Win8.1 / Server 2012 R2"
	case build >= 9200:
		return "Win8 / Server 2012"
	case build >= 7601:
		return "Win7 SP1 / Server 2008 R2"
	case build >= 7600:
		return "Win7 / Server 2008 R2"
	default:
		return fmt.Sprintf("Build %d", build)
	}
}
