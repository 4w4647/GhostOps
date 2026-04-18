package display

import (
	"fmt"
	"strings"
	"time"
)

func MaxLen(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func Since(t time.Time) string {
	d := time.Since(t).Round(time.Second)
	if d < time.Minute {
		return fmt.Sprintf("%ds ago", int(d.Seconds()))
	} else if d < time.Hour {
		return fmt.Sprintf("%dm ago", int(d.Minutes()))
	}
	return fmt.Sprintf("%dh ago", int(d.Hours()))
}

func DynTable(headers []string, rows [][]string) string {
	widths := make([]int, len(headers))
	for i, h := range headers {
		widths[i] = len(h)
	}
	for _, row := range rows {
		for i, cell := range row {
			if len(cell) > widths[i] {
				widths[i] = len(cell)
			}
		}
	}

	sep := "  "
	total := 0
	for _, w := range widths {
		total += w
	}
	total += len(sep) * (len(widths) - 1)

	var sb strings.Builder
	sb.WriteString("\n" + Bold)
	for i, h := range headers {
		sb.WriteString(fmt.Sprintf("%-*s", widths[i], h))
		if i < len(headers)-1 {
			sb.WriteString(sep)
		}
	}
	sb.WriteString(Reset + "\n")
	sb.WriteString(strings.Repeat("─", total) + "\n")

	for _, row := range rows {
		for i, cell := range row {
			sb.WriteString(fmt.Sprintf("%-*s", widths[i], cell))
			if i < len(row)-1 {
				sb.WriteString(sep)
			}
		}
		sb.WriteString("\n")
	}
	return sb.String()
}
