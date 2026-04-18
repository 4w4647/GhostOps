package banner

import (
	"fmt"
)

const logo = `
┏┓┓     ┏┓   
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛  `

func Print(c2Addr, opAddr string) {
	fmt.Println(logo)
	fmt.Printf("%s - %s\n", "HTTPListener", c2Addr)
	fmt.Printf("%s - %s\n", "Operator API", opAddr)
	fmt.Println()
}
