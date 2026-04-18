package banner

import (
	"fmt"
)

const logo = `
┏┓┓     ┏┓
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛  `

func Print(c2Addr, opAddr, apiKey string) {
	fmt.Println(logo)
	fmt.Printf("  %-14s %s\n", "HTTPS Listener", c2Addr)
	fmt.Printf("  %-14s %s\n", "Operator API", opAddr)
	fmt.Printf("  %-14s %s\n", "API Key", apiKey)
	fmt.Println()
}
